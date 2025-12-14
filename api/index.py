"""Serverless function handler for FastAPI app.
Compatible with Vercel and other serverless platforms."""
import os
import sys
import json
import traceback
from typing import Any, Dict

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Lazy initialization - only create handler when needed
_mangum_handler = None
_init_error = None
_init_traceback = None


def _create_handler():
    """Create Mangum handler lazily."""
    global _mangum_handler, _init_error, _init_traceback
    
    if _mangum_handler is not None:
        return _mangum_handler
    
    if _init_error is not None:
        raise _init_error
    
    try:
        from app.api.main import app
        from mangum import Mangum
        
        # Create handler with proper configuration
        _mangum_handler = Mangum(
            app,
            lifespan="off"  # Disable lifespan events for serverless
        )
        return _mangum_handler
        
    except Exception as e:
        _init_error = e
        _init_traceback = traceback.format_exc()
        raise


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler function for Vercel serverless functions.
    
    Args:
        event: Event dictionary from Vercel
        context: Context object (not used but required by Vercel)
    
    Returns:
        Response dictionary with statusCode, headers, and body
    """
    try:
        # Lazy initialization - create handler on first request
        mangum_handler = _create_handler()
        
        # Call Mangum handler
        response = mangum_handler(event, context)
        
        # Ensure response is in correct format
        if isinstance(response, dict):
            return response
        else:
            # If Mangum returns something unexpected, wrap it
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(response) if not isinstance(response, str) else response
            }
            
    except Exception as e:
        # Handle initialization errors
        if _init_error is not None:
            error_info = {
                "error": "Initialization Error",
                "message": str(_init_error),
                "type": type(_init_error).__name__,
            }
            # Include traceback in non-production
            if os.getenv("VERCEL_ENV") != "production":
                error_info["traceback"] = _init_traceback
            error_info["help"] = (
                "Check Vercel logs for more details. "
                "Common issues: missing dependencies, import errors, or environment variables."
            )
        else:
            # Handle runtime errors
            error_info = {
                "error": "Runtime Error",
                "message": str(e),
                "type": type(e).__name__,
            }
            if os.getenv("VERCEL_ENV") != "production":
                error_info["traceback"] = traceback.format_exc()
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(error_info, indent=2)
        }

