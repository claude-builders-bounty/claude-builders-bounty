# n8n Weekly Development Summary Workflow

## Setup Instructions

1. Create a new n8n workflow
2. Import the provided JSON file
3. Configure the GitHub node with your repository details
4. Set up the Claude API credentials in the n8n environment variables
5. Configure the output node (email or webhook) with your delivery preferences

## Configuration

The following environment variables can be set:
- `GITHUB_REPOSITORY`: The repository to summarize
- `DESTINATION_CHANNEL`: Where to send the summary (email or webhook URL)
- `LANGUAGE`: Summary language (EN/FR)

## Testing

To test the workflow:
1. Set up a test schedule (e.g., every minute)
2. Run the workflow manually to verify it works
3. Check the execution log for successful completion
4. Update the schedule to the desired weekly interval
5. Save and activate the workflow

## Notes

The workflow will fetch the last week's commits, closed issues, and merged PRs from the configured repository, generate a narrative summary using Claude API, and deliver it to the configured destination.