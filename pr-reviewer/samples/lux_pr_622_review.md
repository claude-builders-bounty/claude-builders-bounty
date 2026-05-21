### Summary of Changes
This pull request introduces a new integration for the Coinbase Advanced Trade API into the Lux framework. It adds several prisms for interacting with the exchange, including executing orders, canceling orders, fetching market data, checking open orders, and retrieving the account portfolio. Additionally, it provides Python utility wrappers for the Coinbase SDK.

### Identified Risks
- The `coinbase_api_secret` is parsed via the `config.ex` file, which expects the secret to be properly configured. Ensure that invalid credentials do not cause unexpected panics in production.
- Order execution methods do not currently seem to include rate limiting handling out of the box, which could lead to API bans under heavy load.

### Improvement Suggestions
- Consider adding error handling for HTTP 429 (Rate Limit) specifically in the Python utility scripts.
- The `setup.py` added inside the Python `coinbase_utils` directory could be integrated into the global `pyproject.toml` dependencies instead to centralize package management.

### Confidence Score
High
