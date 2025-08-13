import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv


def load_env() -> None:
    """Load environment variables from a .env located at the project root if present."""
    # Search parent directories for a .env similar to the Node server behavior
    script_dir = Path(__file__).resolve().parent
    candidates: List[Path] = [
        script_dir / ".env",
        script_dir.parent / ".env",
        script_dir.parent.parent / ".env",
    ]
    for env_path in candidates:
        if env_path.exists():
            load_dotenv(dotenv_path=str(env_path))
            break


def resolve_python_executable() -> str:
    """Resolve a Python executable cross-platform without user interaction."""
    candidate_env = os.getenv("PYTHON_EXECUTABLE")
    if candidate_env:
        return candidate_env
    # Prefer 'python' which is available on most systems; fall back to 'py -3' on Windows via cmd
    if os.name == "nt":
        return "python"
    return "python"


def run_fetcher(owner: str, repo: str, branch: str, folder: str) -> List[Dict[str, str]]:
    """Invoke the existing get_github_file.py as a subprocess and parse its JSON output."""
    script_path = Path(__file__).resolve().parent / "get_github_file.py"
    if not script_path.exists():
        raise FileNotFoundError(f"Fetcher script not found: {script_path}")

    python_exec = resolve_python_executable()
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")

    proc = subprocess.run(
        [python_exec, str(script_path), owner, repo, branch, folder],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    if proc.returncode != 0:
        stderr = proc.stderr.strip()
        raise RuntimeError(f"Fetcher failed (exit {proc.returncode}): {stderr}")

    stdout = proc.stdout.strip()
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse fetcher output as JSON: {exc}\nOutput:\n{stdout[:2000]}")

    if not isinstance(data, list):
        raise ValueError("Fetcher output is not a list")
    # Each entry: {"path": str, "content": str}
    return data


# ---- Prompt Loading and Management ----

def load_prompts() -> List[str]:
    """Load all prompt files from the prompts folder."""
    script_dir = Path(__file__).resolve().parent
    prompts_dir = script_dir.parent.parent / "prompts"
    
    if not prompts_dir.exists():
        raise FileNotFoundError(f"Prompts directory not found: {prompts_dir}")
    
    prompts = []
    for prompt_file in sorted(prompts_dir.glob("*.txt")):
        try:
            content = prompt_file.read_text(encoding="utf-8")
            prompts.append(content)
        except Exception as e:
            print(f"Warning: Could not read prompt file {prompt_file}: {e}", file=sys.stderr)
    
    if not prompts:
        raise RuntimeError("No prompt files found in prompts directory")
    
    return prompts


def fill_prompt_placeholders(prompt: str, file_path: str, code: str, 
                           cwe_info: Optional[Dict[str, str]] = None) -> str:
    """Fill prompt placeholders with actual values."""
    # Basic placeholders that we can fill
    filled = prompt.replace("{CODE HERE}", code)
    filled = filled.replace("{}", code)  # For prompts that use {} as placeholder
    
    # Fill file path placeholders
    filled = filled.replace("/server.js", file_path)
    
    # Fill CWE information if provided
    if cwe_info:
        for key, value in cwe_info.items():
            placeholder = f"{{{key}}}"
            filled = filled.replace(placeholder, str(value))
    
    return filled


# ---- OpenAI Client (minimal, dependency on `openai` >= 1.x) ----

@dataclass
class AIResult:
    fixed_code: str
    summary: str
    findings: List[str]
    prompt_used: str


class OpenAIClient:
    def __init__(self, model: str) -> None:
        try:
            from openai import OpenAI  # type: ignore
        except Exception as import_err:  # pragma: no cover
            raise RuntimeError(
                "The 'openai' package is required. Install with: pip install openai"
            ) from import_err

        self._OpenAI = OpenAI
        self._client = OpenAI()
        self._model = model

    def analyze_and_fix_with_prompt(self, file_path: str, code: str, prompt: str) -> AIResult:
        """Analyze and fix code using a specific prompt template."""
        # Fill the prompt with actual code and file information
        filled_prompt = fill_prompt_placeholders(prompt, file_path, code)
        
        # Extract the actual code content from the filled prompt for analysis
        # The prompt might contain instructions, so we need to identify where the code is
        if "{CODE HERE}" in prompt or "{}" in prompt:
            # The prompt template has placeholders, so the filled prompt should work
            user_content = filled_prompt
        else:
            # No placeholders, append the code at the end
            user_content = f"{prompt}\n\n{code}"
        
        # Use JSON mode if available; otherwise fallback to plain content parsing
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
                timeout=60,  # 60초 타임아웃 추가
            )
            content = response.choices[0].message.content or "{}"
        except Exception:
            # Fallback without response_format
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,
                timeout=60,  # 60초 타임아웃 추가
            )
            content = response.choices[0].message.content or "{}"

        payload = _coerce_json(content)
        fixed_code = str(payload.get("fixed_code", ""))
        summary = str(payload.get("summary", ""))
        findings_raw = payload.get("findings", [])
        findings = [str(item) for item in findings_raw] if isinstance(findings_raw, list) else []
        
        # If no structured response, try to extract code from the response
        if not fixed_code and content:
            # Try to extract code blocks from the response
            code_blocks = re.findall(r"```(?:javascript|js|typescript|ts)?\s*([\s\S]*?)```", content)
            if code_blocks:
                fixed_code = code_blocks[0].strip()
            else:
                # If no code blocks, use the entire response as fixed code
                fixed_code = content.strip()
        
        return AIResult(
            fixed_code=fixed_code, 
            summary=summary, 
            findings=findings,
            prompt_used=prompt[:100] + "..." if len(prompt) > 100 else prompt
        )


def _coerce_json(text: str) -> Dict[str, Any]:
    """Parse text to JSON. If it includes code fences, extract the JSON block."""
    text = text.strip()
    # Remove common code-fence wrappers
    fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", text, re.IGNORECASE)
    if fence_match:
        text = fence_match.group(1).strip()
    try:
        return json.loads(text)
    except Exception:
        # Last resort: extract the first JSON object
        obj_match = re.search(r"(\{[\s\S]*\})", text)
        if obj_match:
            try:
                return json.loads(obj_match.group(1))
            except Exception:
                pass
        return {}


def build_output(root: Path) -> List[Dict[str, str]]:
    """Read local JS/TS files and return in the same format as GitHub fetcher."""
    results: List[Dict[str, str]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".js", ".ts"}:
            try:
                # Use UTF-8 and ignore decoding errors to mirror GitHub API behavior
                content = path.read_text(encoding="utf-8", errors="ignore")
                # Convert to relative path format
                rel_path = str(path.relative_to(root).as_posix())
                results.append({
                    "path": rel_path,
                    "content": content,
                })
            except Exception as e:
                print(f"Warning: Could not read file {path}: {e}", file=sys.stderr)
    return results


def ensure_output_path(base_dir: Path, file_path: str) -> Path:
    target = base_dir / file_path
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def main(argv: Optional[List[str]] = None) -> int:
    load_env()

    parser = argparse.ArgumentParser(description="Fix vulnerable JS/TS code using an AI model.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--github", nargs=4, metavar=("OWNER", "REPO", "BRANCH", "FOLDER"), 
                      help="GitHub: owner repo branch folder")
    group.add_argument("--local", metavar="FOLDER", help="Local folder containing JS/TS files")
    
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), help="OpenAI model name")
    parser.add_argument("--max-files", type=int, default=50, help="Max number of files to process")
    parser.add_argument("--out", default=str(Path.cwd() / "fixed_output"), help="Output directory for fixed files")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files, only print JSON summary")
    args = parser.parse_args(argv)

    # Validate API keys early
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set. Please add it to your .env or environment.", file=sys.stderr)
        return 2

    # Get files either from GitHub or local folder
    if args.github:
        owner, repo, branch, folder = args.github
        if not os.getenv("GITHUB_TOKEN"):
            print("GITHUB_TOKEN is not set. Required for GitHub mode.", file=sys.stderr)
            return 2
        try:
            files = run_fetcher(owner, repo, branch, folder)
        except Exception as fetch_err:
            print(f"Failed to fetch files from GitHub: {fetch_err}", file=sys.stderr)
            return 1
    else:  # Local mode
        local_folder = Path(args.local).resolve()
        if not local_folder.exists() or not local_folder.is_dir():
            print(f"Local folder not found or not a directory: {local_folder}", file=sys.stderr)
            return 1
        try:
            files = build_output(local_folder)
        except Exception as local_err:
            print(f"Failed to read local files: {local_err}", file=sys.stderr)
            return 1

    if not files:
        print(json.dumps({"results": [], "message": "No files matched."}, ensure_ascii=False))
        return 0

    # Load all prompts
    try:
        prompts = load_prompts()
        print(f"Loaded {len(prompts)} prompt templates", file=sys.stderr)
    except Exception as prompt_err:
        print(f"Failed to load prompts: {prompt_err}", file=sys.stderr)
        return 1

    ai = OpenAIClient(model=args.model)
    output_dir = Path(args.out).resolve()
    results: List[Dict[str, Any]] = []

    processed = 0
    for entry in files:
        if processed >= args.max_files:
            break
        file_path = entry.get("path", "")
        content = entry.get("content", "")
        if not file_path or not content:
            continue
        
        print(f"Processing file {processed + 1}/{min(len(files), args.max_files)}: {file_path}", file=sys.stderr)
        
        file_results = []
        # Apply each prompt to this file
        for i, prompt in enumerate(prompts):
            print(f"  Applying prompt {i + 1}/{len(prompts)}...", file=sys.stderr)
            try:
                ai_result = ai.analyze_and_fix_with_prompt(file_path, content, prompt)
                if ai_result.fixed_code:
                    if not args.dry_run:
                        # Create unique filename for each prompt
                        prompt_suffix = f"_prompt_{i+1}"
                        base_name = Path(file_path)
                        new_name = f"{base_name.stem}{prompt_suffix}{base_name.suffix}"
                        new_path = base_name.parent / new_name
                        out_path = ensure_output_path(output_dir, str(new_path))
                        out_path.write_text(ai_result.fixed_code, encoding="utf-8")
                
                file_results.append({
                    "prompt_index": i + 1,
                    "summary": ai_result.summary,
                    "findings": ai_result.findings,
                    "written": (not args.dry_run),
                    "prompt_preview": ai_result.prompt_used,
                })
            except Exception as ai_err:
                file_results.append({
                    "prompt_index": i + 1,
                    "error": str(ai_err),
                    "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                })
        
        results.append({
            "path": file_path,
            "prompt_results": file_results,
        })
        processed += 1

    # Prepare output metadata
    output_meta = {
        "model": args.model,
        "output_dir": str(output_dir),
        "results": results,
    }
    
    if args.github:
        owner, repo, branch, folder = args.github
        output_meta.update({
            "source": "github",
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "folder": folder,
        })
    else:
        output_meta.update({
            "source": "local",
            "local_folder": str(Path(args.local).resolve()),
        })
    
    print(json.dumps(output_meta, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())


