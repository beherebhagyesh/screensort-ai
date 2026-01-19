const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 4000;
const SCREENSHOTS_DIR = '/sdcard/Pictures/Screenshots';

app.use(cors());
app.use(express.static('public'));
app.use('/images', express.static(SCREENSHOTS_DIR));

// Helper to get all stats
function getStats() {
    let totalFiles = 0;
    let totalSize = 0;
    let categories = [];
    
    // Recent files for "Insights"
    let recentFiles = [];

    const items = fs.readdirSync(SCREENSHOTS_DIR, { withFileTypes: true });

    items.forEach(item => {
        if (item.isDirectory()) {
            const catPath = path.join(SCREENSHOTS_DIR, item.name);
            try {
                const files = fs.readdirSync(catPath).filter(f => {
                    const ext = f.toLowerCase();
                    return ext.endsWith('.jpg') || ext.endsWith('.png') || ext.endsWith('.jpeg') || ext.endsWith('.mp4');
                });
                
                if (files.length > 0) {
                    let catSize = 0;
                    files.forEach(f => {
                        const filePath = path.join(catPath, f);
                        const stats = fs.statSync(filePath);
                        catSize += stats.size;
                        
                        // Collect recent files
                        recentFiles.push({
                            name: f,
                            category: item.name,
                            time: stats.mtime.getTime(),
                            path: `/images/${item.name}/${f}`
                        });
                    });

                    totalFiles += files.length;
                    totalSize += catSize;

                    categories.push({
                        name: item.name,
                        count: files.length,
                        size: catSize,
                        preview: files[0]
                    });
                }
            } catch (e) {
                // ignore permission errors or empty folders
            }
        }
    });

    // Sort categories by count
    categories.sort((a, b) => b.count - a.count);

    // Calculate percentages
    categories = categories.map(cat => ({
        ...cat,
        percentage: totalFiles > 0 ? Math.round((cat.count / totalFiles) * 100) : 0
    }));

    // Sort recent files by time (newest first) and take top 2
    recentFiles.sort((a, b) => b.time - a.time);
    const insights = recentFiles.slice(0, 2).map(f => ({
        title: "New Screenshot Detected", // Placeholder until we have OCR
        category: f.category,
        detail: `Found in ${f.category}`,
        time: "Just now", // You might want to format relative time here
        image: f.path,
        amount: null // Placeholder
    }));

    return { totalFiles, totalSize, categories, insights };
}

app.get('/api/stats', (req, res) => {
    try {
        const { totalFiles, totalSize, categories, insights } = getStats();
        
        // Format size to GB or MB
        const sizeInGB = (totalSize / (1024 * 1024 * 1024)).toFixed(2);
        
        const stats = {
            total_photos: totalFiles,
            storage_usage: sizeInGB + " GB",
            storage_saved: "0.5 GB", // Mocked "Optimization"
            categories: categories,
            insights: insights // Now dynamic based on real recent files
        };

        res.json(stats);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Failed to generate stats' });
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