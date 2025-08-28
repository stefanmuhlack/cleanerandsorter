#!/usr/bin/env python3
"""
TLD and Email Management Service
Handles domain renewals, billing, and automated reports
"""

import asyncio
import os
import json
import logging
import smtplib
import ssl
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
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
import schedule
import time
import threading

# Import LLM Manager for report generation
from llm_manager import LLMClassifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TLD and Email Management Service",
    description="Comprehensive domain and email management with automated reports",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# Configuration
class TLDConfig:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "mail.company.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        self.reports_path = os.getenv("TLD_REPORTS_PATH", "/mnt/nas/tld-reports")
        self.domains_file = os.getenv("TLD_DOMAINS_FILE", "/app/config/domains.yaml")
        self.enable_automated_reports = os.getenv("TLD_AUTO_REPORTS", "true").lower() == "true"
        self.report_schedule = os.getenv("TLD_REPORT_SCHEDULE", "weekly")  # daily, weekly, monthly

config = TLDConfig()

# Pydantic Models
class DomainInfo(BaseModel):
    domain: str
    registrar: str
    registration_date: str
    expiry_date: str
    renewal_date: str
    status: str = "active"
    customer: str
    billing_email: EmailStr
    annual_cost: float
    auto_renewal: bool = True
    notes: Optional[str] = None

class EmailTemplate(BaseModel):
    name: str
    subject: str
    body: str
    variables: List[str] = []

class ReportRequest(BaseModel):
    report_type: str = Field(..., description="Type of report: renewal, billing, status")
    domains: Optional[List[str]] = Field(None, description="Specific domains to include")
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range for report")
    format: str = Field("pdf", description="Report format: pdf, csv, json")
    send_email: bool = Field(True, description="Send report via email")

class EmailRequest(BaseModel):
    to: List[EmailStr]
    subject: str
    body: str
    attachments: Optional[List[str]] = []
    template: Optional[str] = None
    template_variables: Optional[Dict[str, Any]] = {}

# LLM Classifier for report generation
llm_classifier = None
if config.enable_automated_reports:
    try:
        llm_classifier = LLMClassifier()
        logger.info("LLM Classifier initialized for TLD management")
    except Exception as e:
        logger.warning(f"Failed to initialize LLM Classifier: {e}")

class TLDManager:
    def __init__(self):
        self.domains: List[DomainInfo] = []
        self.email_templates: Dict[str, EmailTemplate] = {}
        self.load_domains()
        self.load_email_templates()
    
    def load_domains(self):
        """Load domain information from configuration"""
        try:
            if os.path.exists(config.domains_file):
                with open(config.domains_file, 'r', encoding='utf-8') as f:
                    domains_data = yaml.safe_load(f)
                    
                for domain_data in domains_data.get('domains', []):
                    self.domains.append(DomainInfo(**domain_data))
                    
                logger.info(f"Loaded {len(self.domains)} domains")
            else:
                logger.warning(f"Domains file not found: {config.domains_file}")
                
        except Exception as e:
            logger.error(f"Error loading domains: {e}")
    
    def load_email_templates(self):
        """Load email templates"""
        templates_file = "/app/config/email_templates.yaml"
        try:
            if os.path.exists(templates_file):
                with open(templates_file, 'r', encoding='utf-8') as f:
                    templates_data = yaml.safe_load(f)
                    
                for template_data in templates_data.get('templates', []):
                    template = EmailTemplate(**template_data)
                    self.email_templates[template.name] = template
                    
                logger.info(f"Loaded {len(self.email_templates)} email templates")
            else:
                # Create default templates
                self.create_default_templates()
                
        except Exception as e:
            logger.error(f"Error loading email templates: {e}")
            self.create_default_templates()
    
    def create_default_templates(self):
        """Create default email templates"""
        default_templates = {
            "domain_renewal": EmailTemplate(
                name="domain_renewal",
                subject="Domain Renewal Reminder - {domain}",
                body="""
                Dear {customer},
                
                This is a reminder that your domain {domain} will expire on {expiry_date}.
                
                Domain Details:
                - Domain: {domain}
                - Registrar: {registrar}
                - Expiry Date: {expiry_date}
                - Annual Cost: €{annual_cost}
                
                Please ensure timely renewal to avoid service interruption.
                
                Best regards,
                Your Domain Management Team
                """,
                variables=["domain", "customer", "expiry_date", "registrar", "annual_cost"]
            ),
            "billing_report": EmailTemplate(
                name="billing_report",
                subject="Domain Billing Report - {month_year}",
                body="""
                Dear {customer},
                
                Please find attached your domain billing report for {month_year}.
                
                Summary:
                - Total Domains: {total_domains}
                - Total Annual Cost: €{total_cost}
                - Renewals Due: {renewals_due}
                
                Best regards,
                Your Domain Management Team
                """,
                variables=["customer", "month_year", "total_domains", "total_cost", "renewals_due"]
            )
        }
        
        self.email_templates.update(default_templates)
        logger.info("Created default email templates")

class EmailManager:
    def __init__(self):
        self.smtp_host = config.smtp_host
        self.smtp_port = config.smtp_port
        self.smtp_username = config.smtp_username
        self.smtp_password = config.smtp_password
        self.smtp_use_tls = config.smtp_use_tls
    
    async def send_email(self, to: List[str], subject: str, body: str, attachments: List[str] = []) -> bool:
        """Send email with attachments"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = ', '.join(to)
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            for attachment_path in attachments:
                if os.path.exists(attachment_path):
                    with open(attachment_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(attachment_path)}'
                    )
                    msg.attach(part)
            
            # Send email
            context = ssl.create_default_context()
            
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls(context=context)
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context)
            
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {to}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def render_template(self, template_name: str, variables: Dict[str, Any]) -> tuple:
        """Render email template with variables"""
        if template_name not in tld_manager.email_templates:
            raise ValueError(f"Template {template_name} not found")
        
        template = tld_manager.email_templates[template_name]
        
        # Replace variables in subject and body
        subject = template.subject
        body = template.body
        
        for var_name, var_value in variables.items():
            subject = subject.replace(f"{{{var_name}}}", str(var_value))
            body = body.replace(f"{{{var_name}}}", str(var_value))
        
        return subject, body

class ReportGenerator:
    def __init__(self):
        self.reports_path = Path(config.reports_path)
        self.reports_path.mkdir(parents=True, exist_ok=True)
    
    async def generate_renewal_report(self, domains: Optional[List[str]] = None) -> str:
        """Generate domain renewal report"""
        try:
            # Filter domains
            target_domains = []
            if domains:
                target_domains = [d for d in tld_manager.domains if d.domain in domains]
            else:
                # Get domains expiring in next 30 days
                thirty_days_from_now = datetime.now() + timedelta(days=30)
                target_domains = [
                    d for d in tld_manager.domains 
                    if datetime.strptime(d.expiry_date, "%Y-%m-%d") <= thirty_days_from_now
                ]
            
            # Generate report content
            report_content = {
                "report_type": "domain_renewal",
                "generated_at": datetime.now().isoformat(),
                "total_domains": len(target_domains),
                "domains": [d.dict() for d in target_domains],
                "summary": {
                    "expiring_soon": len([d for d in target_domains if 
                        datetime.strptime(d.expiry_date, "%Y-%m-%d") <= datetime.now() + timedelta(days=7)]),
                    "total_cost": sum(d.annual_cost for d in target_domains),
                    "customers": list(set(d.customer for d in target_domains))
                }
            }
            
            # Save report
            report_file = self.reports_path / f"renewal_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_content, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Renewal report generated: {report_file}")
            return str(report_file)
            
        except Exception as e:
            logger.error(f"Error generating renewal report: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate renewal report: {str(e)}")
    
    async def generate_billing_report(self, date_range: Optional[Dict[str, str]] = None) -> str:
        """Generate billing report"""
        try:
            # Filter domains by date range if provided
            target_domains = tld_manager.domains
            if date_range:
                start_date = datetime.strptime(date_range["start"], "%Y-%m-%d")
                end_date = datetime.strptime(date_range["end"], "%Y-%m-%d")
                target_domains = [
                    d for d in tld_manager.domains
                    if start_date <= datetime.strptime(d.renewal_date, "%Y-%m-%d") <= end_date
                ]
            
            # Generate report content
            report_content = {
                "report_type": "billing",
                "generated_at": datetime.now().isoformat(),
                "date_range": date_range,
                "total_domains": len(target_domains),
                "domains": [d.dict() for d in target_domains],
                "summary": {
                    "total_cost": sum(d.annual_cost for d in target_domains),
                    "customers": list(set(d.customer for d in target_domains)),
                    "registrars": list(set(d.registrar for d in target_domains))
                }
            }
            
            # Save report
            report_file = self.reports_path / f"billing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_content, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Billing report generated: {report_file}")
            return str(report_file)
            
        except Exception as e:
            logger.error(f"Error generating billing report: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate billing report: {str(e)}")

# Global instances
tld_manager = TLDManager()
email_manager = EmailManager()
report_generator = ReportGenerator()

# Background task storage
report_tasks: Dict[str, Dict[str, Any]] = {}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "service": "tld-manager",
            "domains_loaded": len(tld_manager.domains),
            "templates_loaded": len(tld_manager.email_templates),
            "llm_classifier": "available" if llm_classifier else "unavailable"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/domains")
async def get_domains():
    """Get all domains"""
    return {
        "domains": [d.dict() for d in tld_manager.domains],
        "total": len(tld_manager.domains)
    }

@app.get("/domains/{domain}")
async def get_domain(domain: str):
    """Get specific domain information"""
    for d in tld_manager.domains:
        if d.domain == domain:
            return d.dict()
    
    raise HTTPException(status_code=404, detail="Domain not found")

@app.get("/domains/expiring-soon")
async def get_expiring_domains(days: int = 30):
    """Get domains expiring within specified days"""
    target_date = datetime.now() + timedelta(days=days)
    expiring_domains = [
        d for d in tld_manager.domains
        if datetime.strptime(d.expiry_date, "%Y-%m-%d") <= target_date
    ]
    
    return {
        "domains": [d.dict() for d in expiring_domains],
        "total": len(expiring_domains),
        "days_ahead": days
    }

@app.post("/reports/generate")
async def generate_report(
    background_tasks: BackgroundTasks,
    request: ReportRequest
):
    """Generate report with background processing"""
    
    report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Initialize report task
    report_tasks[report_id] = {
        "status": "processing",
        "report_type": request.report_type,
        "created_at": datetime.now().isoformat()
    }
    
    # Start background task
    background_tasks.add_task(
        process_report_generation,
        report_id,
        request
    )
    
    return {
        "report_id": report_id,
        "status": "processing",
        "message": f"Report generation started for {request.report_type}"
    }

async def process_report_generation(report_id: str, request: ReportRequest):
    """Background task to generate report"""
    try:
        report_file = None
        
        # Generate report based on type
        if request.report_type == "renewal":
            report_file = await report_generator.generate_renewal_report(request.domains)
        elif request.report_type == "billing":
            report_file = await report_generator.generate_billing_report(request.date_range)
        else:
            raise ValueError(f"Unknown report type: {request.report_type}")
        
        # Send email if requested
        if request.send_email and report_file:
            # Get customer emails for the report
            customer_emails = []
            if request.report_type == "renewal":
                # Get emails for domains in the report
                domains = request.domains or [d.domain for d in tld_manager.domains]
                customer_emails = list(set([
                    d.billing_email for d in tld_manager.domains 
                    if d.domain in domains
                ]))
            
            if customer_emails:
                # Send email with report
                subject = f"Domain {request.report_type.title()} Report"
                body = f"Please find attached the {request.report_type} report."
                
                await email_manager.send_email(
                    to=customer_emails,
                    subject=subject,
                    body=body,
                    attachments=[report_file]
                )
        
        # Update task status
        report_tasks[report_id]["status"] = "completed"
        report_tasks[report_id]["report_file"] = report_file
        
        logger.info(f"Report {report_id} completed: {report_file}")
        
    except Exception as e:
        logger.error(f"Error in report generation {report_id}: {e}")
        report_tasks[report_id]["status"] = "failed"
        report_tasks[report_id]["error"] = str(e)

@app.get("/reports/status/{report_id}")
async def get_report_status(report_id: str):
    """Get status of report generation"""
    if report_id not in report_tasks:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report_tasks[report_id]

@app.post("/email/send")
async def send_email(request: EmailRequest):
    """Send email with template support"""
    try:
        subject = request.subject
        body = request.body
        
        # Use template if specified
        if request.template:
            subject, body = email_manager.render_template(
                request.template, 
                request.template_variables or {}
            )
        
        # Send email
        success = await email_manager.send_email(
            to=request.to,
            subject=subject,
            body=body,
            attachments=request.attachments or []
        )
        
        if success:
            return {"message": "Email sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
            
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@app.get("/templates")
async def get_email_templates():
    """Get available email templates"""
    return {
        "templates": [
            {"name": name, "subject": template.subject, "variables": template.variables}
            for name, template in tld_manager.email_templates.items()
        ]
    }

# Automated report scheduling
def schedule_automated_reports():
    """Schedule automated reports"""
    if not config.enable_automated_reports:
        return
    
    if config.report_schedule == "daily":
        schedule.every().day.at("09:00").do(generate_daily_reports)
    elif config.report_schedule == "weekly":
        schedule.every().monday.at("09:00").do(generate_weekly_reports)
    elif config.report_schedule == "monthly":
        schedule.every().month.at("09:00").do(generate_monthly_reports)
    
    logger.info(f"Automated reports scheduled: {config.report_schedule}")

def generate_daily_reports():
    """Generate daily reports"""
    asyncio.run(generate_automated_report("renewal"))

def generate_weekly_reports():
    """Generate weekly reports"""
    asyncio.run(generate_automated_report("billing"))

def generate_monthly_reports():
    """Generate monthly reports"""
    asyncio.run(generate_automated_report("billing"))

async def generate_automated_report(report_type: str):
    """Generate automated report"""
    try:
        logger.info(f"Generating automated {report_type} report")
        
        if report_type == "renewal":
            report_file = await report_generator.generate_renewal_report()
        elif report_type == "billing":
            report_file = await report_generator.generate_billing_report()
        else:
            return
        
        # Send to admin email
        admin_email = os.getenv("ADMIN_EMAIL", "admin@company.com")
        if admin_email:
            await email_manager.send_email(
                to=[admin_email],
                subject=f"Automated {report_type.title()} Report",
                body=f"Automated {report_type} report generated successfully.",
                attachments=[report_file]
            )
        
        logger.info(f"Automated {report_type} report completed")
        
    except Exception as e:
        logger.error(f"Error generating automated {report_type} report: {e}")

# Start scheduling in background
if config.enable_automated_reports:
    schedule_automated_reports()
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Automated report scheduler started")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 