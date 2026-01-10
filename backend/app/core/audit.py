from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware for audit logging.
    Tracks all state-changing operations for government accountability.
    """
    
    # Endpoints that trigger audit logs
    AUDITED_ENDPOINTS = [
        "/verify/upload",
        "/verify/status",
        "/admin/verifications",
        "/auth/login",
        "/auth/verify",
    ]
    
    async def dispatch(self, request: Request, call_next):
        """Log audit trail for critical operations"""
        
        path = request.url.path
        should_audit = any(endpoint in path for endpoint in self.AUDITED_ENDPOINTS)
        
        if should_audit and request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            # Extract user info from token (if available)
            auth_header = request.headers.get("Authorization", "")
            user_id = "anonymous"
            
            if auth_header.startswith("Bearer "):
                from app.core.security import get_token_data
                token = auth_header.replace("Bearer ", "")
                token_data = get_token_data(token)
                if token_data:
                    user_id = token_data.user_id
            
            # Log the action (in production, this would write to AuditLog table)
            logger.info(
                f"AUDIT: user={user_id} action={request.method} "
                f"endpoint={path} ip={request.client.host} "
                f"timestamp={datetime.utcnow().isoformat()}"
            )
        
        response = await call_next(request)
        return response


async def log_audit_event(
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    old_value: dict = None,
    new_value: dict = None,
    ip_address: str = None
):
    """
    Create an immutable audit log entry.
    
    This function would write to the AuditLog database table.
    For now, it logs to the application logger.
    """
    from app.database import AsyncSessionLocal
    from app.models.audit import AuditLog
    
    async with AsyncSessionLocal() as session:
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )
        
        session.add(audit_entry)
        await session.commit()
        
        logger.info(
            f"AUDIT_LOG: {action} on {entity_type}:{entity_id} by user {user_id}"
        )
