const express = require("express");
const { spawn } = require("child_process");
const path = require("path");
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });
const app = express();

app.use(express.json());

app.post("/fetch-code", (req, res) => {
  const { owner, repo, branch, folder } = req.body;

  // 절대 경로로 Python 스크립트 지정
 const scriptPath = path.resolve(__dirname, "../mcp/get_github_file.py");

  // 환경변수 포함해서 실행 (GITHUB_TOKEN 전달 필요)
  const env = { ...process.env, PYTHONIOENCODING: 'utf-8' };
  const pythonProcess = spawn("python", [scriptPath, owner, repo, branch, folder], { env });



  let dataBuffer = "";

  pythonProcess.stdout.on("data", (data) => {
    dataBuffer += data.toString();
  });

  pythonProcess.stderr.on("data", (data) => {
    console.error(`stderr: ${data.toString()}`);
  });

  pythonProcess.on("close", (code) => {
    if (code !== 0) {
      return res.status(500).json({ error: "Python MCP 실패" });
    }
    try {
      const result = JSON.parse(dataBuffer);
      res.json(result);
    } catch (err) {
      res.status(500).json({ error: "파싱 실패", details: err.message });
    }
  });
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
