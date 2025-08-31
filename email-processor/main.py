#!/usr/bin/env python3
"""
Enhanced Email Processor Service
Advanced email processing with LLM classification and ingest service integration
"""

import asyncio
import os
import json
import logging
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
import email
import imaplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

import httpx
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, EmailStr
import yaml
from loguru import logger

# Import LLM Manager for classification
try:
    from llm_manager import LLMClassifier
except ImportError:
    LLMClassifier = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enhanced Email Processor Service",
    description="Advanced email processing with LLM classification and ingest integration",
    version="2.0.0"
)

# Security
security = HTTPBearer()

# Configuration
class EmailConfig:
    def __init__(self):
        self.imap_host = os.getenv("IMAP_HOST", "mail.company.com")
        self.imap_port = int(os.getenv("IMAP_PORT", "993"))
        self.imap_username = os.getenv("IMAP_USERNAME", "")
        self.imap_password = os.getenv("IMAP_PASSWORD", "")
        self.imap_use_ssl = os.getenv("IMAP_USE_SSL", "true").lower() == "true"
        
        self.smtp_host = os.getenv("SMTP_HOST", "mail.company.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        self.ingest_service_url = os.getenv("INGEST_SERVICE_URL", "http://cas-ingest-service:8000")
        self.attachments_path = os.getenv("EMAIL_ATTACHMENTS_PATH", "/mnt/nas/email-attachments")
        self.enable_llm_classification = os.getenv("EMAIL_ENABLE_LLM", "true").lower() == "true"
        self.max_attachment_size = int(os.getenv("EMAIL_MAX_ATTACHMENT_SIZE", "10485760"))  # 10MB
        self.allowed_file_types = os.getenv("EMAIL_ALLOWED_TYPES", "pdf,doc,docx,xls,xlsx,jpg,png,txt").split(",")

config = EmailConfig()

# Pydantic Models
class EmailAccount(BaseModel):
    name: str
    imap_host: str
    imap_port: int
    imap_username: str
    imap_password: str
    imap_use_ssl: bool = True
    enabled: bool = True
    folders: List[str] = ["INBOX"]
    processing_rules: List[Dict[str, Any]] = []

class EmailFilter(BaseModel):
    name: str
    enabled: bool = True
    filter_subject: Optional[List[str]] = None
    filter_from: Optional[List[str]] = None
    filter_to: Optional[List[str]] = None
    filter_attachment_types: Optional[List[str]] = None
    min_attachment_size: Optional[int] = None
    max_attachment_size: Optional[int] = None
    actions: List[Dict[str, Any]] = []

class ProcessingResult(BaseModel):
    email_id: str
    subject: str
    from_address: str
    to_address: str
    received_date: str
    attachments_processed: int
    attachments_failed: int
    classification: Optional[Dict[str, Any]] = None
    ingest_results: List[Dict[str, Any]] = []
    status: str
    error: Optional[str] = None

# LLM Classifier
llm_classifier = None
if config.enable_llm_classification:
    try:
        llm_classifier = LLMClassifier()
        logger.info("LLM Classifier initialized for email processing")
    except Exception as e:
        logger.warning(f"Failed to initialize LLM Classifier: {e}")

class EmailProcessor:
    def __init__(self):
        self.accounts: List[EmailAccount] = []
        self.filters: List[EmailFilter] = []
        self.load_configuration()
        
    def load_configuration(self):
        """Load email accounts and filters from configuration"""
        config_file = "/app/config/email-config.yaml"
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                # Load accounts
                for account_data in config_data.get('email_accounts', []):
                    self.accounts.append(EmailAccount(**account_data))
                
                # Load filters
                for filter_data in config_data.get('filters', []):
                    self.filters.append(EmailFilter(**filter_data))
                
                logger.info(f"Loaded {len(self.accounts)} email accounts and {len(self.filters)} filters")
            else:
                logger.warning(f"Email processor config file not found: {config_file}")
                
        except Exception as e:
            logger.error(f"Error loading email processor configuration: {e}")
        
    def write_configuration(self, cfg: Dict[str, Any]):
        """Persist email configuration to YAML and reload in-memory structures."""
        config_file = "/app/config/email-config.yaml"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)
            # reset and reload
            self.accounts = []
            self.filters = []
            self.load_configuration()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to write email config: {e}")
    
    async def connect_imap(self, account: EmailAccount) -> Optional[imaplib.IMAP4_SSL]:
        """Connect to IMAP server"""
        try:
            if account.imap_use_ssl:
                imap = imaplib.IMAP4_SSL(account.imap_host, account.imap_port)
            else:
                imap = imaplib.IMAP4(account.imap_host, account.imap_port)
            
            imap.login(account.imap_username, account.imap_password)
            logger.info(f"Connected to IMAP server for account: {account.name}")
            return imap
            
        except Exception as e:
            logger.error(f"Failed to connect to IMAP for account {account.name}: {e}")
            return None
    
    async def fetch_emails(self, account: EmailAccount, folder: str = "INBOX", limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch emails from IMAP server"""
        try:
            imap = await self.connect_imap(account)
            if not imap:
                return []
            
            # Select folder
            imap.select(folder)
            
            # Search for unread emails
            _, message_numbers = imap.search(None, 'UNSEEN')
            
            emails = []
            for num in message_numbers[0].split()[-limit:]:  # Process last N emails
                try:
                    _, msg_data = imap.fetch(num, '(RFC822)')
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Parse email
                    email_info = {
                        'id': num.decode(),
                        'subject': email_message.get('Subject', ''),
                        'from': email_message.get('From', ''),
                        'to': email_message.get('To', ''),
                        'date': email_message.get('Date', ''),
                        'attachments': []
                    }
                    
                    # Extract attachments
                    for part in email_message.walk():
                        if part.get_content_maintype() == 'multipart':
                            continue
                        if part.get('Content-Disposition') is None:
                            continue
                        
                        filename = part.get_filename()
                        if filename:
                            # Check file type
                            file_ext = Path(filename).suffix.lower().lstrip('.')
                            if file_ext in config.allowed_file_types:
                                # Check file size
                                content = part.get_payload(decode=True)
                                if len(content) <= config.max_attachment_size:
                                    email_info['attachments'].append({
                                        'filename': filename,
                                        'content': content,
                                        'content_type': part.get_content_type(),
                                        'size': len(content)
                                    })
                    
                    emails.append(email_info)
                    
                except Exception as e:
                    logger.error(f"Error processing email {num}: {e}")
                    continue
            
            imap.logout()
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails from {account.name}: {e}")
            return []
    
    async def apply_filters(self, email_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to email and return matching actions"""
        matching_actions = []
        
        for filter_rule in self.filters:
            if not filter_rule.enabled:
                continue
            
            # Check subject filter
            if filter_rule.filter_subject:
                subject_match = any(
                    keyword.lower() in email_info['subject'].lower()
                    for keyword in filter_rule.filter_subject
                )
                if not subject_match:
                    continue
            
            # Check from filter
            if filter_rule.filter_from:
                from_match = any(
                    keyword.lower() in email_info['from'].lower()
                    for keyword in filter_rule.filter_from
                )
                if not from_match:
                    continue
            
            # Check attachment type filter
            if filter_rule.filter_attachment_types:
                attachment_types = [
                    Path(att['filename']).suffix.lower().lstrip('.')
                    for att in email_info['attachments']
                ]
                type_match = any(
                    att_type in filter_rule.filter_attachment_types
                    for att_type in attachment_types
                )
                if not type_match:
                    continue
            
            # Check attachment size filter
            if filter_rule.min_attachment_size or filter_rule.max_attachment_size:
                for attachment in email_info['attachments']:
                    size = attachment['size']
                    if filter_rule.min_attachment_size and size < filter_rule.min_attachment_size:
                        continue
                    if filter_rule.max_attachment_size and size > filter_rule.max_attachment_size:
                        continue
            
            # Add matching actions
            matching_actions.extend(filter_rule.actions)
        
        return matching_actions
    
    async def classify_email_content(self, email_info: Dict[str, Any]) -> Dict[str, Any]:
        """Classify email content using LLM"""
        if not llm_classifier:
            return {}
        
        try:
            # Prepare content for classification
            content = f"""
            Subject: {email_info['subject']}
            From: {email_info['from']}
            To: {email_info['to']}
            Date: {email_info['date']}
            Attachments: {len(email_info['attachments'])} files
            """
            
            # Get classification
            classification = await llm_classifier.classify_document(content)
            
            return {
                "category": classification.get("category", "unknown"),
                "priority": classification.get("priority", "medium"),
                "tags": classification.get("tags", []),
                "confidence": classification.get("confidence", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error classifying email: {e}")
            return {}
    
    async def process_attachment(self, attachment: Dict[str, Any], email_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process attachment through ingest service"""
        try:
            # Save attachment temporarily
            temp_dir = Path(config.attachments_path) / f"email_{email_info['id']}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = temp_dir / attachment['filename']
            with open(file_path, 'wb') as f:
                f.write(attachment['content'])
            
            # Send to ingest service
            async with httpx.AsyncClient() as client:
                with open(file_path, 'rb') as f:
                    files = {'file': (attachment['filename'], f, attachment['content_type'])}
                    data = {
                        'source': 'email',
                        'email_id': email_info['id'],
                        'email_subject': email_info['subject'],
                        'email_from': email_info['from'],
                        'email_date': email_info['date']
                    }
                    
                    response = await client.post(
                        f"{config.ingest_service_url}/api/files/upload",
                        files=files,
                        data=data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return {
                            'filename': attachment['filename'],
                            'status': 'success',
                            'ingest_id': result.get('id'),
                            'file_path': str(file_path)
                        }
                    else:
                        return {
                            'filename': attachment['filename'],
                            'status': 'failed',
                            'error': f"HTTP {response.status_code}"
                        }
            
        except Exception as e:
            logger.error(f"Error processing attachment {attachment['filename']}: {e}")
            return {
                'filename': attachment['filename'],
                'status': 'failed',
                'error': str(e)
            }

# Global processor instance
email_processor = EmailProcessor()

# Background task storage
processing_tasks: Dict[str, Dict[str, Any]] = {}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "service": "email-processor",
            "accounts_loaded": len(email_processor.accounts),
            "filters_loaded": len(email_processor.filters),
            "llm_classifier": "available" if llm_classifier else "unavailable"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/process-account/{account_name}")
async def process_email_account(
    background_tasks: BackgroundTasks,
    account_name: str,
    folder: str = "INBOX",
    limit: int = 50
):
    """Process emails from specific account"""
    
    # Find account
    account = None
    for acc in email_processor.accounts:
        if acc.name == account_name and acc.enabled:
            account = acc
            break
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found or disabled")
    
    task_id = f"process_{account_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Initialize task
    processing_tasks[task_id] = {
        "status": "processing",
        "account": account_name,
        "folder": folder,
        "emails_processed": 0,
        "emails_failed": 0,
        "attachments_processed": 0,
        "attachments_failed": 0,
        "created_at": datetime.now().isoformat()
    }
    
    # Start background task
    background_tasks.add_task(
        process_account_emails,
        task_id,
        account,
        folder,
        limit
    )
    
    return {
        "task_id": task_id,
        "status": "processing",
        "message": f"Email processing started for account {account_name}"
    }

async def process_account_emails(task_id: str, account: EmailAccount, folder: str, limit: int):
    """Background task to process account emails"""
    try:
        # Fetch emails
        emails = await email_processor.fetch_emails(account, folder, limit)
        
        processing_tasks[task_id]["total_emails"] = len(emails)
        
        for email_info in emails:
            try:
                # Apply filters
                actions = await email_processor.apply_filters(email_info)
                
                # Classify email if LLM is available
                classification = {}
                if llm_classifier:
                    classification = await email_processor.classify_email_content(email_info)
                
                # Process attachments
                ingest_results = []
                for attachment in email_info['attachments']:
                    result = await email_processor.process_attachment(attachment, email_info)
                    ingest_results.append(result)
                    
                    if result['status'] == 'success':
                        processing_tasks[task_id]["attachments_processed"] += 1
                    else:
                        processing_tasks[task_id]["attachments_failed"] += 1
                
                # Create processing result
                processing_result = ProcessingResult(
                    email_id=email_info['id'],
                    subject=email_info['subject'],
                    from_address=email_info['from'],
                    to_address=email_info['to'],
                    received_date=email_info['date'],
                    attachments_processed=len([r for r in ingest_results if r['status'] == 'success']),
                    attachments_failed=len([r for r in ingest_results if r['status'] == 'failed']),
                    classification=classification,
                    ingest_results=ingest_results,
                    status="processed"
                )
                
                processing_tasks[task_id]["emails_processed"] += 1
                
                logger.info(f"Processed email {email_info['id']}: {email_info['subject']}")
                
            except Exception as e:
                logger.error(f"Error processing email {email_info.get('id', 'unknown')}: {e}")
                processing_tasks[task_id]["emails_failed"] += 1
        
        # Update task status
        processing_tasks[task_id]["status"] = "completed"
        
        logger.info(f"Email processing task {task_id} completed")
        
    except Exception as e:
        logger.error(f"Error in email processing task {task_id}: {e}")
        processing_tasks[task_id]["status"] = "failed"
        processing_tasks[task_id]["error"] = str(e)

@app.get("/tasks/status/{task_id}")
async def get_task_status(task_id: str):
    """Get status of processing task"""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return processing_tasks[task_id]

@app.get("/tasks")
async def list_tasks():
    """List all processing tasks"""
    return {
        "tasks": [
            {"task_id": k, **v} for k, v in processing_tasks.items()
        ]
    }

@app.get("/accounts")
async def get_accounts():
    """Get email accounts configuration"""
    return {
        "accounts": [
            {
                "name": acc.name,
                "imap_host": acc.imap_host,
                "enabled": acc.enabled,
                "folders": acc.folders
            }
            for acc in email_processor.accounts
        ]
    }


@app.get("/config/email")
async def get_email_config():
    """Return email-config.yaml as raw YAML and parsed object."""
    cfg_path = Path("/app/config/email-config.yaml")
    cfg: Dict[str, Any] = {}
    raw = ""
    try:
        if cfg_path.exists():
            with open(cfg_path, 'r', encoding='utf-8') as f:
                raw = f.read()
                cfg = yaml.safe_load(raw) or {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read email config: {e}")
    return {"config": cfg, "yaml": raw}


class EmailConfigPayload(BaseModel):
    yaml_text: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


@app.put("/config/email")
async def update_email_config(payload: EmailConfigPayload):
    """Update email-config.yaml with basic validation (multiple accounts supported)."""
    if not payload.yaml_text and not payload.config:
        raise HTTPException(status_code=400, detail="Provide yaml_text or config")
    try:
        cfg: Dict[str, Any]
        if payload.yaml_text:
            cfg = yaml.safe_load(payload.yaml_text) or {}
        else:
            cfg = dict(payload.config or {})
        # Basic validation: expect 'accounts' list for multiple accounts
        if 'accounts' in cfg and not isinstance(cfg['accounts'], list):
            raise HTTPException(status_code=400, detail="'accounts' must be a list")
        # Persist
        email_processor.write_configuration(cfg)
        return {"updated": True, "accounts": len(cfg.get('accounts', []))}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid config: {e}")

@app.get("/filters")
async def get_filters():
    """Get email filters configuration"""
    return {
        "filters": [
            {
                "name": f.name,
                "enabled": f.enabled,
                "filter_subject": f.filter_subject,
                "filter_from": f.filter_from,
                "filter_attachment_types": f.filter_attachment_types
            }
            for f in email_processor.filters
        ]
    }

@app.post("/test-connection/{account_name}")
async def test_account_connection(account_name: str):
    """Test connection to email account"""
    # Find account
    account = None
    for acc in email_processor.accounts:
        if acc.name == account_name:
            account = acc
            break
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    try:
        imap = await email_processor.connect_imap(account)
        if imap:
            imap.logout()
            return {"status": "success", "message": "Connection successful"}
        else:
            return {"status": "failed", "message": "Connection failed"}
    except Exception as e:
        return {"status": "failed", "message": f"Connection error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 