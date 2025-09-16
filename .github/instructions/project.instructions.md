---
applyTo: '**'
---

# Pet Poison Guard - Project Copilot Instructions

## Project Overview
This document provides context and coding guidelines for the Pet Poison Guard project, which is designed to help pet owners identify potentially harmful foods through image analysis.

## Architecture & Data Flow
- User uploads food images via the frontend.
- Frontend sends HTTP requests to backend API endpoints.
- Backend processes requests, queues tasks, and interacts with the AI server for analysis.
- Results are returned to the frontend for display.

## Core Components
- **Frontend** (`ppg_frontend/`): React + TypeScript mobile-UI web app (Vite-based)
- **Backend** (`ppg_backend/`): FastAPI RESTful API for image analysis and results
- **AI Server**: PyTorch model for food safety analysis (invoked by backend)

## Integration Points
- Backend and AI server communicate via task queue and direct function calls.
- Frontend and backend communicate via HTTP/JSON.
- Model files and embeddings are stored in `ppg_backend/app/services/snapshots/`.

## Conventions
- Use Pydantic for backend data validation.
- Organize frontend by feature (pages, components, services).
- Backend endpoints follow RESTful conventions.
- Use environment variables/config files for sensitive settings.