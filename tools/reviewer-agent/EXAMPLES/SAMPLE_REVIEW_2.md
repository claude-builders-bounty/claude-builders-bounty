### PR Review: fix: resolve memory leak in websocket reconnection logic

**Summary of changes**
This PR fixes a critical memory leak where WebSocket event listeners were not being properly removed during reconnection cycles. It introduces a `Cleanup` manager to track and dispose of active listeners.

**Identified risks**
- Potential for 'double-cleanup' if the reconnection is triggered rapidly.
- Slight increase in memory footprint for the listener tracking Map.

**Improvement suggestions**
- Use a `WeakMap` for the listener tracker to allow for better garbage collection of abandoned sockets.
- Add a timeout to the cleanup logic to prevent hanging references.

**Confidence score: High**
