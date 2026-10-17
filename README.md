# QueryWise AI

**An AI-Powered Data Analytics Platform**

QueryWise AI is a web-based data analytics application that helps users explore datasets using natural-language questions and SQL queries. It supports querying a MySQL database and uploading CSV or Excel files for analysis through an interactive dashboard.

## Features

- **Natural Language Querying:** Ask questions about data using AI-powered query generation.
- **MySQL Integration:** Connect to a MySQL database and analyze structured data.
- **CSV and Excel Uploads:** Upload datasets and inspect their contents.
- **Dataset Management:** View previously uploaded datasets and delete datasets when no longer needed.
- **SQL Query Validation:** Validate queries before execution to restrict unsafe database operations.
- **DuckDB Integration:** Execute SQL queries against uploaded datasets.
- **Interactive Dashboard:** View query results in tables and charts.
- **Data Preview:** Preview uploaded data before querying.
- **REST API:** Backend APIs built using FastAPI.
- **Persistent Local Storage:** Keep uploaded datasets available across backend restarts.
- **Error Handling:** Return structured API responses for common errors.

## Tech Stack

### Frontend
- React.js
- Vite
- Recharts
- Lucide React
- CSS

### Backend
- Python
- FastAPI
- SQLAlchemy
- PyMySQL
- Pandas
- DuckDB
- SQLGlot
- Google Gemini API

### Database
- MySQL

### Testing and Development
- Pytest
- Git and GitHub
- Visual Studio Code
- Swagger UI

## Project Structure

```text
QueryWise-AI/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── services/
│   │       └── upload_store.py
│   ├── data/
│   │   └── uploaded_datasets/
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── App.css
│   ├── package.json
│   └── .gitignore
├── .gitignore
└── README.md
```

*Note: This is a simplified overview. Your actual project may contain additional files and directories.*

## Prerequisites

Install the following before running the application:

- Python 3.10 or later
- Node.js and npm
- MySQL Server
- A Google Gemini API key for AI-powered query generation

## Getting Started

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd "QueryWise AI"
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your actual GitHub repository URL.

### 2. Set Up the Backend

Open a terminal in the project root:

```bash
cd backend
python -m venv venv
```

Activate the virtual environment.

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file inside the `backend` directory using `.env.example` as a template.

Configure the environment variables required by your application, including:

```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_NAME=querywise_db
DB_USER=your_database_user
DB_PASSWORD=your_database_password
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_configured_model
```

**Important:** Use the exact environment variable names expected by your backend code. Never commit your actual `.env` file, database credentials, or API keys to GitHub.

### 4. Configure MySQL

Start your MySQL server and create the database:

```sql
CREATE DATABASE querywise_db;
```

Configure the required tables and a database account with only the permissions needed by the application. Update your backend environment variables to match your MySQL configuration.

### 5. Start the Backend

From the `backend` directory, run:

```bash
uvicorn app.main:app --reload
```

The backend will typically be available at:

- API base URL: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/health`

### 6. Start the Frontend

Open a second terminal:

```bash
cd "D:\ALL PROJECTS\QueryWise AI\frontend"
npm install
npm run dev
```

Open the local URL displayed by Vite in your terminal, usually `http://localhost:5173`.

## API Endpoints

The backend includes endpoints for health checks, dataset uploads, saved dataset management, and querying.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check backend health |
| GET | `/api/db-health` | Check database connectivity |
| POST | `/api/upload` | Upload a CSV or Excel dataset |
| GET | `/api/upload/{dataset_id}` | Retrieve an uploaded dataset, if supported by the current implementation |
| DELETE | `/api/upload/{dataset_id}` | Delete an uploaded dataset |
| POST | `/api/ask` | Ask a question about the connected MySQL database |
| POST | `/api/upload/ask` | Ask a question about an uploaded dataset |
| GET | `/api/datasets` | List saved datasets |

Interactive API documentation is available at `/docs` when the backend is running.

## How It Works

1. Start the backend and frontend.
2. Choose the MySQL data workflow or upload a CSV/Excel file.
3. Preview the dataset and review its columns.
4. Submit a question using the available query workflow.
5. The backend validates the generated or submitted SQL before execution.
6. Results are returned to the frontend and displayed in tables or charts.
7. Manage saved datasets from the dashboard.

## Security Considerations

- Keep API keys and database passwords in environment variables.
- Exclude `.env`, virtual environments, `node_modules`, and local uploaded data from Git.
- Restrict database access to the permissions required by the application.
- Validate SQL queries before execution and restrict queries to permitted tables and operations.
- Uploaded datasets are stored locally; deploy only with appropriate access controls and storage protections.
- This project is intended as a local development application unless authentication and production security controls are added.

## Future Enhancements

- Add a Gemini-independent direct SQL mode for uploaded datasets.
- Improve query history and saved query management.
- Add more visualization options and dashboard customization.
- Improve automated integration testing.
- Add authentication and authorization for multi-user deployments.
- Support deployment with production-grade configuration and monitoring.

## Author

**Shreya V K**

Computer Science and Engineering | Python Full Stack Development

GitHub: [Shreyavk28](https://github.com/Shreyavk28)

LinkedIn: [Shreya VK](https://linkedin.com/in/shreya-vk-softwareengineer)

---

*QueryWise AI — Turn your data into insights.*
