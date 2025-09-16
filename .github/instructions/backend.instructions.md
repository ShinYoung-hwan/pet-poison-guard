---
applyTo: 'ppg_backend/**'
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
- use ppg_backend/.venv for virtual environment management

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

### API Endpoint Test Writing Principles

When writing test code for web backend API endpoints, follow these principles:

#### 1. Independence
- Each test must run independently. The result of one test should not affect others. Use setup/teardown or mocks to isolate external dependencies.

#### 2. Reproducibility
- Tests should always produce the same result regardless of when or where they are run. Avoid reliance on time, randomness, or external APIs.

#### 3. Isolation
- Tests should focus on specific system parts. For example, when testing the analysis API, mock the AI server and focus on the backend logic only.

#### 4. Coverage
- Cover as many scenarios as possible:
	- Success cases: Valid requests and expected responses.
	- Failure cases: Invalid input, permission errors, non-existent resources, etc.
	- Edge cases: Boundary values, minimum/maximum lengths, zero/negative values.

#### 5. Clarity
- Test code should be easy to understand. Clearly state the test's purpose, input, and expected result. Use descriptive function names (e.g., `test_analyze_image_invalid_type`).

#### Example Structure
- Use the given/when/then pattern:
	- Given: Set up initial state (e.g., define input data)
	- When: Call the API endpoint
	- Then: Assert the expected result

Following these principles ensures robust, maintainable, and clear test code for backend API endpoints.

## Dependencies
- List all dependencies in `requirements.txt`.
- Pin versions for reproducibility.

## Communication with AI Server
- Use HTTP requests to send images and receive analysis.
- Handle timeouts and retries gracefully.

## Documentation
- Keep API docs up-to-date.
- Provide example requests and responses.
