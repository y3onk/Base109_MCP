#!/usr/bin/env python3
"""
MCP Server for Security Code Analysis
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import logging
import re  # for JSON extraction / code block parsing

# --- MCP imports (with compatibility shims across SDK versions) ---
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Resource, Tool, TextContent
except ImportError:
    print("MCP package not found. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Optional/Version-dependent imports (graceful fallback)
try:
    from mcp.server.lowlevel import NotificationOptions  # newer pattern
except Exception:
    try:
        from mcp.server.models import NotificationOptions  # fallback
    except Exception:
        NotificationOptions = None  # final fallback

try:
    from mcp.server.models import InitializationOptions
except Exception:
    InitializationOptions = None  # final fallback for older SDKs

from dotenv import load_dotenv
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

@dataclass
class SecurityAnalysisResult:
    """Result of security analysis"""
    file_path: str
    vulnerability_type: str
    severity: str
    description: str
    fixed_code: str
    findings: List[str]
    prompt_used: str

@dataclass
class CodeFile:
    """Represents a code file"""
    path: str
    content: str
    language: str

class GitHubFetcher:
    """GitHub code fetcher tool"""

    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            logger.warning("GITHUB_TOKEN not set. GitHub functionality will be limited.")

    async def fetch_repo_files(self, owner: str, repo: str, branch: str, folder: str = "") -> List[CodeFile]:
        """Fetch JS/TS files from GitHub repository"""
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN is required for GitHub operations")

        import requests
        import base64
        import time

        headers = {"Authorization": f"token {self.github_token}"}
        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Check rate limit
            if 'X-RateLimit-Remaining' in response.headers:
                remaining = int(response.headers['X-RateLimit-Remaining'])
                if remaining < 10:
                    logger.warning(f"GitHub API rate limit low: {remaining} requests remaining")
            
            data = response.json()
        except requests.exceptions.Timeout:
            raise ValueError(f"GitHub API request timed out for {owner}/{repo}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"GitHub API request failed: {e}")
        except Exception as e:
            raise ValueError(f"Unexpected error fetching repository: {e}")

        files: List[CodeFile] = []
        for file_info in data.get("tree", []):
            if file_info.get("type") != "blob":
                continue

            file_path = file_info["path"]

            # Filter by folder and extension
            if folder and not file_path.startswith(folder.rstrip("/")):
                continue
            if not file_path.endswith((".js", ".ts")):
                continue

            try:
                # Get file content
                content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
                content_response = requests.get(content_url, headers=headers, timeout=30)
                content_response.raise_for_status()
                content_data = content_response.json()

                if "content" not in content_data:
                    logger.warning(f"No content found for {file_path}")
                    continue

                content = base64.b64decode(content_data["content"]).decode("utf-8", errors="ignore")

                files.append(CodeFile(
                    path=file_path,
                    content=content,
                    language="javascript" if file_path.endswith(".js") else "typescript"
                ))
                
                # Rate limiting: small delay between requests
                time.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"Failed to fetch content for {file_path}: {e}")
                continue

        logger.info(f"Successfully fetched {len(files)} files from {owner}/{repo}")
        return files

class LocalFileReader:
    """Local file reader tool"""

    async def read_local_files(self, folder_path: str) -> List[CodeFile]:
        """Read JS/TS files from local folder"""
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            raise ValueError(f"Folder not found: {folder_path}")

        files: List[CodeFile] = []
        for file_path in folder.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() in {".js", ".ts"}:
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    rel_path = str(file_path.relative_to(folder).as_posix())
                    files.append(CodeFile(
                        path=rel_path,
                        content=content,
                        language="javascript" if file_path.suffix.lower() == ".js" else "typescript"
                    ))
                except Exception as e:
                    logger.warning(f"Could not read file {file_path}: {e}")

        return files

class PromptLoader:
    """Prompt template loader"""

    def __init__(self, prompts_dir: str = None):
        if prompts_dir is None:
            # Default to prompts directory relative to this script
            script_dir = Path(__file__).resolve().parent
            prompts_dir = script_dir / "prompts"

        self.prompts_dir = Path(prompts_dir)
        self._prompts: Optional[List[Dict[str, str]]] = None
        logger.info(f"[PromptLoader] Using prompts dir: {self.prompts_dir}")

    async def load_prompts(self) -> List[Dict[str, str]]:
        """Load all prompt templates"""
        if self._prompts is not None:
            return self._prompts

        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {self.prompts_dir}")

        prompts: List[Dict[str, str]] = []
        for prompt_file in sorted(self.prompts_dir.glob("*.txt")):
            try:
                content = prompt_file.read_text(encoding="utf-8")
                prompts.append({
                    "name": prompt_file.stem,
                    "content": content,
                    "file": str(prompt_file)
                })
            except Exception as e:
                logger.warning(f"Could not read prompt file {prompt_file}: {e}")

        self._prompts = prompts
        return prompts

class SecurityAnalyzer:
    """AI-powered security analyzer"""

    def __init__(self, model: str = None):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.openai_client = OpenAI()

    async def analyze_code(self, code_file: CodeFile, prompt_template: str) -> SecurityAnalysisResult:
        """Analyze code for security vulnerabilities using AI"""

        # Fill prompt placeholders
        filled_prompt = prompt_template.replace("{CODE HERE}", code_file.content)
        filled_prompt = filled_prompt.replace("{}", code_file.content)
        filled_prompt = filled_prompt.replace("/index.js", code_file.path)

        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": filled_prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
                timeout=60,
            )
            content = response.choices[0].message.content or "{}"
        except Exception:
            # Fallback without response_format
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": filled_prompt},
                ],
                temperature=0.2,
                timeout=60,
            )
            content = response.choices[0].message.content or "{}"

        # Parse response
        try:
            result_data = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            json_match = re.search(r"(\{[\s\S]*\})", content)
            if json_match:
                try:
                    result_data = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    result_data = {}
            else:
                result_data = {}

        # Extract code blocks if no structured response
        fixed_code = result_data.get("fixed_code", "")
        if not fixed_code and content:
            code_blocks = re.findall(r"```(?:javascript|js|typescript|ts)?\s*([\s\S]*?)```", content)
            if code_blocks:
                fixed_code = code_blocks[0].strip()
            else:
                fixed_code = content.strip()

        return SecurityAnalysisResult(
            file_path=code_file.path,
            vulnerability_type=result_data.get("vulnerability_type", "Unknown"),
            severity=result_data.get("severity", "Medium"),
            description=result_data.get("summary", ""),
            fixed_code=fixed_code,
            findings=result_data.get("findings", []),
            prompt_used=prompt_template[:100] + "..." if len(prompt_template) > 100 else prompt_template
        )

class SecurityMCPServer:
    """Main MCP Server for Security Analysis"""

    def __init__(self):
        self.server = Server("security-analyzer")
        self.github_fetcher = GitHubFetcher()
        self.local_reader = LocalFileReader()
        self.prompt_loader = PromptLoader()
        self.security_analyzer = SecurityAnalyzer()

        # Register tools and resources
        self._register_tools()
        self._register_resources()

    def _register_tools(self):
        """Register MCP tools"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="fetch_github_code",
                    description="Fetch JavaScript/TypeScript files from a GitHub repository",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "owner": {"type": "string", "description": "GitHub repository owner"},
                            "repo": {"type": "string", "description": "GitHub repository name"},
                            "branch": {"type": "string", "description": "Branch name (default: main)"},
                            "folder": {"type": "string", "description": "Folder path to filter files (optional)"}
                        },
                        "required": ["owner", "repo"]
                    }
                ),
                Tool(
                    name="read_local_files",
                    description="Read JavaScript/TypeScript files from a local directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "folder_path": {"type": "string", "description": "Path to local directory"}
                        },
                        "required": ["folder_path"]
                    }
                ),
                Tool(
                    name="load_prompts",
                    description="Load security analysis prompt templates",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prompts_dir": {"type": "string", "description": "Path to prompts directory (optional)"}
                        }
                    }
                ),
                Tool(
                    name="analyze_security",
                    description="Analyze code for security vulnerabilities using AI",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to the code file"},
                            "content": {"type": "string", "description": "Code content to analyze"},
                            "language": {"type": "string", "description": "Programming language (javascript/typescript)"},
                            "prompt_name": {"type": "string", "description": "Name of the prompt template to use"}
                        },
                        "required": ["file_path", "content", "language", "prompt_name"]
                    }
                ),
                Tool(
                    name="batch_analyze",
                    description="Analyze multiple files with multiple prompts",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_type": {"type": "string", "enum": ["github", "local"], "description": "Source type"},
                            "github_params": {
                                "type": "object",
                                "properties": {
                                    "owner": {"type": "string"},
                                    "repo": {"type": "string"},
                                    "branch": {"type": "string"},
                                    "folder": {"type": "string"}
                                }
                            },
                            "local_path": {"type": "string", "description": "Local folder path"},
                            "max_files": {"type": "integer", "description": "Maximum files to process", "default": 10}
                        },
                        "required": ["source_type"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "fetch_github_code":
                    owner = arguments["owner"]
                    repo = arguments["repo"]
                    branch = arguments.get("branch", "main")
                    folder = arguments.get("folder", "")

                    files = await self.github_fetcher.fetch_repo_files(owner, repo, branch, folder)
                    result = {
                        "files_found": len(files),
                        "files": [asdict(f) for f in files]
                    }
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]

                elif name == "read_local_files":
                    folder_path = arguments["folder_path"]
                    files = await self.local_reader.read_local_files(folder_path)
                    result = {
                        "files_found": len(files),
                        "files": [asdict(f) for f in files]
                    }
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]

                elif name == "load_prompts":
                    prompts_dir = arguments.get("prompts_dir")
                    if prompts_dir:
                        self.prompt_loader = PromptLoader(prompts_dir)

                    prompts = await self.prompt_loader.load_prompts()
                    result = {
                        "prompts_loaded": len(prompts),
                        "prompts": prompts
                    }
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]

                elif name == "analyze_security":
                    file_path = arguments["file_path"]
                    content = arguments["content"]
                    language = arguments["language"]
                    prompt_name = arguments["prompt_name"]

                    # Load prompts to find the requested one
                    prompts = await self.prompt_loader.load_prompts()
                    prompt_template = None
                    for prompt in prompts:
                        if prompt["name"] == prompt_name:
                            prompt_template = prompt["content"]
                            break

                    if not prompt_template:
                        return [TextContent(type="text", text=f"Prompt '{prompt_name}' not found")]

                    # Create code file object
                    code_file = CodeFile(path=file_path, content=content, language=language)

                    # Analyze
                    result = await self.security_analyzer.analyze_code(code_file, prompt_template)
                    return [TextContent(type="text", text=json.dumps(asdict(result), indent=2))]

                elif name == "batch_analyze":
                    source_type = arguments["source_type"]
                    max_files = arguments.get("max_files", 10)

                    # Get files
                    if source_type == "github":
                        github_params = arguments["github_params"]
                        files = await self.github_fetcher.fetch_repo_files(
                            github_params["owner"],
                            github_params["repo"],
                            github_params.get("branch", "main"),
                            github_params.get("folder", "")
                        )
                    else:  # local
                        local_path = arguments["local_path"]
                        files = await self.local_reader.read_local_files(local_path)

                    # Load prompts
                    prompts = await self.prompt_loader.load_prompts()

                    # Analyze files
                    results = []
                    for i, code_file in enumerate(files[:max_files]):
                        file_results = []
                        for prompt in prompts:
                            try:
                                analysis = await self.security_analyzer.analyze_code(
                                    code_file, prompt["content"]
                                )
                                file_results.append(asdict(analysis))
                            except Exception as e:
                                file_results.append({
                                    "error": str(e),
                                    "prompt_name": prompt["name"]
                                })

                        results.append({
                            "file_path": code_file.path,
                            "analyses": file_results
                        })

                    return [TextContent(type="text", text=json.dumps(results, indent=2))]

                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]

            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    def _register_resources(self):
        """Register MCP resources"""

        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            return [
                Resource(
                    uri="prompts://templates",
                    name="Security Analysis Prompts",
                    description="Available security analysis prompt templates",
                    mimeType="application/json"
                ),
                Resource(
                    uri="config://server",
                    name="Server Configuration",
                    description="MCP server configuration and status",
                    mimeType="application/json"
                )
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            if uri == "prompts://templates":
                prompts = await self.prompt_loader.load_prompts()
                return json.dumps(prompts, indent=2)
            elif uri == "config://server":
                config = {
                    "server_name": "security-analyzer",
                    "version": "1.0.0",
                    "tools_available": [
                        "fetch_github_code",
                        "read_local_files",
                        "load_prompts",
                        "analyze_security",
                        "batch_analyze"
                    ],
                    "github_configured": bool(os.getenv("GITHUB_TOKEN")),
                    "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
                    "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                }
                return json.dumps(config, indent=2)
            else:
                raise ValueError(f"Unknown resource: {uri}")

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            # Build capabilities with compatibility across SDK versions
            try:
                if NotificationOptions is not None:
                    capabilities = self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                else:
                    capabilities = self.server.get_capabilities()  # type: ignore
            except TypeError:
                capabilities = self.server.get_capabilities()  # type: ignore

            # Initialization options (if supported by SDK)
            init_opts = None
            if InitializationOptions:
                try:
                    init_opts = InitializationOptions(
                        client_name="security-analyzer-client",
                        client_version="1.0.0"
                    )
                except Exception:
                    init_opts = None  # older SDKs

            # Newer SDKs: run(read, write, capabilities=..., initialization_options=?)
            # Older SDKs: run(read, write, capabilities=...)
            try:
                await self.server.run(
                    read_stream,
                    write_stream,
                    capabilities=capabilities,
                    initialization_options=init_opts,  # type: ignore[call-arg]
                )
            except TypeError:
                await self.server.run(
                    read_stream,
                    write_stream,
                    capabilities=capabilities,
                )

def validate_environment():
    """Validate required environment variables"""
    missing_vars = []
    
    if not os.getenv("OPENAI_API_KEY"):
        missing_vars.append("OPENAI_API_KEY")
    
    if not os.getenv("GITHUB_TOKEN"):
        missing_vars.append("GITHUB_TOKEN")
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your .env file or environment")
        return False
    
    logger.info("✅ All required environment variables are set")
    return True

async def main():
    """Main entry point"""
    # Validate environment variables
    if not validate_environment():
        logger.warning("⚠️ Some environment variables are missing. Some functionality may be limited.")
    
    try:
        server = SecurityMCPServer()
        logger.info("🚀 Starting MCP Security Analysis Server...")
        await server.run()
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
