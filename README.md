# 🔒 MCP Security Analysis Server

GitHub에서 JavaScript/TypeScript 파일을 가져와서 AI를 통해 보안 취약점을 분석하고 수정하는 MCP(Model Context Protocol) 서버입니다.

## 🚀 주요 기능

- **GitHub 코드 가져오기**: GitHub 저장소에서 JS/TS 파일 자동 수집
- **로컬 파일 분석**: 로컬 디렉토리의 코드 파일 분석
- **AI 보안 분석**: OpenAI GPT를 활용한 취약점 탐지 및 수정
- **배치 처리**: 여러 파일과 프롬프트를 동시에 처리
- **MCP 프로토콜**: 표준화된 AI 도구 인터페이스

## 📋 요구사항

- Python 3.8+
- OpenAI API 키
- GitHub 토큰 (선택사항)

## 🛠️ 설치

1. **저장소 클론**
   ```bash
   git clone <repository-url>
   cd Base109_MCP
   ```

2. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

3. **환경변수 설정**
   ```bash
   # .env 파일 생성
   echo "OPENAI_API_KEY=your-openai-api-key" > .env
   echo "GITHUB_TOKEN=your-github-token" >> .env
   echo "OPENAI_MODEL=gpt-4o-mini" >> .env
   ```

## 🎯 사용법

### 1. MCP 서버 실행

```bash
python mcp_server.py
```

### 2. MCP 클라이언트 데모

```bash
python mcp_client.py
```

### 3. 백워드 호환 스크립트

```bash
# 로컬 폴더 분석
python fix_vulnerable_code_mcp.py --local ./samples

# GitHub 저장소 분석
python fix_vulnerable_code_mcp.py --github owner repo main src
```

### 4. 단일 파일 가져오기

```bash
python get1file.py owner repo branch filepath
```

## 🛠️ MCP 도구들

### `fetch_github_code`
GitHub 저장소에서 JavaScript/TypeScript 파일을 가져옵니다.

**매개변수:**
- `owner`: GitHub 저장소 소유자
- `repo`: 저장소 이름
- `branch`: 브랜치 이름 (기본값: main)
- `folder`: 필터링할 폴더 경로 (선택사항)

### `read_local_files`
로컬 디렉토리에서 JS/TS 파일을 읽습니다.

**매개변수:**
- `folder_path`: 로컬 디렉토리 경로

### `load_prompts`
보안 분석 프롬프트 템플릿을 로드합니다.

**매개변수:**
- `prompts_dir`: 프롬프트 디렉토리 경로 (선택사항)

### `analyze_security`
AI를 사용하여 코드의 보안 취약점을 분석합니다.

**매개변수:**
- `file_path`: 파일 경로
- `content`: 코드 내용
- `language`: 프로그래밍 언어 (javascript/typescript)
- `prompt_name`: 사용할 프롬프트 템플릿 이름

### `batch_analyze`
여러 파일을 여러 프롬프트로 배치 분석합니다.

**매개변수:**
- `source_type`: 소스 타입 (github/local)
- `github_params`: GitHub 매개변수 (선택사항)
- `local_path`: 로컬 경로 (선택사항)
- `max_files`: 처리할 최대 파일 수 (기본값: 10)

## 📁 프로젝트 구조

```
Base109_MCP/
├── mcp_server.py              # MCP 서버 (핵심)
├── mcp_client.py              # MCP 클라이언트 데모
├── get1file.py                # GitHub 파일 가져오기 스크립트
├── fix_vulnerable_code_mcp.py # 백워드 호환 래퍼
├── run_mcp_server.py          # 서버 실행 스크립트
├── test_mcp.py                # 테스트 스크립트
├── requirements.txt           # Python 의존성
├── mcp.json                   # MCP 설정 파일
├── prompts/                   # 보안 분석 프롬프트
│   ├── fixed0.txt
│   ├── fixed1.txt
│   └── ...
└── samples/                   # 취약한 코드 샘플
    ├── cg_vul_1.js
    ├── cg_vul_2.js
    └── ...
```

## 🔧 설정

### MCP 클라이언트 설정

`mcp.json` 파일을 MCP 클라이언트 설정에 추가하세요:

```json
{
  "mcpServers": {
    "security-analyzer": {
      "command": "python",
      "args": ["./mcp_server.py"],
      "cwd": ".",
      "env": {
        "OPENAI_API_KEY": "${env:OPENAI_API_KEY}",
        "GITHUB_TOKEN": "${env:GITHUB_TOKEN}",
        "OPENAI_MODEL": "${env:OPENAI_MODEL}"
      }
    }
  }
}
```

## 🧪 테스트

```bash
# 기본 테스트
python simple_test.py

# 종합 테스트
python test_mcp.py
```

## 📊 보안 분석 프롬프트

프로젝트에는 5개의 보안 분석 프롬프트가 포함되어 있습니다:

1. **fixed0.txt**: 일반적인 보안 취약점 분석
2. **fixed1.txt**: SQL 인젝션 탐지
3. **fixed2.txt**: XSS 취약점 분석
4. **fixed3_1.txt**: 입력 검증 문제
5. **fixed3_2.txt**: 출력 인코딩 문제

## 🚨 문제 해결

### 환경변수 오류
```
❌ Missing required environment variables: OPENAI_API_KEY, GITHUB_TOKEN
```
**해결방법**: `.env` 파일에 필요한 환경변수를 설정하세요.

### GitHub API 제한
```
⚠️ GitHub API rate limit low: 5 requests remaining
```
**해결방법**: GitHub 토큰을 설정하거나 잠시 기다린 후 다시 시도하세요.

### MCP 연결 실패
```
❌ MCP client connection failed
```
**해결방법**: MCP SDK가 올바르게 설치되었는지 확인하세요.



