const express = require('express');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const bodyParser = require('body-parser');
const { body, validationResult } = require('express-validator');
const escapeHtml = require('escape-html');
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

function highlightText(text, query) {
    const regex = new RegExp(query, 'gi');
    const escapedText = escapeHtml(text);
    return escapedText.replace(regex, (match) => `<mark>${escapeHtml(match)}</mark>`);
}

app.post('/highlight',
    body('text').isString().isLength({ min: 1, max: 10000 }),
    body('query').isString().isLength({ min: 1, max: 100 }),
    (req, res) => {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({ errors: errors.array() });
        }
        const { text, query } = req.body;
        try {
            const highlighted = highlightText(text, query);
            res.json({ result: highlighted });
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
