## Summary
This PR adds a new CLI command `deploy --environment <env>` for deploying services to staging or production. It introduces a new deployment config parser, extends the CI pipeline step, and adds environment-specific variable injection.

## Identified Risks
- Production deployments currently lack an approval gate — any merged PR triggering CI could deploy to prod
- The config parser does not validate required fields before attempting deployment, which could cause silent failures
- No rollback mechanism exists if a deployment fails mid-flight

## Improvement Suggestions
- Add a manual approval gate for the `production` environment in the CI workflow
- Implement config validation with clear error messages for missing required fields
- Add a health-check step after deployment to verify service readiness before marking success
- Document the new command in the CLI help text and add a `--dry-run` flag for testing

## Confidence Score
Medium
