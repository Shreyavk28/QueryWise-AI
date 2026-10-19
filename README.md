QueryWise AI
AI-Powered Data Analytics | Natural Language to SQL

QueryWise AI is a web-based data analytics application that lets users ask business questions in plain English and view query results from a MySQL database or an uploaded CSV/Excel dataset. For uploaded datasets, the application generates SQL, validates it, executes it against the dataset, and displays the results in an interactive dashboard.
Features
- Natural-language questions: Ask questions about data in plain English.
- MySQL analytics: Submit questions about data in a connected MySQL database.
- CSV and Excel uploads: Upload CSV or XLSX files (maximum file size: 5 MB).
- Persistent dataset management: List, select, preview, and delete saved uploaded datasets.
- SQL validation: Validate SQL before execution and restrict queries to read-only operations.
- Uploaded-data SQL execution: Run validated queries against uploaded datasets using DuckDB.
- Interactive results: View result tables and generated SQL in the dashboard, with supported visualizations.
- REST API: FastAPI endpoints with interactive Swagger documentation.
- Local dataset persistence: Uploaded datasets remain available after a backend restart.
Tech Stack
Frontend
- React
- Vite
- Recharts
- Lucide React
- CSS
Backend
- Python
- FastAPI
- SQLAlchemy
- PyMySQL
- Pandas
- DuckDB
- SQLGlot
- Google Gemini API
Database and testing
- MySQL
- Pytest
- Swagger UI / OpenAPI
Development tools
- Git and GitHub
- Visual Studio Code
Project Structure
QueryWise-AI/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── services/
│   │       └── upload_store.py
│   ├── data/
│   │   └── uploaded_datasets/   # Local data; ignored by Git
│   ├── .env                     # Local secrets; do not commit
│   ├── .env.example             # Safe configuration template
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── App.css
│   ├── package.json
│   └── .gitignore
├── .gitignore
└── README.md
This is a simplified overview; additional files and directories may exist in the repository.
Prerequisites
- Python 3.10 or later
- Node.js and npm
- MySQL Server, if using the MySQL workflow
- A Google Gemini API key for AI-powered natural-language query generation
Setup and Run
1. Clone the repository
git clone YOUR_GITHUB_REPOSITORY_URL
cd "QueryWise AI"
Replace YOUR_GITHUB_REPOSITORY_URL with your actual GitHub repository URL.
2. Set up the backend
From the project root, run:
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
If PowerShell blocks virtual-environment activation, you can invoke the environment's Python directly:
.\venv\Scripts\python.exe -m pip install -r requirements.txt
3. Configure environment variables
Create backend/.env using backend/.env.example as a template. Set the variables expected by your backend code, including the MySQL connection settings and Gemini configuration.

Example only — use the exact variable names required by your implementation:
DB_HOST=localhost
DB_PORT=3306
DB_NAME=querywise_db
DB_USER=your_database_user
DB_PASSWORD=your_database_password
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_configured_model
Security: Never put real passwords, API keys, or connection strings in this README or commit your .env file. Keep .env.example limited to placeholders.
4. Configure MySQL (for the MySQL workflow)
Start MySQL and create the database if it does not already exist:
CREATE DATABASE querywise_db;
Configure the tables and a database account with only the permissions the application needs. Set the corresponding connection variables in backend/.env.

If you only want to test uploaded CSV/XLSX datasets, use the upload workflow; MySQL configuration is needed for the MySQL workflow.
5. Start the backend
From the backend directory, run:
python -m uvicorn app.main:app --reload
The backend should be available at:
- API base: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/health
Keep this terminal running.
6. Start the frontend
Open a second terminal and run:
cd "D:\ALL PROJECTS\QueryWise AI\frontend"
npm install
npm run dev
Open the local address printed by Vite, usually http://localhost:5173.

If you cloned the repository to a different location, change the cd path to your actual frontend directory.
API Endpoints
The current API includes these routes:
Method	Endpoint	Purpose
GET	/api/health	Check backend health
GET	/api/db-health	Check MySQL connectivity
GET	/api/datasets	List saved uploaded datasets
POST	/api/upload	Upload and save a CSV/XLSX dataset
DELETE	/api/upload/{dataset_id}	Delete a saved uploaded dataset
POST	/api/ask	Ask a natural-language question about MySQL data
POST	/api/upload/ask	Ask a natural-language question about a saved uploaded dataset


Interactive request schemas and responses are available at http://127.0.0.1:8000/docs.
Example: Analyze an Uploaded Dataset
1. Open QueryWise AI in your browser.
2. Select or upload employee_performance.csv.
3. Ask: “Who has the highest performance score?”
4. Review the returned result and generated SQL.
For the sample employee dataset, the highest performance score shown is 4.8, belonging to Ira Sharma.

Example generated SQL:
SELECT employee_name, performance_score
FROM uploaded_data
ORDER BY performance_score DESC
LIMIT 1;
The exact result depends on the contents of the dataset you upload.

Other example questions for employee_performance.csv:
- What is the average performance score for each department?
- Who has the highest monthly salary?
- Show the top 5 employees by tasks completed.
- Which employees have attendance above 95%?
- What is the total monthly salary for each department?
How It Works
1. The user selects the MySQL workflow or uploads a CSV/XLSX file.
2. QueryWise AI previews the uploaded data and saves the dataset locally.
3. The user submits a natural-language question.
4. The AI-assisted workflow generates a SQL query.
5. The backend validates the query before execution.
6. For uploaded datasets, the validated query runs against the data using DuckDB.
7. The frontend displays the query results and generated SQL.
AI requests may be affected by provider quota limits, rate limits, or network availability.
Security and Limitations
- Do not commit .env files or real credentials.
- Keep uploaded datasets and local database files out of Git.
- Use least-privilege database credentials.
- Validate SQL before execution and allow only the operations and tables intended by the application.
- Uploaded files are stored locally in the backend data directory.
- This project is configured for local development. Add authentication, authorization, deployment configuration, and additional production safeguards before exposing it publicly.
- Natural-language query generation depends on the configured Gemini API and may be affected by its quota or availability.
Future Enhancements
- Add a Gemini-independent direct SQL mode for uploaded datasets.
- Make suggested example questions adapt to the selected dataset.
- Add query history and saved queries.
- Expand charts and visualization options.
- Add authentication and authorization for multi-user use.
- Add production deployment, monitoring, and further integration tests.
Author
Shreya V K
Computer Science and Engineering | Python Full Stack Development
- GitHub: Shreyavk28
- LinkedIn: Shreya VK
QueryWise AI — Turn your data into insights.