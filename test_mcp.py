#!/usr/bin/env python3
"""
Test script for MCP Security Analysis Server
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp_client import SecurityMCPClient, SecurityAnalysisWorkflow

async def test_mcp_server():
    """Test the MCP server functionality"""
    print("🧪 Testing MCP Security Analysis Server\n")
    
    # Check environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set. Please set it in your environment or .env file.")
        return False
    
    print("✅ Environment variables check passed")
    
    client = SecurityMCPClient()
    
    try:
        # Connect to server
        print("🔌 Connecting to MCP server...")
        await client.connect()
        print("✅ Connected successfully")
        
        # Test 1: List tools
        print("\n📋 Testing tool listing...")
        tools = await client.list_tools()
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        
        # Test 2: Load prompts
        print("\n📝 Testing prompt loading...")
        prompts_result = await client.load_prompts()
        print(f"✅ Loaded {prompts_result['prompts_loaded']} prompts:")
        for prompt in prompts_result['prompts']:
            print(f"  - {prompt['name']}")
        
        # Test 3: Read local files (if samples exist)
        samples_dir = Path(__file__).parent / "samples"
        if samples_dir.exists():
            print(f"\n📁 Testing local file reading from {samples_dir}...")
            files_result = await client.read_local_files(str(samples_dir))
            print(f"✅ Found {files_result['files_found']} files:")
            for file_info in files_result['files'][:3]:  # Show first 3
                print(f"  - {file_info['path']} ({file_info['language']})")
        
        # Test 4: Single file analysis (if we have files and prompts)
        if samples_dir.exists() and prompts_result['prompts']:
            print(f"\n🔍 Testing single file analysis...")
            sample_files = files_result['files']
            if sample_files:
                sample_file = sample_files[0]
                prompt_name = prompts_result['prompts'][0]['name']
                
                print(f"  Analyzing: {sample_file['path']}")
                print(f"  Using prompt: {prompt_name}")
                
                analysis = await client.analyze_security(
                    sample_file['path'],
                    sample_file['content'],
                    sample_file['language'],
                    prompt_name
                )
                
                print(f"✅ Analysis complete:")
                print(f"  - Vulnerability type: {analysis.get('vulnerability_type', 'Unknown')}")
                print(f"  - Severity: {analysis.get('severity', 'Unknown')}")
                print(f"  - Findings: {len(analysis.get('findings', []))}")
                print(f"  - Fixed code length: {len(analysis.get('fixed_code', ''))}")
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await client.disconnect()
        print("🔌 Disconnected from server")

async def test_workflow():
    """Test the high-level workflow"""
    print("\n🔄 Testing Security Analysis Workflow\n")
    
    client = SecurityMCPClient()
    workflow = SecurityAnalysisWorkflow(client)
    
    try:
        await client.connect()
        
        # Test local folder analysis
        samples_dir = Path(__file__).parent / "samples"
        if samples_dir.exists():
            print(f"📁 Testing workflow with local folder: {samples_dir}")
            results = await workflow.analyze_local_folder(str(samples_dir), max_files=2)
            
            print(f"✅ Workflow completed:")
            print(f"  - Files analyzed: {results['files_analyzed']}")
            print(f"  - Prompts used: {results['prompts_used']}")
            
            # Save results
            output_file = "test_workflow_results.json"
            await workflow.save_results(results, output_file)
            print(f"  - Results saved to: {output_file}")
        
        print("\n🎉 Workflow test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await client.disconnect()

async def main():
    """Main test function"""
    print("🚀 MCP Security Analysis Server Test Suite\n")
    
    # Test basic functionality
    basic_test_passed = await test_mcp_server()
    
    if basic_test_passed:
        # Test workflow
        workflow_test_passed = await test_workflow()
        
        if workflow_test_passed:
            print("\n🎊 All tests passed! MCP server is working correctly.")
            return 0
        else:
            print("\n⚠️ Basic tests passed but workflow test failed.")
            return 1
    else:
        print("\n💥 Basic tests failed. Please check your setup.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

