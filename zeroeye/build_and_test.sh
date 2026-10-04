<content>
#!/bin/bash
# Build and test script for ZeroEye

echo "Starting ZeroEye build and test process..."

# Create necessary directories
mkdir -p models
mkdir -p logs
mkdir -p diagnostic

# Run the build script
echo "Running build script..."
python3 build.py

# Run the test script
echo "Running tests..."
python3 test_read_tool.py

echo "Build and test process completed."
</content>