// Vulnerable Express.js server example
const express = require('express');
const app = express();

app.use(express.json());

// Vulnerable endpoint - SQL injection
app.post('/users', (req, res) => {
    const { name, email } = req.body;
    
    // VULNERABLE: Direct string concatenation in SQL query
    const query = `INSERT INTO users (name, email) VALUES ('${name}', '${email}')`;
    
    // Execute query (simulated)
    console.log('Executing query:', query);
    res.json({ message: 'User created', query });
});

// Vulnerable endpoint - XSS
app.get('/search', (req, res) => {
    const { q } = req.query;
    
    // VULNERABLE: Direct output without escaping
    const html = `
        <html>
            <body>
                <h1>Search Results</h1>
                <p>You searched for: ${q}</p>
            </body>
        </html>
    `;
    
    res.send(html);
});

// Vulnerable endpoint - Command injection
app.post('/ping', (req, res) => {
    const { host } = req.body;
    
    // VULNERABLE: Direct command execution
    const { exec } = require('child_process');
    exec(`ping ${host}`, (error, stdout, stderr) => {
        res.json({ output: stdout, error: stderr });
    });
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
