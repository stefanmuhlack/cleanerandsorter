#!/usr/bin/env python3
"""
OTRS Integration Service
Enhanced with ticket export, attachment extraction, and LLM classification
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

import httpx
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
import yaml
from loguru import logger

# Import LLM Manager for classification
from llm_manager import LLMClassifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OTRS Integration Service",
    description="Enhanced OTRS integration with ticket export and LLM classification",
    version="2.0.0"
)

# Security
security = HTTPBearer()

# Configuration
class OTRSConfig:
    def __init__(self):
        self.api_url = os.getenv("OTRS_API_URL", "http://otrs.company.com/otrs/nph-genericinterface.pl/Webservice/GenericTicketConnectorREST")
        self.api_key = os.getenv("OTRS_API_KEY", "")
        self.username = os.getenv("OTRS_USERNAME", "api_user")
        self.password = os.getenv("OTRS_PASSWORD", "")
        self.export_path = os.getenv("OTRS_EXPORT_PATH", "/mnt/nas/otrs-exports")
        self.attachment_path = os.getenv("OTRS_ATTACHMENT_PATH", "/mnt/nas/otrs-attachments")
        self.max_tickets_per_batch = int(os.getenv("OTRS_MAX_TICKETS", "100"))
        self.enable_llm_classification = os.getenv("OTRS_ENABLE_LLM", "true").lower() == "true"

config = OTRSConfig()

# Pydantic Models
class TicketExportRequest(BaseModel):
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    status: Optional[str] = Field(None, description="Ticket status filter")
    priority: Optional[str] = Field(None, description="Priority filter")
    queue: Optional[str] = Field(None, description="Queue filter")
    customer: Optional[str] = Field(None, description="Customer filter")
    include_attachments: bool = Field(True, description="Include attachments")
    enable_classification: bool = Field(True, description="Enable LLM classification")

class TicketInfo(BaseModel):
    ticket_id: str
    title: str
    customer: str
    status: str
    priority: str
    queue: str
    created: str
    updated: str
    attachments: List[Dict[str, Any]] = []
    classification: Optional[Dict[str, Any]] = None

class ExportResult(BaseModel):
    export_id: str
    total_tickets: int
    processed_tickets: int
    failed_tickets: int
    attachments_downloaded: int
    classification_results: int
    export_path: str
    status: str
    created_at: str

# LLM Classifier
llm_classifier = None
if config.enable_llm_classification:
    try:
        llm_classifier = LLMClassifier()
        logger.info("LLM Classifier initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize LLM Classifier: {e}")

class OTRSExporter:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=config.api_url,
            auth=(config.username, config.password),
            headers={"Content-Type": "application/json"}
        )
        
    async def get_tickets(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch tickets from OTRS API"""
        try:
            # Build query parameters
            params = {
                "UserLogin": config.username,
                "Password": config.password,
                "Limit": config.max_tickets_per_batch
            }
            
            if filters.get("start_date"):
                params["CreatedTimeNewerDate"] = filters["start_date"]
            if filters.get("end_date"):
                params["CreatedTimeOlderDate"] = filters["end_date"]
            if filters.get("status"):
                params["StateType"] = filters["status"]
            if filters.get("priority"):
                params["PriorityIDs"] = filters["priority"]
            if filters.get("queue"):
                params["QueueIDs"] = filters["queue"]
                
            response = await self.client.get("/Ticket", params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get("Ticket", [])
            
        except Exception as e:
            logger.error(f"Error fetching tickets: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch tickets: {str(e)}")
    
    async def get_ticket_details(self, ticket_id: str) -> Dict[str, Any]:
        """Get detailed ticket information including attachments"""
        try:
            params = {
                "UserLogin": config.username,
                "Password": config.password,
                "TicketID": ticket_id,
                "AllArticles": 1,
                "Attachments": 1
            }
            
            response = await self.client.get(f"/Ticket/{ticket_id}", params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching ticket {ticket_id}: {e}")
            return {}
    
    async def download_attachment(self, ticket_id: str, attachment_id: str, filename: str) -> str:
        """Download attachment from OTRS"""
        try:
            # Create attachment directory
            attachment_dir = Path(config.attachment_path) / ticket_id
            attachment_dir.mkdir(parents=True, exist_ok=True)
            
            # Download attachment
            params = {
                "UserLogin": config.username,
                "Password": config.password,
                "TicketID": ticket_id,
                "ArticleID": attachment_id
            }
            
            response = await self.client.get(f"/Ticket/{ticket_id}/Article/{attachment_id}/Attachment/{attachment_id}", params=params)
            response.raise_for_status()
            
            # Save attachment
            file_path = attachment_dir / filename
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded attachment: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error downloading attachment {attachment_id}: {e}")
            return ""

# Global exporter instance
exporter = OTRSExporter()

# Background task storage
export_tasks: Dict[str, Dict[str, Any]] = {}

async def classify_ticket_content(ticket_info: Dict[str, Any]) -> Dict[str, Any]:
    """Classify ticket content using LLM"""
    if not llm_classifier:
        return {}
    
    try:
        # Prepare content for classification
        content = f"""
        Ticket: {ticket_info.get('Title', '')}
        Customer: {ticket_info.get('CustomerUserID', '')}
        Queue: {ticket_info.get('Queue', '')}
        Priority: {ticket_info.get('Priority', '')}
        Status: {ticket_info.get('State', '')}
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
        logger.error(f"Error classifying ticket: {e}")
        return {}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test OTRS connection
        test_response = await exporter.client.get("/", timeout=5.0)
        otrs_status = "connected" if test_response.status_code == 200 else "disconnected"
        
        return {
            "status": "healthy",
            "service": "otrs-integration",
            "otrs_connection": otrs_status,
            "llm_classifier": "available" if llm_classifier else "unavailable"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/export-tickets", response_model=ExportResult)
async def export_tickets(
    background_tasks: BackgroundTasks,
    request: TicketExportRequest
):
    """Export tickets within a date range with enhanced features"""
    
    export_id = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Initialize export task
    export_tasks[export_id] = {
        "status": "processing",
        "total_tickets": 0,
        "processed_tickets": 0,
        "failed_tickets": 0,
        "attachments_downloaded": 0,
        "classification_results": 0,
        "created_at": datetime.now().isoformat()
    }
    
    # Start background task
    background_tasks.add_task(
        process_ticket_export,
        export_id,
        request
    )
    
    return ExportResult(
        export_id=export_id,
        total_tickets=0,
        processed_tickets=0,
        failed_tickets=0,
        attachments_downloaded=0,
        classification_results=0,
        export_path=config.export_path,
        status="processing",
        created_at=datetime.now().isoformat()
    )

async def process_ticket_export(export_id: str, request: TicketExportRequest):
    """Background task to process ticket export"""
    try:
        # Create export directory
        export_dir = Path(config.export_path) / export_id
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Build filters
        filters = {}
        if request.start_date:
            filters["start_date"] = request.start_date
        if request.end_date:
            filters["end_date"] = request.end_date
        if request.status:
            filters["status"] = request.status
        if request.priority:
            filters["priority"] = request.priority
        if request.queue:
            filters["queue"] = request.queue
        if request.customer:
            filters["customer"] = request.customer
        
        # Fetch tickets
        tickets = await exporter.get_tickets(filters)
        export_tasks[export_id]["total_tickets"] = len(tickets)
        
        processed_tickets = []
        
        for ticket in tickets:
            try:
                # Get detailed ticket information
                ticket_details = await exporter.get_ticket_details(ticket["TicketID"])
                
                if not ticket_details:
                    export_tasks[export_id]["failed_tickets"] += 1
                    continue
                
                # Process attachments if requested
                attachments = []
                if request.include_attachments:
                    for article in ticket_details.get("Article", []):
                        for attachment in article.get("Attachment", []):
                            if attachment.get("Filename"):
                                file_path = await exporter.download_attachment(
                                    ticket["TicketID"],
                                    article["ArticleID"],
                                    attachment["Filename"]
                                )
                                if file_path:
                                    attachments.append({
                                        "filename": attachment["Filename"],
                                        "path": file_path,
                                        "size": attachment.get("Filesize", 0)
                                    })
                                    export_tasks[export_id]["attachments_downloaded"] += 1
                
                # Classify ticket if requested
                classification = {}
                if request.enable_classification and llm_classifier:
                    classification = await classify_ticket_content(ticket_details)
                    if classification:
                        export_tasks[export_id]["classification_results"] += 1
                
                # Create ticket info
                ticket_info = TicketInfo(
                    ticket_id=ticket["TicketID"],
                    title=ticket_details.get("Title", ""),
                    customer=ticket_details.get("CustomerUserID", ""),
                    status=ticket_details.get("State", ""),
                    priority=ticket_details.get("Priority", ""),
                    queue=ticket_details.get("Queue", ""),
                    created=ticket_details.get("Created", ""),
                    updated=ticket_details.get("Changed", ""),
                    attachments=attachments,
                    classification=classification
                )
                
                processed_tickets.append(ticket_info.dict())
                export_tasks[export_id]["processed_tickets"] += 1
                
            except Exception as e:
                logger.error(f"Error processing ticket {ticket.get('TicketID')}: {e}")
                export_tasks[export_id]["failed_tickets"] += 1
        
        # Save export results
        export_file = export_dir / "tickets_export.json"
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(processed_tickets, f, indent=2, ensure_ascii=False)
        
        # Update task status
        export_tasks[export_id]["status"] = "completed"
        export_tasks[export_id]["export_path"] = str(export_file)
        
        logger.info(f"Export {export_id} completed: {len(processed_tickets)} tickets processed")
        
    except Exception as e:
        logger.error(f"Error in export task {export_id}: {e}")
        export_tasks[export_id]["status"] = "failed"
        export_tasks[export_id]["error"] = str(e)

@app.get("/export-status/{export_id}")
async def get_export_status(export_id: str):
    """Get status of export task"""
    if export_id not in export_tasks:
        raise HTTPException(status_code=404, detail="Export not found")
    
    return export_tasks[export_id]

@app.get("/exports")
async def list_exports():
    """List all export tasks"""
    return {
        "exports": [
            {"export_id": k, **v} for k, v in export_tasks.items()
        ]
}

@app.delete("/export/{export_id}")
async def delete_export(export_id: str):
    """Delete export and associated files"""
    if export_id not in export_tasks:
        raise HTTPException(status_code=404, detail="Export not found")
    
    try:
        # Remove export directory
        export_dir = Path(config.export_path) / export_id
        if export_dir.exists():
            shutil.rmtree(export_dir)
        
        # Remove from tasks
        del export_tasks[export_id]
        
        return {"message": f"Export {export_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting export {export_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete export: {str(e)}")

@app.get("/tickets/recent")
async def get_recent_tickets(limit: int = 10):
    """Get recent tickets for dashboard"""
    try:
        # Get tickets from last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        filters = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }
        
        tickets = await exporter.get_tickets(filters)
        
        # Return limited results
        return {
            "tickets": tickets[:limit],
            "total": len(tickets),
            "period": "last_7_days"
        }
        
    except Exception as e:
        logger.error(f"Error fetching recent tickets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent tickets: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 