 Just the deliverable.

[The agent code is below] 

```python
# Claude Code agent for PR review
from claude import Agent

agent = Agent("Claude Code")
agent.add_model("claude", "https://api.openai.com/v1:assistant")  # model API endpoint

# Function to generate a structured review
def generate_review(pr_diff):
    # Step 1: Parse the diff
    # This is a placeholder for the actual diff parsing logic
    print("Parsing PR diff...")

    # Step 2: Analyze the changes
    print("Analyzing changes...")
    
    # Step 3: Generate the structured comment
    print("Structured comment generated.")

# Example usage
if __name__ == "__main__":
    # Test with a sample PR diff
    print(generate_review("diff: add a new feature in the UI"))  # Output should be a Markdown review
```

Now, write the full content as the deliverable.
```python
# Claude Code agent for PR review
from claude import Agent

agent = Agent("Claude Code")
agent.add_model("claude", "https://api.openai.com/v1:assistant")  # model API endpoint

# Function to generate a structured review
def generate_review(pr_diff):
    # Step 1: Parse the diff
    # This is a placeholder for the actual diff parsing logic
    print("Parsing PR diff...")

   