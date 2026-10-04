<content>
#!/usr/bin/env python3
"""
Test script for the read tool hook implementation
"""

import os
import sys
import tempfile
import json
from datetime import datetime

# Add the ai_integration module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_integration'))

from ai_integration.agent import ZeroEyeAgent

def test_read_tool_hook():
    """Test the read tool hook functionality"""
    print("Testing ZeroEye Agent Read Tool Hook...")
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        test_content = f"Test data for ZeroEye Agent\nGenerated: {datetime.now().isoformat()}"
        f.write(test_content)
        test_file_path = f.name
    
    try:
        # Initialize the agent
        agent = ZeroEyeAgent()
        
        # Test initialization
        assert agent.initialize(), "Agent initialization failed"
        assert agent.read_tool_hook is not None, "Read tool hook not initialized"
        
        # Test data reading
        result = agent.process_input(test_file_path)
        
        # Verify results
        assert result["status"] == "processed", f"Expected 'processed' status, got '{result['status']}'"
        assert result["source"] == test_file_path, "Source path mismatch"
        assert "timestamp" in result, "Timestamp missing from result"
        
        # Test history
        history = agent.read_tool_hook.get_processing_history()
        assert len(history) == 1, f"Expected 1 entry in history, got {len(history)}"
        assert history[0]["source"] == test_file_path, "History entry mismatch"
        
        # Test status
        status = agent.get_status()
        assert status["initialized"] == True, "Agent not marked as initialized"
        assert status["read_tool_hook"] == True, "Read tool hook not marked as available"
        
        print("✓ All tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False
        
    finally:
        # Clean up
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)
        
        # Shutdown agent
        if 'agent' in locals():
            agent.shutdown()

def main():
    """Main test function"""
    success = test_read_tool_hook()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
</content>