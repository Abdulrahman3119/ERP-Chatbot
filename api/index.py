"""Serverless function handler for FastAPI app.
Compatible with Vercel and other serverless platforms."""
import os
import sys
import json
import traceback

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Try to import and initialize the app
try:
    from app.api.main import app
    from mangum import Mangum
    
    # Create handler - Vercel expects this at module level
    handler = Mangum(app, lifespan="off")
    
except Exception as e:
    # If initialization fails, create a handler that returns the error
    # This helps debug what's going wrong
    error_msg = str(e)
    error_type = type(e).__name__
    error_traceback = traceback.format_exc()
    
    def error_handler(event, context):
        """Error handler that shows what went wrong during initialization."""
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Initialization Error",
                "message": error_msg,
                "type": error_type,
                "traceback": error_traceback,
                "help": "Check Vercel logs for more details. Common issues: missing dependencies, import errors, or environment variables."
            }, indent=2)
        }
    
    handler = error_handler

