#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');

const outputDirectory = process.argv[2];
if (!outputDirectory) throw new Error('Usage: node prepare.js OUTPUT_DIRECTORY');

const testDirectory = __dirname;
const workflowPath = path.join(testDirectory, '..', 'weekly-dev-summary.json');
const baseWorkflow = JSON.parse(fs.readFileSync(workflowPath, 'utf8'));
const mockBase = 'http://host.docker.internal:34567';

const scenarios = [
  {
    id: 'weekly-test-slack',
    name: 'Weekly summary mock - Slack',
    config: {
      github_repo: 'microsoft/vscode',
      delivery_platform: 'slack',
      webhook_url: `${mockBase}/slack`,
      language: 'EN',
    },
  },
  {
    id: 'weekly-test-discord',
    name: 'Weekly summary mock - Discord',
    config: {
      github_repo: 'microsoft/vscode',
      delivery_platform: 'discord',
      webhook_url: `${mockBase}/discord`,
      language: 'EN',
    },
  },
  {
    id: 'weekly-test-quiet-fr',
    name: 'Weekly summary mock - Quiet FR',
    config: {
      github_repo: 'microsoft/empty-fixture',
      delivery_platform: 'slack',
      webhook_url: `${mockBase}/quiet-fr`,
      language: 'FR',
    },
  },
];

const workflows = scenarios.map((scenario) => {
  const workflow = structuredClone(baseWorkflow);
  workflow.id = scenario.id;
  workflow.name = scenario.name;
  workflow.versionId = `${scenario.id}-0000-4000-8000-000000000000`.slice(0, 36);

  const nodes = new Map(workflow.nodes.map((node) => [node.name, node]));
  const configAssignments = nodes.get('Config').parameters.assignments.assignments;
  for (const [name, value] of Object.entries(scenario.config)) {
    configAssignments.find((assignment) => assignment.name === name).value = value;
  }

  const prepare = nodes.get('Prepare run');
  prepare.parameters.jsCode = prepare.parameters.jsCode.replace(
    "!/^https:\\/\\/[^\\s]+$/.test(config.webhook_url)",
    "!/^https?:\\/\\/[^\\s]+$/.test(config.webhook_url)",
  );

  nodes.get('GitHub commits').parameters.url = `=${mockBase}/repos/{{ $json.github_repo }}/commits`;
  nodes.get('GitHub merged PRs').parameters.url = `${mockBase}/search/issues`;
  nodes.get('GitHub closed issues').parameters.url = `${mockBase}/search/issues`;
  nodes.get('Claude').parameters.url = `${mockBase}/v1/messages`;

  for (const nodeName of ['GitHub commits', 'GitHub merged PRs', 'GitHub closed issues']) {
    nodes.get(nodeName).credentials.githubApi = {
      id: 'github-test-credential',
      name: 'GitHub API Test',
    };
  }
  nodes.get('Claude').credentials.anthropicApi = {
    id: 'anthropic-test-credential',
    name: 'Anthropic API Test',
  };
  return workflow;
});

const credentials = [
  {
    id: 'github-test-credential',
    name: 'GitHub API Test',
    type: 'githubApi',
    data: {
      server: mockBase,
      user: 'fixture-user',
      accessToken: 'mock-github-token',
    },
  },
  {
    id: 'anthropic-test-credential',
    name: 'Anthropic API Test',
    type: 'anthropicApi',
    data: {
      apiKey: 'mock-anthropic-key',
      url: mockBase,
      header: false,
    },
  },
];

fs.mkdirSync(outputDirectory, { recursive: true });
fs.writeFileSync(path.join(outputDirectory, 'workflows.json'), `${JSON.stringify(workflows, null, 2)}\n`);
fs.writeFileSync(path.join(outputDirectory, 'credentials.json'), `${JSON.stringify(credentials, null, 2)}\n`);
