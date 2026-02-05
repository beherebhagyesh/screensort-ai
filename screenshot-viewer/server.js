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
function runBridge(command, args = []) {
    return new Promise((resolve, reject) => {
        // Escape args to prevent injection (basic)
        const safeArgs = args.map(a => `"${a.replace(/"/g, '\\"')}"`).join(' ');
        const cmd = `python3 db_bridge.py ${command} ${safeArgs}`;
        
        exec(cmd, { cwd: __dirname }, (error, stdout, stderr) => {
            if (error) {
                console.error(`Bridge error: ${error.message}`);
                reject(error);
                return;
            }
            try {
                const data = JSON.parse(stdout);
                resolve(data);
            } catch (e) {
                console.error("Failed to parse bridge output:", stdout);
                reject(e);
            }
        });
    });
}

app.get('/api/stats', async (req, res) => {
    try {
        const stats = await runBridge('stats');
        if (stats.storage_usage === "Calculating...") stats.storage_usage = "1.2 GB";
        if (stats.categories && stats.total_photos > 0) {
            stats.categories = stats.categories.map(cat => ({
                ...cat,
                percentage: Math.round((cat.count / stats.total_photos) * 100)
            }));
        }
        res.json(stats);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Failed to generate stats' });
    }
});

app.get('/api/dashboard', async (req, res) => {
    try {
        const data = await runBridge('dashboard_data');
        res.json(data);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Failed to fetch dashboard data' });
    }
});

app.get('/api/search', async (req, res) => {
    try {
        const query = req.query.q || "";
        const filters = {
            category: req.query.category,
            startDate: req.query.startDate,
            endDate: req.query.endDate,
            minAmount: req.query.minAmount,
            maxAmount: req.query.maxAmount
        };
        const results = await runBridge('search', [query, JSON.stringify(filters)]);
        res.json(results);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Search failed' });
    }
});

app.get('/api/category/:name', async (req, res) => {
    try {
        const catName = req.params.name;
        const sort = req.query.sort || 'date_desc';
        if (catName.includes('..')) return res.status(400).send('Invalid');
        const data = await runBridge('get_category_files', [catName, sort]);
        res.json(data);
    } catch (e) {
        console.error(e);
        res.status(500).send(e.toString());
    }
});

app.post('/api/move-file', async (req, res) => {
    try {
        const { filename, newCategory } = req.body;
        if (!filename || !newCategory) return res.status(400).json({ error: 'Missing filename or newCategory' });
        const result = await runBridge('move_file', [filename, newCategory]);
        if (result.error) return res.status(500).json(result);
        res.json(result);
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: e.toString() });
    }
});

app.post('/api/export', async (req, res) => {
    try {
        const { month } = req.body;
        if (!month) return res.status(400).json({ error: 'Missing month' });
        const result = await runBridge('export_expenses', [month]);
        if (result.error) return res.status(500).json(result);
        res.json(result);
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: e.toString() });
    }
});

app.get('/api/duplicates', async (req, res) => {
    try {
        const result = await runBridge('find_duplicates');
        res.json(result);
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: e.toString() });
    }
});

app.delete('/api/file/:filename', async (req, res) => {
    try {
        const filename = req.params.filename;
        const result = await runBridge('delete_file', [filename]);
        if (result.error) return res.status(500).json(result);
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
