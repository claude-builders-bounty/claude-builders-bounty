import { strict as assert } from "node:assert";
import { buildReview } from "../src/review.mjs";

const fixture = {
  url: "https://github.com/example/project/pull/7",
  owner: "example",
  repo: "project",
  number: 7,
  title: "Improve settings validation",
  body: "Adds stricter validation around settings and documents the expected behavior.",
  state: "open",
  author: "contributor",
  base: "main",
  head: "settings-validation",
  additions: 42,
  deletions: 10,
  changedFiles: 3,
  files: [
    {
      filename: "src/settings.ts",
      status: "modified",
      additions: 30,
      deletions: 8,
      changes: 38,
      patch: "validate settings before save",
    },
    {
      filename: "src/settings.test.ts",
      status: "modified",
      additions: 10,
      deletions: 2,
      changes: 12,
      patch: "adds validation coverage",
    },
    {
      filename: "README.md",
      status: "modified",
      additions: 2,
      deletions: 0,
      changes: 2,
      patch: "document settings validation",
    },
  ],
};

const review = buildReview(fixture);

assert.match(review, /## Summary/);
assert.match(review, /## Identified Risks/);
assert.match(review, /## Improvement Suggestions/);
assert.match(review, /## Changed Files/);
assert.match(review, /## Confidence/);
assert.match(review, /src\/settings\.ts/);
assert.match(review, /src\/settings\.test\.ts/);

const riskyFixture = {
  ...fixture,
  title: "Add checkout session endpoint",
  body: "Creates a Stripe checkout session and stores a customer token.",
  additions: 180,
  deletions: 20,
  changedFiles: 2,
  files: [
    {
      filename: "src/billing.ts",
      status: "added",
      additions: 120,
      deletions: 0,
      changes: 120,
      patch: "create stripe checkout with token and customer secret",
    },
    {
      filename: "src/billing-routes.ts",
      status: "modified",
      additions: 60,
      deletions: 20,
      changes: 80,
      patch: "new payment route",
    },
  ],
};

const riskyReview = buildReview(riskyFixture);

assert.match(riskyReview, /payment or billing behavior/);
assert.match(riskyReview, /authentication or secret handling/);
assert.match(riskyReview, /No obvious test file was changed/);
assert.match(riskyReview, /Add or reference tests/);
assert.match(riskyReview, /rollout, rollback, and secret-handling/);
assert.match(riskyReview, /## Confidence\n\nMedium/);

console.log("review.test.mjs ok");
