const express = require('express');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const bodyParser = require('body-parser');
const { body, validationResult } = require('express-validator');
const app = express();

app.use(helmet());
app.use(bodyParser.json({ limit: '1kb' }));

const limiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 100,
    standardHeaders: true,
    legacyHeaders: false,
});

app.use(limiter);

function isValidLogText(text) {
    return typeof text === 'string' && text.length > 0 && text.length <= 10000;
}

function vulnerableExtractUserIdEntries(userId, logText) {
    const pattern = new RegExp(`userId=${userId}\\b`, 'g');
    const matches = [];
    let match;
    while ((match = pattern.exec(logText)) !== null) {
        matches.push(match[0]);
        if (matches.length > 1000) {
            break;
        }
    }
    return matches;
}

app.post('/searchLogin',
    body('userId').isString().isLength({ min: 1, max: 100 }),
    body('logText').custom(isValidLogText),
    (req, res) => {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({ errors: errors.array() });
        }

        const { userId, logText } = req.body;
        try {
            const results = vulnerableExtractUserIdEntries(userId, logText);
            res.json({ matches: results });
        } catch (err) {
            res.status(500).json({ error: err.message });
        }
    }
);

app.use((err, req, res, next) => {
    res.status(500).json({ error: 'Something went wrong' });
});

const port = process.env.PORT || 3000;
app.listen(port, () => {});
