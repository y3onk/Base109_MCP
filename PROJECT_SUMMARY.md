# MCP Security Analysis Project

## 📋 **프로젝트 구조**

```
Base109_MCP/
├── mcp_server.py              # MCP 서버 (핵심)
├── mcp_client.py              # MCP 클라이언트 데모
├── fix_vulnerable_code_mcp.py # 백워드 호환 래퍼
├── run_mcp_server.py          # 서버 실행 스크립트
├── simple_test.py             # 기본 테스트
├── test_mcp.py                # 종합 테스트
├── requirements.txt           # 의존성
├── mcp_config.json            # MCP 설정
├── README.md                  # 사용법
├── MIGRATION_GUIDE.md         # 마이그레이션 가이드
├── prompts/                   # 5개 보안 분석 프롬프트
└── samples/                   # 6개 취약 코드 샘플
```

## 🚀 **빠른 시작**

1. **의존성 설치**:
   ```bash
   pip install -r requirements.txt
   ```

2. **환경 변수 설정**:
   ```bash
   set OPENAI_API_KEY=your-api-key
   ```

3. **테스트 실행**:
   ```bash
   python simple_test.py
   ```

4. **MCP 클라이언트 데모**:
   ```bash
   python mcp_client.py
   ```

5. **백워드 호환 (기존 API 스타일)**:
   ```bash
   python fix_vulnerable_code_mcp.py --local ./samples
   ```

## 🛠️ **MCP 도구들**

- `fetch_github_code` - GitHub 코드 가져오기
- `read_local_files` - 로컬 파일 읽기  
- `load_prompts` - 프롬프트 템플릿 로드
- `analyze_security` - AI 보안 분석
- `batch_analyze` - 배치 분석

## 🎯 **주요 성과**

✅ **AI API → MCP 변환 완료**  
✅ **5개 보안 분석 도구 구현**  
✅ **표준화된 MCP 프로토콜 적용**  
✅ **완전한 백워드 호환성**  
✅ **포괄적 테스트 스위트**  

## 📊 **완성도: 90%**

- 서버 아키텍처: ✅ 완료
- 도구 구현: ✅ 완료  
- 문서화: ✅ 완료
- 테스트: ✅ 완료
- 클라이언트 연결: ⚠️ 개선 필요
