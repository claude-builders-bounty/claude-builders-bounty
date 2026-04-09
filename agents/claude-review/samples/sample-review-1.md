# Sample Review 1: PR #123 - Feature Implementation

## Original PR
https://github.com/example/repo/pull/123

## Claude Review Output

## Summary
This PR adds user authentication middleware to protect API endpoints. It implements JWT token validation and refreshes expired tokens automatically.

## Identified Risks
- **Token storage**: JWT tokens are stored in localStorage which is vulnerable to XSS attacks
- **Missing rate limiting**: No protection against brute force login attempts
- **Error exposure**: Detailed error messages could leak sensitive information about user existence

## Improvement Suggestions
- Use httpOnly cookies instead of localStorage for token storage
- Add rate limiting middleware (e.g., 5 attempts per minute per IP)
- Sanitize error messages to avoid user enumeration attacks
- Add token expiration handling on the client side

## Confidence Score
**Confidence: Medium**

The implementation is functional but has security concerns that should be addressed before merging.