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

function parseKeyValue(input, key) {
    const pattern = new RegExp(`${key}=([^\\s]+)`, 'g');
    const match = pattern.exec(input);
    if (match) {
        return match[1];
    } else {
        return null;
    }
}

app.post('/parse',
    body('key').isString().isLength({ min: 1, max: 50 }),
    body('input').isString().isLength({ min: 1, max: 10000 }),
    (req, res) => {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({ errors: errors.array() });
        }

        const { key, input } = req.body;
        try {
            const value = parseKeyValue(input, key);
            if (value !== null) {
                res.json({ value: value });
            } else {
                res.status(404).json({ error: 'Key not found' });
            }
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
