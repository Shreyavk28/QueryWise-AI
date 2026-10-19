# QueryWise AI

**AI-Powered Data Analytics | Natural Language to SQL**

QueryWise AI is a web-based data analytics application that allows users to ask business questions in plain English and view query results from a MySQL database or uploaded CSV/Excel datasets. It uses AI-assisted SQL generation, query validation, and DuckDB to analyze uploaded datasets and present results in an interactive dashboard.

## Features

- **Natural Language Querying:** Ask questions about business data in plain English.
- **MySQL Integration:** Query structured data stored in a MySQL database.
- **CSV and Excel Uploads:** Upload CSV or XLSX files up to 5 MB.
- **Dataset Management:** View, select, preview, and delete saved datasets.
- **SQL Validation:** Validate SQL queries before execution and restrict queries to read-only operations.
- **DuckDB Integration:** Execute validated SQL queries against uploaded datasets.
- **Interactive Dashboard:** View query results in tables and supported charts.
- **Generated SQL Preview:** Inspect the SQL generated for a question.
- **Persistent Dataset Storage:** Keep uploaded datasets available across backend restarts.
- **REST API:** FastAPI endpoints with interactive Swagger documentation.
- **Error Handling:** Handle invalid requests and query-processing errors.

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

### Database and Testing
- MySQL
- Pytest
- Swagger UI / OpenAPI

### Development Tools
- Git
- GitHub
- Visual Studio Code

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
│   ├── .env
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

*This is a simplified project structure. Additional files and directories may exist in the repository.*

## Prerequisites

Install the following before running the application:

- Python 3.10 or later
- Node.js and npm
- MySQL Server for the MySQL workflow
- A Google Gemini API key for AI-powered natural-language query generation

## Installation and Setup

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd "QueryWise AI"
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your actual GitHub repository URL.

### 2. Set Up the Backend

Open a terminal in the project root and run:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If the virtual environment is already created, activate it and install any missing dependencies.

### 3. Configure Environment Variables

Create a `.env` file inside the `backend` directory using `.env.example` as a template.

Configure the environment variables required by your backend code. The following is an example; use the exact variable names expected by your implementation.

```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_NAME=querywise_db
DB_USER=your_database_user
DB_PASSWORD=your_database_password
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_configured_model
```

**Important:** Never commit your actual `.env` file, database password, API key, or other secrets to GitHub. Keep placeholder values in `.env.example`.

### 4. Configure MySQL

For the MySQL workflow, start your MySQL server and create the database if it does not already exist.

```sql
CREATE DATABASE querywise_db;
```

Configure the required tables and a database account with only the permissions needed by the application. Update the database connection settings in `backend/.env`.

MySQL configuration is required for the MySQL workflow. You can use the uploaded-dataset workflow to analyze CSV/XLSX files.

### 5. Start the Backend

From the `backend` directory, activate your virtual environment and run:

```powershell
python -m uvicorn app.main:app --reload
```

The backend should be available at:

- **API Base URL:** http://127.0.0.1:8000
- **Swagger UI:** http://127.0.0.1:8000/docs
- **Health Check:** http://127.0.0.1:8000/api/health

Keep the backend terminal running.

### 6. Start the Frontend

Open a second terminal and navigate to the frontend directory.

```powershell
cd "D:\ALL PROJECTS\QueryWise AI\frontend"
npm install
npm run dev
```

Open the local URL printed by Vite, usually:

http://localhost:5173

If the project is installed in another location, change the directory path accordingly.

## API Endpoints

The backend currently provides the following endpoints.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Check backend health |
| GET | `/api/db-health` | Check MySQL connectivity |
| GET | `/api/datasets` | List saved uploaded datasets |
| POST | `/api/upload` | Upload and save a CSV/XLSX dataset |
| DELETE | `/api/upload/{dataset_id}` | Delete a saved uploaded dataset |
| POST | `/api/ask` | Ask a natural-language question about MySQL data |
| POST | `/api/upload/ask` | Ask a question about a saved uploaded dataset |

Interactive API documentation, request schemas, and responses are available at:

http://127.0.0.1:8000/docs

## How to Use QueryWise AI

1. Start the backend and frontend.
2. Open QueryWise AI in your browser.
3. Select the MySQL workflow or choose an uploaded dataset.
4. Upload a CSV/XLSX file if needed.
5. Preview the dataset and review its columns.
6. Enter a question in plain English.
7. Submit the question and wait for processing.
8. Review the query results and generated SQL.
9. Select another saved dataset or delete datasets you no longer need.

## Example: Employee Performance Analysis

Select `employee_performance.csv` and ask:

**Question:**

> Who has the highest performance score?

**Example result from the sample dataset:**

| Employee Name | Performance Score |
|---|---:|
| Ira Sharma | 4.8 |

**Generated SQL:**

```sql
SELECT employee_name, performance_score
FROM uploaded_data
ORDER BY performance_score DESC
LIMIT 1;
```

The result is based on the sample employee dataset and may differ for other uploaded files.

### More Example Questions

For `employee_performance.csv`:

- What is the average performance score for each department?
- Who has the highest monthly salary?
- Show the top 5 employees by tasks completed.
- Which employees have attendance above 95%?
- What is the total monthly salary for each department?
- Count the number of employees in each department.
- Show employees with performance scores above 4.5.

For `retail_orders.csv`:

- What is the total revenue for each region?
- Which product generated the highest revenue?
- What is the average order value?
- Show total sales by product category.

For `sample_sales.csv`:

- What is the total revenue for each product?
- Which product has the highest unit price?
- Show the total quantity sold for each product.

The questions should match the columns in the currently selected dataset.

## How It Works

1. The user selects a MySQL workflow or uploads a CSV/XLSX file.
2. QueryWise AI validates and saves uploaded data locally.
3. The user submits a natural-language question.
4. The AI-assisted workflow generates a SQL query.
5. The backend validates the query before execution.
6. For uploaded datasets, validated SQL is executed against the data using DuckDB.
7. Query results and generated SQL are returned to the frontend.
8. The dashboard displays the results for analysis.

## Security and Limitations

- Environment variables are used for sensitive configuration.
- `.env` files, virtual environments, frontend dependencies, and local uploaded datasets should be excluded from Git.
- SQL queries are validated before execution.
- Use database credentials with the minimum permissions required.
- Uploaded datasets are stored locally in the backend data directory.
- AI query generation depends on the configured Gemini API and may be affected by rate limits, quota restrictions, or service availability.
- This project is intended for local development. Authentication, authorization, and additional production safeguards should be added before exposing it publicly.

## Future Enhancements

- Add a Gemini-independent direct SQL mode for uploaded datasets.
- Display example questions dynamically based on the selected dataset.
- Add query history and saved queries.
- Expand chart and visualization options.
- Add authentication and authorization for multiple users.
- Improve integration testing and production deployment support.

## Author

**Shreya V K**

Computer Science and Engineering | Python Full Stack Development

- GitHub: [Shreyavk28](https://github.com/Shreyavk28)
- LinkedIn: [Shreya VK](https://linkedin.com/in/shreya-vk-softwareengineer)

---

**QueryWise AI — Turn your data into insights.**
