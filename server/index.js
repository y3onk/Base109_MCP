const express = require("express");
const { spawn } = require("child_process");
const app = express();

app.use(express.json());

app.post("/fetch-code", (req, res) => {
  const { owner, repo } = req.body;

  const pythonProcess = spawn("python3", [
    "./mcp/github_code_fetcher.py",
    owner,
    repo,
  ]);

  let dataBuffer = "";

  pythonProcess.stdout.on("data", (data) => {
    dataBuffer += data.toString();
  });

  pythonProcess.stderr.on("data", (data) => {
    console.error(`stderr: ${data}`);
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
