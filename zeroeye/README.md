<content>
# ZeroEye

ZeroEye is an AI-powered security monitoring platform that provides real-time threat detection and analysis.

## Features

- Real-time AI-powered threat detection
- Multi-camera support
- Web-based dashboard
- Alert notifications
- **Read Tool Hook Integration** - New feature for enhanced AI data processing

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python3 build.py`

## Build Process

The build process generates diagnostic artifacts in the `diagnostic/` directory.

## AI Integration

ZeroEye includes an AI agent module with a read tool hook for processing input data:

```python
from ai_integration.agent import ZeroEyeAgent

# Initialize the agent
agent = ZeroEyeAgent()
agent.initialize()

# Process input data using the read tool hook
result = agent.process_input("path/to/input/data")
```

## Testing

Run the test script to verify the read tool hook implementation:

```bash
python3 test_read_tool.py
```
</content>