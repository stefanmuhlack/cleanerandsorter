import os
import asyncio
import yaml
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import json
from loguru import logger

# Configure logging
logger.add("/app/logs/llm-manager.log", rotation="1 day", retention="7 days")

app = FastAPI(title="LLM Manager", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")

class ClassificationRequest(BaseModel):
    content: str
    model: str = "mistral-7b"
    temperature: float = 0.1
    max_tokens: int = 100

class ClassificationResponse(BaseModel):
    category: str
    confidence: float
    customer: Optional[str] = None
    project: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}

class ModelInfo(BaseModel):
    name: str
    size: int
    modified_at: str
    digest: str

class ModelPullRequest(BaseModel):
    name: str
    tag: Optional[str] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Ollama connection
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            if response.status_code != 200:
                raise HTTPException(status_code=503, detail="Ollama service unavailable")
        
        return {"status": "healthy", "service": "llm-manager"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/models")
async def list_models():
    """List available models"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            if response.status_code != 200:
                raise HTTPException(status_code=503, detail="Failed to fetch models")
            
            data = response.json()
            models = []
            for model in data.get("models", []):
                models.append(ModelInfo(
                    name=model["name"],
                    size=model.get("size", 0),
                    modified_at=model.get("modified_at", ""),
                    digest=model.get("digest", "")
                ))
            
            return {"models": models}
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail="Failed to list models")

@app.post("/models/pull")
async def pull_model(request: ModelPullRequest, background_tasks: BackgroundTasks):
    """Pull a model from Ollama"""
    try:
        model_name = f"{request.name}:{request.tag}" if request.tag else request.name
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/pull",
                json={"name": model_name}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to pull model")
            
            # Start background task to monitor pull progress
            background_tasks.add_task(monitor_model_pull, model_name)
            
            return {"message": f"Started pulling model {model_name}", "status": "pulling"}
    except Exception as e:
        logger.error(f"Failed to pull model: {e}")
        raise HTTPException(status_code=500, detail="Failed to pull model")

@app.delete("/models/{model_name}")
async def delete_model(model_name: str):
    """Delete a model"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{OLLAMA_URL}/api/delete", json={"name": model_name})
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to delete model")
            
            return {"message": f"Model {model_name} deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete model: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete model")

@app.post("/classify")
async def classify_document(request: ClassificationRequest):
    """Classify document content using LLM"""
    try:
        # Prepare prompt for classification
        prompt = f"""Classify this document into one of these categories: finanzen, projekte, personal, footage, unsorted.
Also extract customer name and project name if mentioned.

Document content: {request.content[:1000]}

Respond in JSON format:
{{
    "category": "category_name",
    "confidence": 0.95,
    "customer": "customer_name",
    "project": "project_name",
    "tags": ["tag1", "tag2"]
}}"""

        # Call Ollama API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": request.model,
                    "prompt": prompt,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    "stream": False
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=503, detail="LLM service unavailable")
            
            data = response.json()
            response_text = data.get("response", "{}")
            
            try:
                # Parse JSON response
                classification = json.loads(response_text)
                
                return ClassificationResponse(
                    category=classification.get("category", "unsorted"),
                    confidence=classification.get("confidence", 0.0),
                    customer=classification.get("customer"),
                    project=classification.get("project"),
                    tags=classification.get("tags", [])
                )
            except json.JSONDecodeError:
                # Fallback to rule-based classification
                logger.warning(f"Invalid JSON response from LLM: {response_text}")
                return await rule_based_classification(request.content)
                
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        # Fallback to rule-based classification
        return await rule_based_classification(request.content)

async def rule_based_classification(content: str) -> ClassificationResponse:
    """Fallback rule-based classification"""
    content_lower = content.lower()
    
    # Simple keyword-based classification
    if any(keyword in content_lower for keyword in ["rechnung", "invoice", "bill", "zahlung", "payment"]):
        return ClassificationResponse(category="finanzen", confidence=0.7, tags=["rechnung"])
    
    if any(keyword in content_lower for keyword in ["vertrag", "contract", "agreement", "vereinbarung"]):
        return ClassificationResponse(category="finanzen", confidence=0.7, tags=["vertrag"])
    
    if any(keyword in content_lower for keyword in ["projekt", "project", "website", "webdesign"]):
        return ClassificationResponse(category="projekte", confidence=0.6, tags=["projekt"])
    
    if any(keyword in content_lower for keyword in ["personal", "hr", "bewerbung", "application"]):
        return ClassificationResponse(category="personal", confidence=0.6, tags=["personal"])
    
    if any(keyword in content_lower for keyword in ["video", "footage", "foto", "photo", "bild"]):
        return ClassificationResponse(category="footage", confidence=0.6, tags=["media"])
    
    return ClassificationResponse(category="unsorted", confidence=0.0, tags=["unsorted"])

async def monitor_model_pull(model_name: str):
    """Monitor model pull progress"""
    logger.info(f"Monitoring pull progress for model {model_name}")
    # This would typically involve WebSocket or polling to track progress
    # For now, just log the start

@app.get("/config")
async def get_config():
    """Get LLM configuration"""
    try:
        config_path = "/app/config/llm-config.yaml"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        else:
            return {"message": "No configuration file found"}
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise HTTPException(status_code=500, detail="Failed to load configuration")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 