"""NIVA AI Platform - Unified Runner.

Starts the FastAPI server serving both the backend API and the responsive web UI.
Access URL: http://localhost:8000
"""

import sys
import os
import uvicorn

if __name__ == "__main__":
    # Add backend directory to sys.path
    backend_path = os.path.join(os.path.dirname(__file__), "backend")
    sys.path.insert(0, backend_path)

    print("=" * 60)
    print(" NIVA AI - Natural Intelligent Virtual Agent")
    print(" Complete Modular AI Assistant Platform")
    print("=" * 60)
    print(" * Local Web Interface:  http://localhost:8000")
    print(" * API Health Endpoint:  http://localhost:8000/health")
    print(" * API Documentation:    http://localhost:8000/docs")
    print(" * Supabase Backend:     Connected (https://gmklwdzpbntixhvbvfcl.supabase.co)")
    print(" * Private Storage:      niva-files (50MB RLS isolated)")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
