"""
Advanced LLM Service for CAS Platform
Integrates with Ollama for document classification and content analysis.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import aiohttp
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Available LLM models."""
    MISTRAL_7B = "mistral:7b"
    LLAMA2_7B = "llama2:7b"
    CODEGEMMA_7B = "codegemma:7b"
    NEURAL_CHAT = "neural-chat:7b"
    QWEN_7B = "qwen:7b"


@dataclass
class ClassificationResult:
    """Result of document classification."""
    document_type: str
    confidence: float
    categories: List[str]
    tags: List[str]
    summary: str
    metadata: Dict[str, Any]


@dataclass
class ContentAnalysis:
    """Result of content analysis."""
    key_topics: List[str]
    sentiment: str
    entities: List[Dict[str, Any]]
    language: str
    readability_score: float
    summary: str


class LLMService:
    """
    Advanced LLM service for document processing and analysis.
    
    Features:
    - Document classification
    - Content analysis
    - Entity extraction
    - Sentiment analysis
    - Multi-language support
    - Batch processing
    """
    
    def __init__(self, ollama_url: str = "http://ollama:11434"):
        self.ollama_url = ollama_url
        self.default_model = ModelType.MISTRAL_7B.value
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to Ollama API."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.ollama_url}/api/{endpoint}"
        
        try:
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama API error: {response.status} - {error_text}")
                    raise Exception(f"Ollama API error: {response.status}")
        except Exception as e:
            logger.error(f"Request to Ollama failed: {e}")
            raise
    
    async def classify_document(self, content: str, file_extension: str = None) -> ClassificationResult:
        """
        Classify document based on content and file type.
        
        Args:
            content: Document content (first 2000 characters)
            file_extension: File extension for additional context
            
        Returns:
            ClassificationResult with document type and metadata
        """
        # Truncate content for efficiency
        truncated_content = content[:2000] if len(content) > 2000 else content
        
        prompt = f"""
        Analyze this document and classify it. Return a JSON response with the following structure:
        {{
            "document_type": "invoice|contract|report|email|presentation|other",
            "confidence": 0.95,
            "categories": ["finance", "legal", "technical"],
            "tags": ["urgent", "confidential", "draft"],
            "summary": "Brief summary of the document content",
            "metadata": {{
                "language": "en",
                "page_count": 1,
                "has_signatures": false,
                "is_legal_document": false
            }}
        }}
        
        Document content:
        {truncated_content}
        
        File type: {file_extension or 'unknown'}
        
        Respond only with valid JSON:
        """
        
        try:
            response = await self._make_request("generate", {
                "model": self.default_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 500
                }
            })
            
            # Extract JSON from response
            response_text = response.get("response", "")
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                
                return ClassificationResult(
                    document_type=result.get("document_type", "other"),
                    confidence=result.get("confidence", 0.0),
                    categories=result.get("categories", []),
                    tags=result.get("tags", []),
                    summary=result.get("summary", ""),
                    metadata=result.get("metadata", {})
                )
            else:
                # Fallback classification
                return self._fallback_classification(content, file_extension)
                
        except Exception as e:
            logger.error(f"Document classification failed: {e}")
            return self._fallback_classification(content, file_extension)
    
    def _fallback_classification(self, content: str, file_extension: str) -> ClassificationResult:
        """Fallback classification based on simple rules."""
        content_lower = content.lower()
        
        # Simple rule-based classification
        if any(word in content_lower for word in ["invoice", "bill", "payment", "amount", "total"]):
            doc_type = "invoice"
            categories = ["finance"]
        elif any(word in content_lower for word in ["contract", "agreement", "terms", "conditions"]):
            doc_type = "contract"
            categories = ["legal"]
        elif any(word in content_lower for word in ["report", "analysis", "findings", "conclusion"]):
            doc_type = "report"
            categories = ["business"]
        elif any(word in content_lower for word in ["@", "subject:", "from:", "to:"]):
            doc_type = "email"
            categories = ["communication"]
        else:
            doc_type = "other"
            categories = ["general"]
        
        return ClassificationResult(
            document_type=doc_type,
            confidence=0.6,
            categories=categories,
            tags=[],
            summary="Fallback classification",
            metadata={"language": "en", "fallback": True}
        )
    
    async def analyze_content(self, content: str) -> ContentAnalysis:
        """
        Perform comprehensive content analysis.
        
        Args:
            content: Document content to analyze
            
        Returns:
            ContentAnalysis with detailed insights
        """
        truncated_content = content[:3000] if len(content) > 3000 else content
        
        prompt = f"""
        Analyze this document content and provide detailed insights. Return a JSON response:
        {{
            "key_topics": ["topic1", "topic2"],
            "sentiment": "positive|negative|neutral",
            "entities": [
                {{"name": "entity_name", "type": "person|organization|location|date", "value": "entity_value"}}
            ],
            "language": "en",
            "readability_score": 0.75,
            "summary": "Comprehensive summary of the content"
        }}
        
        Content:
        {truncated_content}
        
        Respond only with valid JSON:
        """
        
        try:
            response = await self._make_request("generate", {
                "model": self.default_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "num_predict": 800
                }
            })
            
            response_text = response.get("response", "")
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                
                return ContentAnalysis(
                    key_topics=result.get("key_topics", []),
                    sentiment=result.get("sentiment", "neutral"),
                    entities=result.get("entities", []),
                    language=result.get("language", "en"),
                    readability_score=result.get("readability_score", 0.5),
                    summary=result.get("summary", "")
                )
            else:
                return self._fallback_content_analysis(content)
                
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return self._fallback_content_analysis(content)
    
    def _fallback_content_analysis(self, content: str) -> ContentAnalysis:
        """Fallback content analysis."""
        content_lower = content.lower()
        
        # Simple sentiment analysis
        positive_words = ["good", "great", "excellent", "positive", "success", "profit"]
        negative_words = ["bad", "poor", "negative", "loss", "problem", "issue"]
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return ContentAnalysis(
            key_topics=["general"],
            sentiment=sentiment,
            entities=[],
            language="en",
            readability_score=0.5,
            summary="Fallback analysis"
        )
    
    async def extract_entities(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from content.
        
        Args:
            content: Document content
            
        Returns:
            List of extracted entities
        """
        truncated_content = content[:2000] if len(content) > 2000 else content
        
        prompt = f"""
        Extract named entities from this text. Return a JSON array:
        [
            {{"name": "entity_name", "type": "person|organization|location|date|amount", "value": "entity_value"}}
        ]
        
        Text:
        {truncated_content}
        
        Respond only with valid JSON array:
        """
        
        try:
            response = await self._make_request("generate", {
                "model": self.default_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 400
                }
            })
            
            response_text = response.get("response", "")
            json_start = response_text.find("[")
            json_end = response_text.rfind("]") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                return []
                
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []
    
    async def generate_summary(self, content: str, max_length: int = 200) -> str:
        """
        Generate a concise summary of the content.
        
        Args:
            content: Document content
            max_length: Maximum summary length
            
        Returns:
            Generated summary
        """
        truncated_content = content[:4000] if len(content) > 4000 else content
        
        prompt = f"""
        Generate a concise summary of this document in {max_length} characters or less:
        
        {truncated_content}
        
        Summary:
        """
        
        try:
            response = await self._make_request("generate", {
                "model": self.default_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": max_length + 50
                }
            })
            
            summary = response.get("response", "").strip()
            return summary[:max_length] if len(summary) > max_length else summary
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return "Summary generation failed"
    
    async def batch_classify(self, documents: List[Tuple[str, str]]) -> List[ClassificationResult]:
        """
        Classify multiple documents in batch.
        
        Args:
            documents: List of (content, file_extension) tuples
            
        Returns:
            List of classification results
        """
        tasks = []
        for content, file_extension in documents:
            task = self.classify_document(content, file_extension)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch classification failed for document {i}: {result}")
                # Use fallback classification
                content, file_extension = documents[i]
                processed_results.append(self._fallback_classification(content, file_extension))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available Ollama models."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("models", [])
                    else:
                        logger.error(f"Failed to get models: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []
    
    async def switch_model(self, model_name: str) -> bool:
        """
        Switch to a different model.
        
        Args:
            model_name: Name of the model to switch to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if model is available
            models = await self.get_available_models()
            model_names = [model["name"] for model in models]
            
            if model_name in model_names:
                self.default_model = model_name
                logger.info(f"Switched to model: {model_name}")
                return True
            else:
                logger.warning(f"Model {model_name} not available")
                return False
                
        except Exception as e:
            logger.error(f"Error switching model: {e}")
            return False
