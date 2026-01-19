const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const app = express();
const PORT = 4000;
const SCREENSHOTS_DIR = '/sdcard/Pictures/Screenshots';

app.use(cors());
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
        
        // Enrich stats with percentage if needed (can be done in JS or Python)
        // Let's just pass it through for now
        
        // Add hardcoded storage usage if Python didn't calculate it
        if (stats.storage_usage === "Calculating...") {
             stats.storage_usage = "1.2 GB"; // Placeholder
        }
        
        // Calculate percentages for UI
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

app.get('/api/search', async (req, res) => {
    try {
        const query = req.query.q;
        if (!query) return res.json([]);
        
        const results = await runBridge('search', [query]);
        res.json(results);
    } catch (error) {
        res.status(500).json({ error: 'Search failed' });
    }
});

app.get('/api/category/:name', (req, res) => {
    try {
        const catName = req.params.name;
        if (catName.includes('..')) return res.status(400).send('Invalid');
        
        const dir = path.join(SCREENSHOTS_DIR, catName);
        if (!fs.existsSync(dir)) return res.status(404).send('Not found');

        const files = fs.readdirSync(dir)
            .filter(f => !f.startsWith('.'))
            .map(f => ({
                name: f,
                time: fs.statSync(path.join(dir, f)).mtime.getTime()
            }))
            .sort((a, b) => b.time - a.time) // Newest first
            .map(f => f.name);

        res.json({ files });
    } catch (e) {
        res.status(500).send(e.toString());
    }
});

if (require.main === module) {
    app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
}

module.exports = app;

app.get('/api/category/:name', (req, res) => {
    try {
        const catName = req.params.name;
        if (catName.includes('..')) return res.status(400).send('Invalid');
        
        const dir = path.join(SCREENSHOTS_DIR, catName);
        if (!fs.existsSync(dir)) return res.status(404).send('Not found');

        const files = fs.readdirSync(dir)
            .filter(f => !f.startsWith('.'))
            .map(f => ({
                name: f,
                time: fs.statSync(path.join(dir, f)).mtime.getTime()
            }))
            .sort((a, b) => b.time - a.time) // Newest first
            .map(f => f.name);

        res.json({ files });
    } catch (e) {
        res.status(500).send(e.toString());
    }
});

if (require.main === module) {
    app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
}

module.exports = app;