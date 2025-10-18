#!/usr/bin/env node

/**
 * Script to remove ALL console.log/error/warn/info/debug statements from src directory
 * Usage: node cleanup_console_logs.js
 */

const fs = require('fs');
const path = require('path');

const SRC_DIR = path.join(__dirname, 'src');
let totalRemoved = 0;
let filesModified = 0;

function removeConsoleLogs(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');
    let modified = content;
    let removedCount = 0;

    // Pattern to match console statements (single and multi-line)
    // Matches: console.log(...), console.error(...), etc.
    const patterns = [
        // Single line console statements
        /\s*console\.(log|error|warn|info|debug)\([^;]*\);?\n?/g,
        // Multi-line console statements
        /\s*console\.(log|error|warn|info|debug)\([^)]*\([^)]*\)[^)]*\);?\n?/g,
        // Console statements with template literals
        /\s*console\.(log|error|warn|info|debug)\(`[^`]*`[^;]*\);?\n?/g,
        // Console statements spanning multiple lines
        /\s*console\.(log|error|warn|info|debug)\(\s*[^;]*?\);?\n?/gs,
    ];

    patterns.forEach(pattern => {
        const matches = modified.match(pattern);
        if (matches) {
            removedCount += matches.length;
            modified = modified.replace(pattern, '');
        }
    });

    // Additional cleanup for console statements that might be left
    // This is more aggressive and handles edge cases
    const lines = modified.split('\n');
    const cleanedLines = [];
    let skipNext = false;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();

        // Skip if this line starts a console statement
        if (trimmed.match(/^console\.(log|error|warn|info|debug)\(/)) {
            skipNext = true;
            removedCount++;

            // Check if it's a complete statement on one line
            if (trimmed.includes(');')) {
                skipNext = false;
            }
            continue;
        }

        // Skip continuation lines
        if (skipNext) {
            if (trimmed.includes(');')) {
                skipNext = false;
            }
            continue;
        }

        cleanedLines.push(line);
    }

    modified = cleanedLines.join('\n');

    // Clean up multiple consecutive empty lines
    modified = modified.replace(/\n\n\n+/g, '\n\n');

    if (content !== modified) {
        fs.writeFileSync(filePath, modified, 'utf8');
        totalRemoved += removedCount;
        filesModified++;
        console.log(`✅ ${path.relative(SRC_DIR, filePath)}: Removed ${removedCount} console statement(s)`);
        return true;
    }

    return false;
}

function processDirectory(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);

        if (entry.isDirectory()) {
            // Skip node_modules and other unnecessary directories
            if (!['node_modules', '.git', 'build', 'dist'].includes(entry.name)) {
                processDirectory(fullPath);
            }
        } else if (entry.isFile()) {
            // Process only JS and JSX files
            if (entry.name.endsWith('.js') || entry.name.endsWith('.jsx')) {
                try {
                    removeConsoleLogs(fullPath);
                } catch (error) {
                    console.error(`❌ Error processing ${fullPath}:`, error.message);
                }
            }
        }
    }
}

console.log('🧹 Starting console log cleanup...\n');
processDirectory(SRC_DIR);
console.log('\n' + '='.repeat(60));
console.log(`✨ Cleanup complete!`);
console.log(`📁 Files modified: ${filesModified}`);
console.log(`🗑️  Console statements removed: ${totalRemoved}`);
console.log('='.repeat(60));
