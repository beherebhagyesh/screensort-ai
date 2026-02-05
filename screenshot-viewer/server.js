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
        const safeArgs = args.map(a => `"${a.replace(/