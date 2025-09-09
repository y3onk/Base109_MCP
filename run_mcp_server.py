#!/usr/bin/env python3
"""
Simple runner script for MCP Security Analysis Server
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server import main

if __name__ == "__main__":
    print("🚀 Starting MCP Security Analysis Server...")
    print("📡 Server will run on stdio (stdin/stdout)")
    print("💡 Use mcp_client.py to interact with this server")
    print("🔧 Press Ctrl+C to stop the server\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

