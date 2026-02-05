const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const app = express();
const PORT = 4000;
const SCREENSHOTS_DIR = '/sdcard/Pictures/Screenshots';

app.use(cors());
app.use(express.json());
app.use(express.static('public'));
app.use('/images', express.static(SCREENSHOTS_DIR));

// Helper to run Python bridge
// ... [helper code stays same] ...

app.get('/api/stats', async (req, res) => {
// ... [stats code stays same] ...
});

app.get('/api/dashboard', async (req, res) => {
// ... [dashboard code stays same] ...
});

app.get('/api/search', async (req, res) => {
// ... [search code stays same] ...
});

app.get('/api/category/:name', async (req, res) => {
// ... [category code stays same] ...
});

app.post('/api/move-file', async (req, res) => {
    try {
        const { filename, newCategory } = req.body;
        if (!filename || !newCategory) {
            return res.status(400).json({ error: 'Missing filename or newCategory' });
        }
        
        const result = await runBridge('move_file', [filename, newCategory]);
        if (result.error) {
            return res.status(500).json(result);
        }
        res.json(result);
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: e.toString() });
    }
});

if (require.main === module) {
    app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
}

module.exports = app;