const express = require('express');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const bodyParser = require('body-parser');
const { body, validationResult } = require('express-validator');
const { JSDOM } = require('jsdom');
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

function stripTag(html, tag) {
    const regex = new RegExp(`<${tag}[^>]*>.*?<\\/${tag}>`, 'gis');
    return html.replace(regex, '');
}

app.post('/stripTag',
    body('text').isString().isLength({ min: 1, max: 100000 }),
    body('tag').isString().isLength({ min: 1, max: 30 }),
    (req, res) => {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({ errors: errors.array() });
        }

        const { text, tag } = req.body;
        try {
            const sanitizedHtml = stripTag(text, tag);
            res.json({ result: sanitizedHtml });
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
