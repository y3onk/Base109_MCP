import requests
from typing import List, Dict
import os
import base64
from dotenv import load_dotenv
import sys
import json
import traceback


# .env 파일 로드
load_dotenv()

GITHUB_API_BASE = "https://api.github.com"

# 환경변수에서 토큰 가져오기 (없으면 종료)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("❌ GITHUB_TOKEN이 설정되지 않았습니다. .env 파일에 GITHUB_TOKEN을 추가하세요.")
    sys.exit(1)

def get_repo_file_list(owner: str, repo: str, branch: str, token: str) -> List[Dict]:
    """브랜치의 전체 파일 목록 가져오기"""
    headers = {"Authorization": f"token {token}"}
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return [file for file in data.get("tree", []) if file.get("type") == "blob"]

def get_file_content(owner: str, repo: str, target_path: str, branch: str, token: str) -> str:
    """특정 브랜치의 특정 파일 원본 코드 가져오기"""
    headers = {"Authorization": f"token {token}"}
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{target_path}?ref={branch}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    content = response.json()

    if "content" not in content:
        return ""
    return base64.b64decode(content["content"]).decode("utf-8", errors="ignore")

def fetch_repo_code_files(owner: str, repo: str, branch: str, target_path: str, token: str) -> List[Dict[str, str]]:
    """특정 브랜치와 폴더의 모든 JS/TS 파일 가져오기"""
    files = get_repo_file_list(owner, repo, branch, token)

    result = []
    for file in files:
        # 폴더 필터: target_path가 폴더 경로임
        if target_path and not file["path"].startswith(target_path.rstrip("/")):
            continue
        # 확장자 필터 (필요시 확장자 추가 가능)
        if not file["path"].endswith((".js", ".ts")):
            continue

        try:
            content = get_file_content(owner, repo, file["path"], branch, token)
            result.append({"path": file["path"], "content": content})
        except Exception as e:
            print(f"Failed to fetch {file['path']}: {e}", file=sys.stderr)
    return result


if __name__ == "__main__":
    try:
        if len(sys.argv) < 5:
            print("사용법: python get_github_file.py <owner> <repo> <branch> <target_path> [--folder]")
            sys.exit(1)

        owner = sys.argv[1]
        repo = sys.argv[2]
        branch = sys.argv[3]
        target_path = sys.argv[4]  # 폴더명 또는 파일경로

        is_folder_mode = len(sys.argv) > 5 and sys.argv[5] == "--folder"

        if is_folder_mode:
            code_files = fetch_repo_code_files(owner, repo, branch, target_path, GITHUB_TOKEN)
            for code_file in code_files:
                print(json.dumps(code_file, ensure_ascii=False))
        else:
            content = get_file_content(owner, repo, target_path, branch, GITHUB_TOKEN)
            print(json.dumps({"path": target_path, "content": content}, indent=2, ensure_ascii=False))

    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
