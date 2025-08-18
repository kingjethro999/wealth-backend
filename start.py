#!/usr/bin/env python3
"""
Startup script for the Wealth Investment API backend
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    print("Starting Wealth Investment API...")
    print("MongoDB URL:", os.getenv("MONGODB_URL", "Not set"))
    print("Database:", os.getenv("DATABASE_NAME", "wealthinvest"))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
