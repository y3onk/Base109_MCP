#!/usr/bin/env python3
"""
Basic MCP functionality tests
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import mcp
        print("✅ MCP package imported successfully")
    except ImportError as e:
        print(f"❌ MCP package import failed: {e}")
        return False
    
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        print("✅ MCP server modules imported successfully")
    except ImportError as e:
        print(f"❌ MCP server modules import failed: {e}")
        return False
    
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp import stdio_client
        print("✅ MCP client modules imported successfully")
    except ImportError as e:
        print(f"❌ MCP client modules import failed: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ dotenv imported successfully")
    except ImportError as e:
        print(f"❌ dotenv import failed: {e}")
        return False
    
    try:
        from openai import OpenAI
        print("✅ OpenAI imported successfully")
    except ImportError as e:
        print(f"❌ OpenAI import failed: {e}")
        return False
    
    return True

def test_server_creation():
    """Test if MCP server can be created"""
    print("\n🏗️ Testing server creation...")
    
    try:
        from mcp.server import Server
        from mcp.server.models import InitializationOptions
        
        server = Server("security-analyzer")
        print("✅ MCP server created successfully")
        
        # Test capabilities
        capabilities = server.get_capabilities(
            notification_options=None,
            experimental_capabilities={}
        )
        print("✅ Server capabilities retrieved successfully")
        
        return True
    except Exception as e:
        print(f"❌ Server creation failed: {e}")
        return False

def test_tool_registration():
    """Test if tools can be registered"""
    print("\n🔧 Testing tool registration...")
    
    try:
        from mcp.server import Server
        from mcp.types import Tool
        
        server = Server("test-server")
        
        # Test tool registration
        @server.list_tools()
        async def list_tools():
            return [
                Tool(
                    name="test_tool",
                    description="Test tool",
                    inputSchema={"type": "object"}
                )
            ]
        
        print("✅ Tool registration successful")
        return True
    except Exception as e:
        print(f"❌ Tool registration failed: {e}")
        return False

def test_prompt_loading():
    """Test if prompts can be loaded"""
    print("\n📝 Testing prompt loading...")
    
    try:
        prompts_dir = Path(__file__).parent / "prompts"
        if prompts_dir.exists():
            prompt_files = list(prompts_dir.glob("*.txt"))
            print(f"✅ Found {len(prompt_files)} prompt files:")
            for prompt_file in prompt_files:
                print(f"  - {prompt_file.name}")
            return True
        else:
            print(f"❌ Prompts directory not found: {prompts_dir}")
            return False
    except Exception as e:
        print(f"❌ Prompt loading failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 MCP Server Simple Test Suite\n")
    
    tests = [
        test_imports,
        test_server_creation,
        test_tool_registration,
        test_prompt_loading
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MCP server is ready to use.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
