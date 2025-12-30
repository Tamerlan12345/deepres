# Centras Strategic AI-Agent
AI-аналитик для Совета Директоров АО «Сентрас Иншуранс».

## Stack
- **Backend:** Python / FastAPI / SQLAlchemy / WeasyPrint
- **Frontend:** React / Vite / TailwindCSS / Recharts
- **Database:** PostgreSQL
- **AI:** Gemini Deep Research (via API)

## Architecture
The system is designed as a Monolith for easy deployment on Railway.
- The `backend/` directory contains the FastAPI application.
- The `frontend/` directory contains the React application.
- The `Dockerfile` at the root builds the frontend using Node.js, installs Python dependencies, and serves the static frontend files via FastAPI.

## Deployment on Railway
1. **Fork/Clone** this repository to your GitHub.
2. Login to **Railway.app**.
3. Create a **New Project** -> **Deploy from GitHub repo**.
4. Select this repository.
5. Add a **PostgreSQL** database plugin to the project.
6. Go to **Settings** -> **Variables**:
    - `DATABASE_URL`: (Automatically added by the plugin, usually)
    - `GEMINI_API_KEY`: [Your Gemini API Key]
7. The deployment should start automatically.

## Local Development
1. **Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
   (Make sure you have a local postgres or update DATABASE_URL in `.env`)

2. **Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Features
- **Deep Research:** Analyzing competitors, regulations, and products using Gemini.
- **Reporting:** Generating structured JSON reports with specific metrics.
- **Visualization:** Charts and graphs.
- **Export:** Download reports as PDF.
