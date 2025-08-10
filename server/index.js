const express = require("express");
const { spawn } = require("child_process");
const path = require("path");
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });
const app = express();

app.use(express.json());

app.post("/fetch-code", (req, res) => {
  const { owner, repo, branch, folder, filePath } = req.body;

  // 절대 경로로 Python 스크립트 지정
  const scriptPath = path.resolve(__dirname, "../mcp/get_github_file.py");
  // 환경변수 포함해서 실행 (GITHUB_TOKEN 전달 필요)
  const env = { ...process.env, PYTHONIOENCODING: 'utf-8' };

  const args = [scriptPath, owner, repo, branch];

  if (filePath) {
    args.push(filePath);
  } else if (folder) {
    args.push(folder, "--folder"); //폴더 내 여러파일 요청
  } else {
    return res.status(400).json({ error: "filePath 또는 folder 중 하나는 필수입니다." });
  }

  res.setHeader("Content-Type", "application/x-ndjson; charset=utf-8");

  const pythonProcess = spawn("python", args, { env });

  pythonProcess.stdout.on("data", (data) => {
    // 폴더 요청 시 여러 JSON 객체가 한 줄씩 출력됨 -> 그대로 클라이언트에 스트리밍
    res.write(data);
  });

  pythonProcess.stderr.on("data", (data) => {
    console.error(`stderr: ${data.toString()}`);
  });

  pythonProcess.on("close", (code) => {
    if (code !== 0) {
      if (!res.headersSent) {
        res.status(500).json({ error: "Python MCP 실패" });
      } else {
        // 이미 일부 데이터가 전송되었으면 그냥 연결 종료
        res.end();
      }
      return;
    }
    res.end(); // 모든 데이터 전송 후 연결 종료
  });
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
