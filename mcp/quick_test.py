#!/usr/bin/env python3
"""
간단한 OpenAI API 연결 테스트
"""

import os
import sys
from pathlib import Path

def test_openai_connection():
    """OpenAI API 연결 테스트"""
    try:
        from openai import OpenAI
        
        # API 키 확인
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
            return False
        
        print(f"✅ API 키 확인됨: {api_key[:10]}...")
        
        # 클라이언트 생성
        client = OpenAI()
        
        # 간단한 요청 테스트
        print("🔄 OpenAI API 연결 테스트 중...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello, say 'test successful' in Korean"}],
            max_tokens=50,
            timeout=30
        )
        
        result = response.choices[0].message.content
        print(f"✅ API 응답 성공: {result}")
        return True
        
    except ImportError:
        print("❌ openai 패키지가 설치되지 않았습니다.")
        print("pip install openai 명령으로 설치하세요.")
        return False
    except Exception as e:
        print(f"❌ API 연결 실패: {e}")
        return False

def test_prompt_loading():
    """프롬프트 로딩 테스트"""
    try:
        script_dir = Path(__file__).resolve().parent
        prompts_dir = script_dir.parent.parent / "prompts"
        
        if not prompts_dir.exists():
            print(f"❌ 프롬프트 폴더를 찾을 수 없습니다: {prompts_dir}")
            return False
        
        prompts = list(prompts_dir.glob("*.txt"))
        print(f"✅ {len(prompts)}개의 프롬프트 파일 발견")
        
        for prompt_file in prompts:
            size = prompt_file.stat().st_size
            print(f"  - {prompt_file.name}: {size} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ 프롬프트 로딩 실패: {e}")
        return False

def main():
    print("🚀 OpenAI API 및 프롬프트 로딩 테스트 시작\n")
    
    # 1. OpenAI API 테스트
    print("1️⃣ OpenAI API 연결 테스트")
    api_ok = test_openai_connection()
    print()
    
    # 2. 프롬프트 로딩 테스트
    print("2️⃣ 프롬프트 로딩 테스트")
    prompt_ok = test_prompt_loading()
    print()
    
    # 결과 요약
    if api_ok and prompt_ok:
        print("🎉 모든 테스트 통과! 메인 스크립트를 실행할 수 있습니다.")
        print("\n실행 명령:")
        print("python fix_vulnerable_code.py --local ../samples --max-files 1 --dry-run")
        return 0
    else:
        print("❌ 일부 테스트 실패. 위의 오류를 확인하세요.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
