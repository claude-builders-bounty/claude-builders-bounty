### Summary of Changes
This Pull Request introduces an optional `verify` parameter to the `RustChainClient` constructor, allowing users to toggle SSL verification. Additionally, it includes a new Proof-of-Concept tool, `eligibility_checker.py`, which utilizes the SDK to check miner eligibility and reward distributions for specific epochs.

### Identified Risks
- **Security**: Disabling SSL verification (`verify=False`) in the PoC tool makes the communication vulnerable to Man-in-the-Middle (MitM) attacks.
- **Dependency**: The `eligibility_checker.py` script depends on `rustchain_sdk` being installed or in the Python path, which might cause issues if run directly from the source tree without proper environment setup.

### Improvement Suggestions
- **Error Handling**: In `eligibility_checker.py`, the generic `except Exception as e` could be replaced with more specific SDK exceptions (e.g., `APIError`, `RCConnectionError`) to provide better debugging information.
- **Logging**: Instead of using `import logging` inside `__init__`, consider initializing a logger at the module level for consistency and performance.

### Confidence Score
High
