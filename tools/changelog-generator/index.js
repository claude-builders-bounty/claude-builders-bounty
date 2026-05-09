#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Helper to run shell commands
function runCommand(command) {
    try {
        return execSync(command, { encoding: 'utf8' }).trim();
    } catch (error) {
        return '';
    }
}

// Get the latest git tag
function getLatestTag() {
    return runCommand('git describe --tags --abbrev=0');
}

// Get commits since the last tag (or all if no tag exists)
function getCommits(latestTag) {
    const format = '"--pretty=format:%H|%s|%an|%ad"';
    let command = `git log ${format}`;
    
    if (latestTag) {
        command = `git log ${latestTag}..HEAD ${format}`;
    }
    
    const output = runCommand(command);
    if (!output) return [];
    
    return output.split('\n').map(line => {
        const [hash, message, author, date] = line.split('|');
        return { hash, message, author, date };
    });
}

// Parse conventional commits
function parseCommits(commits) {
    const categories = {
        Features: [],
        Fixes: [],
        Documentation: [],
        Performance: [],
        Refactors: [],
        Other: []
    };

    const typeMapping = {
        feat: 'Features',
        fix: 'Fixes',
        docs: 'Documentation',
        perf: 'Performance',
        refactor: 'Refactors',
        chore: 'Other',
        style: 'Other',
        test: 'Other',
        build: 'Other',
        ci: 'Other'
    };

    const regex = /^(\w+)(?:\((.*)\))?!?: (.*)$/;

    commits.forEach(commit => {
        const match = commit.message.match(regex);
        if (match) {
            const type = match[1];
            const scope = match[2] ? `**${match[2]}:** ` : '';
            const description = match[3];
            
            const category = typeMapping[type] || 'Other';
            categories[category].push(`- ${scope}${description} (${commit.hash.substring(0, 7)}) by @${commit.author}`);
        } else {
            categories['Other'].push(`- ${commit.message} (${commit.hash.substring(0, 7)}) by @${commit.author}`);
        }
    });

    return categories;
}

// Generate markdown content
function generateMarkdown(categories, latestTag) {
    const date = new Date().toISOString().split('T')[0];
    const version = latestTag ? `Unreleased (since ${latestTag})` : `Initial Release`;
    
    let markdown = `## ${version} - ${date}\n\n`;

    for (const [category, items] of Object.entries(categories)) {
        if (items.length > 0) {
            markdown += `### ${category}\n`;
            items.forEach(item => {
                markdown += `${item}\n`;
            });
            markdown += '\n';
        }
    }

    return markdown;
}

function main() {
    console.log('Generating structured changelog...');
    
    // Simple argument parsing
    const args = process.argv.slice(2);
    const isDryRun = args.includes('--dry-run');
    let outputFile = 'CHANGELOG.md';
    
    const outIndex = args.indexOf('--output');
    if (outIndex !== -1 && args[outIndex + 1]) {
        outputFile = args[outIndex + 1];
    }

    const latestTag = getLatestTag();
    if (latestTag) {
        console.log(`Found latest tag: ${latestTag}`);
    } else {
        console.log('No tags found, generating changelog for all commits.');
    }

    const commits = getCommits(latestTag);
    console.log(`Found ${commits.length} commits.`);

    if (commits.length === 0) {
        console.log('No new commits to generate a changelog from.');
        return;
    }

    const parsedCategories = parseCommits(commits);
    const markdown = generateMarkdown(parsedCategories, latestTag);
    
    if (isDryRun) {
        console.log('\n--- DRY RUN OUTPUT ---\n');
        console.log(markdown);
        console.log('----------------------\n');
        console.log('Dry run complete. No files were modified.');
        return;
    }

    const outputPath = path.resolve(process.cwd(), outputFile);
    
    // Prepend to existing CHANGELOG if it exists
    if (fs.existsSync(outputPath)) {
        let existing = fs.readFileSync(outputPath, 'utf8');
        const headerIndex = existing.indexOf('## ');
        if (headerIndex !== -1) {
            const updated = existing.substring(0, headerIndex) + markdown + existing.substring(headerIndex);
            fs.writeFileSync(outputPath, updated);
        } else {
            fs.writeFileSync(outputPath, markdown + '\n' + existing);
        }
        console.log(`Appended to existing ${outputFile}`);
    } else {
        fs.writeFileSync(outputPath, '# Changelog\n\n' + markdown);
        console.log(`Created new ${outputFile}`);
    }
    
    console.log('Done!');
}

main();
