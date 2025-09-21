---
applyTo: '**'
---


# Pet Poison Guard - Copilot Instructions

## Project Overview
Pet Poison Guard helps pet owners identify foods that may be harmful to their pets using image-based AI analysis. The system is composed of three main services: frontend (React/Vite), backend (FastAPI), and a database/AI server (PyTorch, PostgreSQL+pgvector).

## Architecture & Data Flow
- **Frontend** (`ppg_frontend/`): React + TypeScript mobile-UI web app (Vite-based). Users upload food images and view analysis results.
- **Backend** (`ppg_backend/`): FastAPI RESTful API. Handles image upload, analysis requests, and result delivery. Communicates with AI server and database.
- **Database** (`ppg_database/`): PostgreSQL 17 + pgvector. Stores food safety data, embeddings, and analysis results. Initialized via Docker and custom scripts.
- **AI Server**: PyTorch model for food safety analysis. Invoked by backend via direct calls or task queue.

## Conventions & Patterns
- **Backend:**
	- Use Pydantic for request/response validation (`schemas/`).
	- Organize by feature: `api/`, `models/`, `services/`.
	- RESTful endpoints, JSON payloads.
	- Model/data files in `app/services/snapshots/`.
- **Frontend:**
	- Feature-based structure: `components/`, `pages/`, `services/`.
	- Use React hooks for API polling (`usePolling.ts`).
	- TypeScript models for API results (`models/AnalysisResult.ts`).
- **Database:**
	- Data initialization via SQL and shell scripts (`10_create_tables.sql`, `20_load_tables.sh`).
	- Embeddings and IDs in `.pkl` files.
	- Uses pgvector for vector search.

## Integration Points
- Frontend <-> Backend: HTTP/JSON (see `api.ts`)
- Backend <-> AI Server: Python function calls/task queue (`ai_service.py`, `task_service.py`)
- Backend <-> Database: Direct SQL/ORM, data loaded from JSON/PKL files

## External Dependencies
- React, Vite, Material-UI (frontend)
- FastAPI, Pydantic, PyTorch (backend/AI)
- PostgreSQL 17 + pgvector (database)

## Tips for AI Agents
- Always check `ppg_backend/app/services/snapshots/` for required model/data files.
- Backend and database containers use environment variables for secrets/config.
- For new features, follow existing feature-based organization in both frontend and backend.
- Use provided scripts for DB initialization and data loading.

## References
- See `README.md` in each major directory for more details and examples.
- For architecture, see the mermaid diagram in the root `README.md`.