---
applyTo: 'ppg_database/**'
---
## Pet Poison Guard Database: AI Agent Instructions

### Project Overview
This directory (`ppg_database/`) provides the PostgreSQL 17 + pgvector database for Pet Poison Guard. It manages recipe, embedding, and pet poison data for backend AI analysis. All initialization and data loading are automated via Docker.

### Key Files & Structure
- `Dockerfile`: Builds a container with PostgreSQL 17, pgvector, Python 3.13, and required packages. Sets up `/app` as the working directory and exposes port 8001.
- `10_create_tables.sql`: Creates tables (`recipe_data`, `rec_embeds`, `pet_poisons`) and installs pgvector extension.
- `20_load_tables.sh`: Runs `load_tables.py` to populate tables from JSON/PKL files.
- `load_tables.py`: Loads data into DB using psycopg2, numpy, tqdm. Handles JSON and PKL formats. Connection info is hardcoded for local container use.
- Data files: `layer1.json`, `layer2.json`, `layer2+.json`, `petpoison_data.json`, `rec_embeds.pkl`, `rec_ids.pkl`.

### Build & Run Workflow
1. **Build the image:**
	```bash
	docker build -t ppg_database .
	```
2. **Run the container:**
	```bash
	docker run -d --name ppg_database \
		 -e POSTGRES_PASSWORD=mysecretpassword \
		 -e TZ=Asia/Seoul \
		 -p 8001:8001 ppg_database
	```
3. **Initialization:**
	- On first run, tables are created and all data is loaded automatically (see logs with `docker logs ppg_database`).
	- No manual intervention is needed for data loading.

### Accessing the Database
- Connect via psql inside the container:
  ```bash
  docker exec -it ppg_database psql -U postgres -d postgres -p 8001
  ```
- Default DB name/user: `postgres`, password: `mysecretpassword`, port: `8001`.

### Coding Patterns & Conventions
- Data loading is always performed via Python (`load_tables.py`) using psycopg2 and numpy. See function patterns for inserting JSON and PKL data.
- Table schemas are defined in `10_create_tables.sql` and should not be changed without updating both the SQL and loader script.
- All data files must be present in `/app` at build time; Dockerfile copies them automatically.
- For new data types, update both the SQL schema and loader script, and ensure Dockerfile copies new files.

### Integration Points
- Backend (`ppg_backend`) connects to this DB for recipe and poison data queries. Ensure DB is running and accessible on port 8001.
- No direct frontend integration; all access is via backend API.

### Troubleshooting
- Check container logs for errors: `docker logs ppg_database`
- If data loading fails, verify file presence and DB connection info in `load_tables.py`.

### Example: Adding a New Table
1. Update `10_create_tables.sql` with new table definition.
2. Update `load_tables.py` to insert data into the new table.
3. Add new data files and update Dockerfile to copy them.
4. Rebuild and rerun the container.

---
For backend integration, see `.github/instructions/backend.instructions.md`.