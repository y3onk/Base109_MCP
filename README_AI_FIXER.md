# AI Code Vulnerability Fixer

This script uses OpenAI models to automatically fix security vulnerabilities in JavaScript/TypeScript code using predefined prompt templates.

## Features

- **Multiple Prompt Templates**: Applies all prompt files from the `prompts/` folder to each code file
- **Dual Input Modes**: 
  - GitHub repository mode (requires GITHUB_TOKEN)
  - Local folder mode (for testing with sample code)
- **Batch Processing**: Processes multiple files with multiple prompts
- **Structured Output**: Generates unique filenames for each prompt result

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
# Required
export OPENAI_API_KEY="your-openai-api-key"

# Optional (for GitHub mode)
export GITHUB_TOKEN="your-github-token"
export OPENAI_MODEL="gpt-4o-mini"  # default
```

## Usage

### Local Mode (Recommended for Testing)

Process JS/TS files from a local folder:
```bash
python mcp/fix_vulnerable_code.py --local ./sample_code --out ./fixed_output --max-files 10
```

### GitHub Mode

Process JS/TS files from a GitHub repository:
```bash
python mcp/fix_vulnerable_code.py --github owner repo branch folder --out ./fixed_output
```

### Options

- `--local FOLDER`: Use local folder instead of GitHub
- `--github OWNER REPO BRANCH FOLDER`: GitHub repository details
- `--model MODEL`: OpenAI model name (default: gpt-4o-mini)
- `--max-files N`: Maximum files to process (default: 50)
- `--out DIR`: Output directory (default: ./fixed_output)
- `--dry-run`: Don't write files, only show results

## Output Structure

### Files
- Each prompt generates a separate fixed file
- Filenames: `original_prompt_1.js`, `original_prompt_2.js`, etc.
- Files are saved in the output directory maintaining the original folder structure

### JSON Output
```json
{
  "source": "local",
  "local_folder": "/path/to/sample_code",
  "model": "gpt-4o-mini",
  "output_dir": "/path/to/fixed_output",
  "results": [
    {
      "path": "example.js",
      "prompt_results": [
        {
          "prompt_index": 1,
          "summary": "Fixed XSS vulnerability...",
          "findings": ["CWE-79: XSS", "CWE-89: SQL Injection"],
          "written": true,
          "prompt_preview": "You are an experienced security researcher..."
        }
      ]
    }
  ]
}
```

## Prompt Templates

The script automatically loads all `.txt` files from the `prompts/` folder:
- `fixed0.txt` - Basic security researcher prompt
- `fixed1.txt` - Vulnerability-focused prompt  
- `fixed2.txt` - CodeQL detection prompt
- `fixed3_1.txt` - Learning material prompt
- `fixed3_2.txt` - CWE-focused prompt

Each prompt is applied to every code file, providing multiple analysis perspectives.

## Example Workflow

1. **Test with local samples**:
```bash
python mcp/fix_vulnerable_code.py --local ./test_code --dry-run
```

2. **Process GitHub repository**:
```bash
python mcp/fix_vulnerable_code.py --github hvvup codeSec jwt database/jwt/fixed
```

3. **Custom model and output**:
```bash
python mcp/fix_vulnerable_code.py --local ./code --model gpt-4 --out ./secure_code --max-files 25
```

## Notes

- The script preserves original code functionality while fixing security issues
- Each prompt generates a different perspective on the same code
- Use `--dry-run` to test without writing files
- Check the JSON output for detailed results and any errors
