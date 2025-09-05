#!/usr/bin/env python3
"""
Backward compatible wrapper using MCP architecture
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from mcp_client import SecurityMCPClient, SecurityAnalysisWorkflow

def convert_old_to_new_args(args) -> dict:
    """Convert old argument format to new MCP format"""
    if args.github:
        owner, repo, branch, folder = args.github
        return {
            "source_type": "github",
            "github_params": {
                "owner": owner,
                "repo": repo,
                "branch": branch,
                "folder": folder
            }
        }
    else:  # local
        return {
            "source_type": "local",
            "local_path": args.local
        }

async def run_mcp_analysis(args) -> dict:
    """Run analysis using MCP architecture"""
    client = SecurityMCPClient()
    workflow = SecurityAnalysisWorkflow(client)
    
    try:
        await client.connect()
        
        # Convert arguments
        mcp_args = convert_old_to_new_args(args)
        
        if mcp_args["source_type"] == "github":
            github_params = mcp_args["github_params"]
            results = await workflow.analyze_repository(
                github_params["owner"],
                github_params["repo"],
                github_params.get("branch", "main"),
                github_params.get("folder", ""),
                args.max_files
            )
        else:  # local
            results = await workflow.analyze_local_folder(
                mcp_args["local_path"],
                args.max_files
            )
        
        return results
        
    finally:
        await client.disconnect()

def save_results_old_format(results: dict, output_dir: str, dry_run: bool = False):
    """Save results in the old format for backward compatibility"""
    if dry_run:
        return
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Convert MCP results to old format
    old_format_results = {
        "source": "mcp",
        "model": "gpt-4o-mini",  # Default model
        "output_dir": str(output_path),
        "results": []
    }
    
    # Add source-specific metadata
    if "repository" in results:
        old_format_results.update({
            "source": "github",
            "owner": results["repository"].split("/")[0],
            "repo": results["repository"].split("/")[1],
            "branch": results.get("branch", "main"),
            "folder": results.get("folder", "")
        })
    else:
        old_format_results.update({
            "source": "local",
            "local_folder": results.get("folder", "")
        })
    
    # Convert file results
    for file_result in results.get("results", []):
        file_path = file_result["file_path"]
        analyses = file_result.get("analyses", [])
        
        prompt_results = []
        for i, analysis in enumerate(analyses):
            if "error" in analysis:
                prompt_results.append({
                    "prompt_index": i + 1,
                    "error": analysis["error"],
                    "prompt_preview": analysis.get("prompt_name", f"prompt_{i+1}")
                })
            else:
                # Save fixed code file
                if analysis.get("fixed_code"):
                    prompt_suffix = f"_prompt_{i+1}"
                    base_name = Path(file_path)
                    new_name = f"{base_name.stem}{prompt_suffix}{base_name.suffix}"
                    new_path = base_name.parent / new_name
                    out_path = output_path / new_path
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_text(analysis["fixed_code"], encoding="utf-8")
                
                prompt_results.append({
                    "prompt_index": i + 1,
                    "summary": analysis.get("description", ""),
                    "findings": analysis.get("findings", []),
                    "written": bool(analysis.get("fixed_code")),
                    "prompt_preview": analysis.get("prompt_used", f"prompt_{i+1}")
                })
        
        old_format_results["results"].append({
            "path": file_path,
            "prompt_results": prompt_results
        })
    
    # Save JSON summary
    json_path = output_path / "analysis_summary.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(old_format_results, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to {output_path}", file=sys.stderr)
    print(f"JSON summary saved to {json_path}", file=sys.stderr)

def main(argv: Optional[List[str]] = None) -> int:
    """Main function with backward compatibility"""
    parser = argparse.ArgumentParser(description="Fix vulnerable JS/TS code using MCP architecture.")
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

    # Run MCP analysis
    try:
        results = asyncio.run(run_mcp_analysis(args))
        
        # Save results in old format for compatibility
        save_results_old_format(results, args.out, args.dry_run)
        
        # Print JSON output (old format)
        old_format = {
            "source": "mcp",
            "model": args.model,
            "output_dir": args.out,
            "results": []
        }
        
        # Add source-specific metadata
        if args.github:
            owner, repo, branch, folder = args.github
            old_format.update({
                "source": "github",
                "owner": owner,
                "repo": repo,
                "branch": branch,
                "folder": folder
            })
        else:
            old_format.update({
                "source": "local",
                "local_folder": str(Path(args.local).resolve())
            })
        
        # Convert results
        for file_result in results.get("results", []):
            file_path = file_result["file_path"]
            analyses = file_result.get("analyses", [])
            
            prompt_results = []
            for i, analysis in enumerate(analyses):
                if "error" in analysis:
                    prompt_results.append({
                        "prompt_index": i + 1,
                        "error": analysis["error"],
                        "prompt_preview": analysis.get("prompt_name", f"prompt_{i+1}")
                    })
                else:
                    prompt_results.append({
                        "prompt_index": i + 1,
                        "summary": analysis.get("description", ""),
                        "findings": analysis.get("findings", []),
                        "written": (not args.dry_run),
                        "prompt_preview": analysis.get("prompt_used", f"prompt_{i+1}")
                    })
            
            old_format["results"].append({
                "path": file_path,
                "prompt_results": prompt_results
            })
        
        print(json.dumps(old_format, ensure_ascii=False, indent=2))
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())

