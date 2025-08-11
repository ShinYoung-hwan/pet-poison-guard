---
applyTo: '**/ppg_backend'
---
# Pet Poison Guard Backend - Copilot Instructions

## Overview
This backend is a RESTful API service responsible for:
- Receiving image uploads from the frontend.
- Communicating with the AI server for food safety analysis.
- Returning analysis results to the frontend.

## Coding Guidelines
- Use Python (FastAPI preferred) for API implementation.
- Ensure endpoints are well-documented with OpenAPI/Swagger.
- Validate all incoming data (e.g., image file types, size limits).
- Handle errors gracefully and return meaningful HTTP status codes.
- Use async functions for I/O-bound operations.
- Write modular, testable code with clear separation of concerns.
- Log requests and errors for debugging and monitoring.

## API Endpoints
- `/analyze` (POST): Accepts an image file, returns food safety analysis.
- `/health` (GET): Returns service health status.

## Security
- Sanitize all inputs.
- Limit file upload size.
- Return generic error messages to avoid leaking sensitive info.

## Testing
- Include unit and integration tests for all endpoints.
- Use mock AI server responses for backend tests.

## Dependencies
- List all dependencies in `requirements.txt`.
- Pin versions for reproducibility.

## Communication with AI Server
- Use HTTP requests to send images and receive analysis.
- Handle timeouts and retries gracefully.

## Documentation
- Keep API docs up-to-date.
- Provide example requests and responses.
