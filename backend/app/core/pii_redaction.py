from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import re
import json


class PIIRedactionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to redact Personally Identifiable Information (PII)
    before data is sent to external LLM APIs.
    
    This is critical for data sovereignty compliance.
    """
    
    # Regex patterns for PII detection
    PATTERNS = {
        "phone": re.compile(r'\+?254\d{9}|\b0\d{9}\b'),  # Kenyan phone numbers
        "id_number": re.compile(r'\b\d{8}\b'),  # 8-digit ID numbers
        "maisha_namba": re.compile(r'\b\d{14}\b'),  # 14-digit Maisha Namba
        "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    }
    
    REPLACEMENTS = {
        "phone": "[PHONE]",
        "id_number": "[ID]",
        "maisha_namba": "[NAMBA]",
        "email": "[EMAIL]",
    }
    
    async def dispatch(self, request: Request, call_next):
        """Process request and response"""
        # Only apply to LLM-bound requests (chat endpoints)
        if "/chat" in request.url.path:
            # Read request body
            body = await request.body()
            
            try:
                data = json.loads(body)
                
                # Redact PII from text fields
                if "text" in data:
                    data["text"] = self.redact_pii(data["text"])
                
                # Create new request with redacted data
                from starlette.datastructures import Headers
                headers = Headers(scope=request.scope)
                
                request._body = json.dumps(data).encode()
                
            except json.JSONDecodeError:
                pass  # Not JSON, skip
        
        response = await call_next(request)
        return response
    
    def redact_pii(self, text: str) -> str:
        """
        Redact PII from text using regex patterns.
        
        Args:
            text: Input text potentially containing PII
        
        Returns:
            Text with PII replaced by placeholders
        """
        redacted = text
        
        for pii_type, pattern in self.PATTERNS.items():
            replacement = self.REPLACEMENTS[pii_type]
            redacted = pattern.sub(replacement, redacted)
        
        return redacted
