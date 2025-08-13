#!/usr/bin/env python3
"""
Test script to verify prompt loading and placeholder filling logic.
Run this to test the core functionality without requiring OpenAI API.
"""

import sys
from pathlib import Path

# Add the current directory to Python path to import functions
sys.path.insert(0, str(Path(__file__).parent))

def test_prompt_loading():
    """Test loading prompts from the prompts folder."""
    try:
        # Test the prompt loading logic directly
        script_dir = Path(__file__).resolve().parent
        prompts_dir = script_dir.parent.parent / "prompts"
        
        print(f"Looking for prompts in: {prompts_dir}")
        
        if not prompts_dir.exists():
            print(f"❌ Prompts directory not found: {prompts_dir}")
            return False
        
        prompts = []
        for prompt_file in sorted(prompts_dir.glob("*.txt")):
            try:
                content = prompt_file.read_text(encoding="utf-8")
                prompts.append(content)
                print(f"✅ Loaded: {prompt_file.name}")
            except Exception as e:
                print(f"❌ Could not read {prompt_file}: {e}")
        
        if not prompts:
            print("❌ No prompt files found")
            return False
        
        print(f"\n✅ Successfully loaded {len(prompts)} prompts:")
        
        for i, prompt in enumerate(prompts, 1):
            print(f"  {i}. Length: {len(prompt)} chars")
            print(f"     Preview: {prompt[:100]}...")
            print()
        
        # Test placeholder filling logic
        print("Testing placeholder filling...")
        sample_code = "console.log('Hello World');"
        sample_file = "test.js"
        
        for i, prompt in enumerate(prompts, 1):
            # Basic placeholder replacement
            filled = prompt.replace("{CODE HERE}", sample_code)
            filled = filled.replace("{}", sample_code)
            filled = filled.replace("/server.js", sample_file)
            
            print(f"  Prompt {i}: {len(filled)} chars after filling")
            if "{CODE HERE}" in prompt or "{}" in prompt:
                print(f"    ✅ Placeholders replaced")
            else:
                print(f"    ℹ️  No placeholders found")
        
        print("\n✅ All tests passed! The script is ready to use.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_prompt_loading()
    sys.exit(0 if success else 1)
