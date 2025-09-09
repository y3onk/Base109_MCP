const express = require('express');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const bodyParser = require('body-parser');
const { body, validationResult } = require('express-validator');
const app = express();

app.use(helmet());
app.use(bodyParser.json({ limit: '10kb' }));

const limiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 100,
    standardHeaders: true,
    legacyHeaders: false,
});

app.use(limiter);

function filterByAction(lines, action) {
    const pattern = new RegExp(`\\b${action}\\b`, 'i');
    const result = [];
    for (const line of lines) {
        if (typeof line !== 'string' || line.length > 1000) {
            continue;
        }
        if (pattern.test(line)) {
            result.push(line);
            if (result.length >= 1000) {
                break;
            }
        }
    }
    return result;
}

app.post('/filterAction',
    body('action').isString().isLength({ min: 1, max: 100 }),
    body('logs').isArray({ min: 1, max: 10000 }),
    (req, res) => {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({ errors: errors.array() });
        }

        const { action, logs } = req.body;
        try {
            const filtered = filterByAction(logs, action);
            res.json({ matches: filtered });
        } catch (err) {
            res.status(500).json({ error: 'Internal server error' });
        }
    }
);

app.use((err, req, res, next) => {
    res.status(500).json({ error: 'Something went wrong' });
});

const port = process.env.PORT || 3000;
app.listen(port, () => {});
