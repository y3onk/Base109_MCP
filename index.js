const express = require("express");
const { spawn } = require("child_process");
const path = require("path");
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });
const app = express();

app.use(express.json());

app.post("/fetch-code", (req, res) => {
  const { owner, repo, branch, folder, filePath } = req.body;

  const scriptPath = path.resolve(__dirname, "../mcp/get_github_file.py");
  const env = { ...process.env, PYTHONIOENCODING: 'utf-8' };

  const args = [scriptPath, owner, repo, branch];

  if (filePath) {
    args.push(filePath);
  } else if (folder) {
    args.push(folder, "--folder");
  } else {
    return res.status(400).json({ error: "filePath 또는 folder 중 하나는 필수입니다." });
  }

  res.setHeader("Content-Type", "application/json; charset=utf-8");
  // 배열형 JSON으로 묶어서 보낼 경우 아래처럼
  // res.write('[');

  const pythonProcess = spawn("python", args, { env });

  let buffer = "";

  pythonProcess.stdout.on("data", (data) => {
    buffer += data.toString();

    // 라인 단위로 자르기
    let lines = buffer.split("\n");
    // 마지막 라인은 아직 완전하지 않을 수 있으니 남겨두기
    buffer = lines.pop();

    for (const line of lines) {
      if (line.trim().length === 0) continue;
      try {
        const jsonObj = JSON.parse(line);
        // jsonObj 가공 가능
        // 예) console.log(jsonObj);

        // 클라이언트에 보내기
        // 만약 배열로 묶지 않고 스트리밍으로 하나씩 JSON 보내려면 개별 JSON.stringify 후 전송
        res.write(JSON.stringify(jsonObj) + "\n");
      } catch (e) {
        console.error("JSON parse error:", e);
        console.error("Line:", line);
      }
    }
  });

  pythonProcess.stderr.on("data", (data) => {
    console.error(`stderr: ${data.toString()}`);
  });

  pythonProcess.on("close", (code) => {
    if (buffer.trim().length > 0) {
      try {
        const jsonObj = JSON.parse(buffer);
        res.write(JSON.stringify(jsonObj) + "\n");
      } catch (e) {
        console.error("Final JSON parse error:", e);
      }
    }

    if (code !== 0) {
      if (!res.headersSent) {
        res.status(500).json({ error: "Python MCP 실패" });
      } else {
        res.end();
      }
      return;
    }
    res.end();
  });
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
