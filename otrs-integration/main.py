import os
import asyncio
import yaml
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
import requests
from datetime import datetime, timedelta

# Configure logging
logger.add("/app/logs/otrs-integration.log", rotation="1 day", retention="7 days")

app = FastAPI(title="OTRS Integration", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OTRS_API_URL = os.getenv("OTRS_API_URL", "http://otrs.company.com/api")
OTRS_API_KEY = os.getenv("OTRS_API_KEY", "")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://cas_user:cas_password@rabbitmq:5672/")
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")

class TicketInfo(BaseModel):
    ticket_id: str
    subject: str
    customer: str
    status: str
    priority: str
    created_at: str
    attachments: List[Dict[str, Any]] = []

class ProcessingResult(BaseModel):
    success: bool
    message: str
    processed_tickets: int = 0
    processed_attachments: int = 0
    errors: List[str] = []

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {"status": "healthy", "service": "otrs-integration"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/tickets")
async def get_tickets(limit: int = 50, status: Optional[str] = None):
    """Get tickets from OTRS"""
    try:
        config = load_otrs_config()
        
        # Build API request
        params = {
            "limit": limit,
            "api_key": OTRS_API_KEY
        }
        
        if status:
            params["status"] = status
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OTRS_API_URL}/tickets", params=params)
            
            if response.status_code != 200:
                raise HTTPException(status_code=503, detail="Failed to fetch tickets from OTRS")
            
            data = response.json()
            tickets = []
            
            for ticket_data in data.get("tickets", []):
                tickets.append(TicketInfo(
                    ticket_id=ticket_data["ticket_id"],
                    subject=ticket_data["subject"],
                    customer=ticket_data.get("customer", ""),
                    status=ticket_data["status"],
                    priority=ticket_data.get("priority", "normal"),
                    created_at=ticket_data["created_at"],
                    attachments=ticket_data.get("attachments", [])
                ))
            
            return {"tickets": tickets}
            
    except Exception as e:
        logger.error(f"Failed to fetch tickets: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tickets")

@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    """Get specific ticket details"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OTRS_API_URL}/tickets/{ticket_id}",
                params={"api_key": OTRS_API_KEY}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Ticket not found")
            
            ticket_data = response.json()
            
            return TicketInfo(
                ticket_id=ticket_data["ticket_id"],
                subject=ticket_data["subject"],
                customer=ticket_data.get("customer", ""),
                status=ticket_data["status"],
                priority=ticket_data.get("priority", "normal"),
                created_at=ticket_data["created_at"],
                attachments=ticket_data.get("attachments", [])
            )
            
    except Exception as e:
        logger.error(f"Failed to fetch ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ticket")

@app.get("/tickets/{ticket_id}/attachments")
async def get_ticket_attachments(ticket_id: str):
    """Get attachments for a specific ticket"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OTRS_API_URL}/tickets/{ticket_id}/attachments",
                params={"api_key": OTRS_API_KEY}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Ticket attachments not found")
            
            return response.json()
            
    except Exception as e:
        logger.error(f"Failed to fetch attachments for ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch attachments")

@app.post("/tickets/{ticket_id}/download-attachments")
async def download_ticket_attachments(ticket_id: str, background_tasks: BackgroundTasks):
    """Download all attachments for a ticket"""
    try:
        # Start background download
        background_tasks.add_task(download_attachments, ticket_id)
        
        return {"message": f"Started downloading attachments for ticket {ticket_id}", "status": "downloading"}
        
    except Exception as e:
        logger.error(f"Failed to start attachment download for ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start download")

@app.post("/export-tickets")
async def export_tickets(
    background_tasks: BackgroundTasks,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None
):
    """Export tickets within a date range"""
    try:
        # Set default date range if not provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Start background export
        background_tasks.add_task(export_tickets_range, start_date, end_date, status)
        
        return {
            "message": f"Started exporting tickets from {start_date} to {end_date}",
            "status": "exporting",
            "date_range": {"start": start_date, "end": end_date}
        }
        
    except Exception as e:
        logger.error(f"Failed to start ticket export: {e}")
        raise HTTPException(status_code=500, detail="Failed to start export")

async def download_attachments(ticket_id: str):
    """Download attachments for a ticket"""
    try:
        logger.info(f"Starting attachment download for ticket {ticket_id}")
        
        # Get ticket attachments
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OTRS_API_URL}/tickets/{ticket_id}/attachments",
                params={"api_key": OTRS_API_KEY}
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get attachments for ticket {ticket_id}")
                return
            
            attachments = response.json().get("attachments", [])
            
            # Create ticket directory
            ticket_dir = Path("/app/attachments") / f"ticket_{ticket_id}"
            ticket_dir.mkdir(parents=True, exist_ok=True)
            
            # Download each attachment
            for attachment in attachments:
                await download_single_attachment(ticket_id, attachment, ticket_dir)
        
        logger.info(f"Completed attachment download for ticket {ticket_id}")
        
    except Exception as e:
        logger.error(f"Failed to download attachments for ticket {ticket_id}: {e}")

async def download_single_attachment(ticket_id: str, attachment: Dict[str, Any], ticket_dir: Path):
    """Download a single attachment"""
    try:
        attachment_id = attachment["id"]
        filename = attachment["filename"]
        
        # Download attachment
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OTRS_API_URL}/tickets/{ticket_id}/attachments/{attachment_id}/download",
                params={"api_key": OTRS_API_KEY}
            )
            
            if response.status_code == 200:
                # Save attachment
                file_path = ticket_dir / filename
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded attachment {filename} for ticket {ticket_id}")
                
                # Process attachment (send to ingest service)
                await process_attachment(file_path, ticket_id, attachment)
            else:
                logger.error(f"Failed to download attachment {filename} for ticket {ticket_id}")
        
    except Exception as e:
        logger.error(f"Failed to download attachment for ticket {ticket_id}: {e}")

async def process_attachment(file_path: Path, ticket_id: str, attachment: Dict[str, Any]):
    """Process downloaded attachment"""
    try:
        # Send to ingest service for processing
        async with httpx.AsyncClient() as client:
            with open(file_path, 'rb') as f:
                files = {'file': (attachment["filename"], f, attachment.get("content_type", "application/octet-stream"))}
                data = {
                    'ticket_id': ticket_id,
                    'source': 'otrs',
                    'metadata': json.dumps(attachment)
                }
                
                response = await client.post(
                    "http://ingest-service:8000/api/files/upload",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    logger.info(f"Sent attachment {attachment['filename']} to ingest service")
                else:
                    logger.error(f"Failed to send attachment {attachment['filename']} to ingest service")
        
    except Exception as e:
        logger.error(f"Failed to process attachment {attachment['filename']}: {e}")

async def export_tickets_range(start_date: str, end_date: str, status: Optional[str] = None):
    """Export tickets within a date range"""
    try:
        logger.info(f"Starting ticket export from {start_date} to {end_date}")
        
        # Build API request
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "api_key": OTRS_API_KEY,
            "include_attachments": True
        }
        
        if status:
            params["status"] = status
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OTRS_API_URL}/tickets/export", params=params)
            
            if response.status_code != 200:
                logger.error("Failed to export tickets from OTRS")
                return
            
            export_data = response.json()
            tickets = export_data.get("tickets", [])
            
            # Create export directory
            export_dir = Path("/app/attachments") / f"export_{start_date}_{end_date}"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Process each ticket
            for ticket in tickets:
                await process_exported_ticket(ticket, export_dir)
            
            logger.info(f"Completed ticket export: {len(tickets)} tickets processed")
        
    except Exception as e:
        logger.error(f"Failed to export tickets: {e}")

async def process_exported_ticket(ticket: Dict[str, Any], export_dir: Path):
    """Process an exported ticket"""
    try:
        ticket_id = ticket["ticket_id"]
        ticket_dir = export_dir / f"ticket_{ticket_id}"
        ticket_dir.mkdir(exist_ok=True)
        
        # Save ticket metadata
        metadata_file = ticket_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(ticket, f, indent=2)
        
        # Process attachments
        attachments = ticket.get("attachments", [])
        for attachment in attachments:
            await download_single_attachment(ticket_id, attachment, ticket_dir)
        
        logger.info(f"Processed exported ticket {ticket_id}")
        
    except Exception as e:
        logger.error(f"Failed to process exported ticket {ticket.get('ticket_id', 'unknown')}: {e}")

def load_otrs_config() -> Dict[str, Any]:
    """Load OTRS configuration"""
    config_path = "/app/config/otrs-config.yaml"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    else:
        return {"api": {"url": OTRS_API_URL, "key": OTRS_API_KEY}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 