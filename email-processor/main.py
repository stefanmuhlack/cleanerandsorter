import os
import asyncio
import yaml
import imaplib
import email
import tempfile
import shutil
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import json
from loguru import logger
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib

# Configure logging
logger.add("/app/logs/email-processor.log", rotation="1 day", retention="7 days")

app = FastAPI(title="Email Processor", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
PAPERLESS_URL = os.getenv("PAPERLESS_URL", "http://paperless:8000")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://cas_user:cas_password@rabbitmq:5672/")
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")

class EmailAccount(BaseModel):
    name: str
    host: str
    port: int
    username: str
    password: str
    use_ssl: bool = True
    folders: List[str] = ["INBOX"]

class EmailMessage(BaseModel):
    id: str
    subject: str
    sender: str
    recipient: str
    body: str
    attachments: List[Dict[str, Any]] = []
    received_at: str

class ProcessingResult(BaseModel):
    success: bool
    message: str
    processed_attachments: int = 0
    errors: List[str] = []

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Paperless connection
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PAPERLESS_URL}/health/")
            if response.status_code != 200:
                raise HTTPException(status_code=503, detail="Paperless service unavailable")
        
        return {"status": "healthy", "service": "email-processor"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/accounts")
async def list_email_accounts():
    """List configured email accounts"""
    try:
        config_path = "/app/config/email-config.yaml"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config.get("accounts", [])
        else:
            return {"accounts": []}
    except Exception as e:
        logger.error(f"Failed to load email config: {e}")
        raise HTTPException(status_code=500, detail="Failed to load email configuration")

@app.post("/process/{account_name}")
async def process_email_account(account_name: str, background_tasks: BackgroundTasks):
    """Process emails from a specific account"""
    try:
        # Load email configuration
        config = load_email_config()
        account_config = None
        
        for account in config.get("accounts", []):
            if account["name"] == account_name:
                account_config = account
                break
        
        if not account_config:
            raise HTTPException(status_code=404, detail=f"Email account {account_name} not found")
        
        # Start background processing
        background_tasks.add_task(process_emails, account_config)
        
        return {"message": f"Started processing emails for account {account_name}", "status": "processing"}
    except Exception as e:
        logger.error(f"Failed to start email processing: {e}")
        raise HTTPException(status_code=500, detail="Failed to start email processing")

@app.get("/messages/{account_name}")
async def get_email_messages(account_name: str, limit: int = 50):
    """Get recent email messages from an account"""
    try:
        config = load_email_config()
        account_config = None
        
        for account in config.get("accounts", []):
            if account["name"] == account_name:
                account_config = account
                break
        
        if not account_config:
            raise HTTPException(status_code=404, detail=f"Email account {account_name} not found")
        
        messages = await fetch_email_messages(account_config, limit)
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Failed to fetch email messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch email messages")

async def process_emails(account_config: Dict[str, Any]):
    """Process emails from an account"""
    try:
        logger.info(f"Starting email processing for account {account_config['name']}")
        
        # Connect to IMAP server
        if account_config.get("use_ssl", True):
            imap_server = imaplib.IMAP4_SSL(account_config["host"], account_config["port"])
        else:
            imap_server = imaplib.IMAP4(account_config["host"], account_config["port"])
        
        # Login
        imap_server.login(account_config["username"], account_config["password"])
        
        # Process each folder
        for folder in account_config.get("folders", ["INBOX"]):
            await process_email_folder(imap_server, folder, account_config)
        
        imap_server.logout()
        logger.info(f"Completed email processing for account {account_config['name']}")
        
    except Exception as e:
        logger.error(f"Email processing failed for account {account_config['name']}: {e}")

async def process_email_folder(imap_server, folder: str, account_config: Dict[str, Any]):
    """Process emails in a specific folder"""
    try:
        # Select folder
        imap_server.select(folder)
        
        # Search for unread messages
        _, message_numbers = imap_server.search(None, 'UNSEEN')
        
        if not message_numbers[0]:
            logger.info(f"No unread messages in folder {folder}")
            return
        
        message_list = message_numbers[0].split()
        
        for num in message_list:
            await process_single_email(imap_server, num, account_config)
            
    except Exception as e:
        logger.error(f"Failed to process folder {folder}: {e}")

async def process_single_email(imap_server, message_num: bytes, account_config: Dict[str, Any]):
    """Process a single email message"""
    try:
        # Fetch message
        _, msg_data = imap_server.fetch(message_num, '(RFC822)')
        email_body = msg_data[0][1]
        email_message = email.message_from_bytes(email_body)
        
        # Extract message information
        subject = email_message.get('Subject', '')
        sender = email_message.get('From', '')
        recipient = email_message.get('To', '')
        date = email_message.get('Date', '')
        
        # Extract body
        body = extract_email_body(email_message)
        
        # Process attachments
        attachments = await process_email_attachments(email_message, account_config)
        
        # Send to Paperless if attachments found
        if attachments:
            await send_to_paperless(attachments, subject, sender, account_config)
        
        # Mark as read
        imap_server.store(message_num, '+FLAGS', '\\Seen')
        
        logger.info(f"Processed email: {subject} from {sender}")
        
    except Exception as e:
        logger.error(f"Failed to process email {message_num}: {e}")

def extract_email_body(email_message) -> str:
    """Extract text body from email message"""
    body = ""
    
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode()
                break
    else:
        body = email_message.get_payload(decode=True).decode()
    
    return body

async def process_email_attachments(email_message, account_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Process email attachments"""
    attachments = []
    
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            
            filename = part.get_filename()
            if filename:
                # Save attachment
                attachment_path = await save_attachment(part, filename, account_config)
                if attachment_path:
                    attachments.append({
                        "filename": filename,
                        "path": attachment_path,
                        "content_type": part.get_content_type(),
                        "size": len(part.get_payload(decode=True))
                    })
    
    return attachments

async def save_attachment(part, filename: str, account_config: Dict[str, Any]) -> Optional[str]:
    """Save email attachment to disk"""
    try:
        # Create attachment directory
        attachment_dir = Path("/app/attachments") / account_config["name"]
        attachment_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = attachment_dir / filename
        with open(file_path, 'wb') as f:
            f.write(part.get_payload(decode=True))
        
        return str(file_path)
    except Exception as e:
        logger.error(f"Failed to save attachment {filename}: {e}")
        return None

async def send_to_paperless(attachments: List[Dict[str, Any]], subject: str, sender: str, account_config: Dict[str, Any]):
    """Send attachments to Paperless for processing"""
    try:
        async with httpx.AsyncClient() as client:
            for attachment in attachments:
                # Upload to Paperless
                with open(attachment["path"], 'rb') as f:
                    files = {'document': (attachment["filename"], f, attachment["content_type"])}
                    data = {
                        'title': f"{subject} - {attachment['filename']}",
                        'tags': f"email,{account_config['name']},{sender}",
                        'correspondent': sender
                    }
                    
                    response = await client.post(
                        f"{PAPERLESS_URL}/api/documents/post_document/",
                        files=files,
                        data=data
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"Uploaded {attachment['filename']} to Paperless")
                    else:
                        logger.error(f"Failed to upload {attachment['filename']} to Paperless")
        
    except Exception as e:
        logger.error(f"Failed to send to Paperless: {e}")

async def fetch_email_messages(account_config: Dict[str, Any], limit: int) -> List[EmailMessage]:
    """Fetch recent email messages"""
    messages = []
    
    try:
        # Connect to IMAP server
        if account_config.get("use_ssl", True):
            imap_server = imaplib.IMAP4_SSL(account_config["host"], account_config["port"])
        else:
            imap_server = imaplib.IMAP4(account_config["host"], account_config["port"])
        
        # Login
        imap_server.login(account_config["username"], account_config["password"])
        
        # Select INBOX
        imap_server.select("INBOX")
        
        # Search for recent messages
        _, message_numbers = imap_server.search(None, 'ALL')
        message_list = message_numbers[0].split()
        
        # Get recent messages (up to limit)
        recent_messages = message_list[-limit:] if len(message_list) > limit else message_list
        
        for num in recent_messages:
            try:
                _, msg_data = imap_server.fetch(num, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                body = extract_email_body(email_message)
                
                messages.append(EmailMessage(
                    id=num.decode(),
                    subject=email_message.get('Subject', ''),
                    sender=email_message.get('From', ''),
                    recipient=email_message.get('To', ''),
                    body=body,
                    received_at=email_message.get('Date', '')
                ))
            except Exception as e:
                logger.error(f"Failed to fetch message {num}: {e}")
        
        imap_server.logout()
        
    except Exception as e:
        logger.error(f"Failed to fetch email messages: {e}")
    
    return messages

def load_email_config() -> Dict[str, Any]:
    """Load email configuration"""
    config_path = "/app/config/email-config.yaml"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    else:
        return {"accounts": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 