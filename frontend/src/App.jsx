
import { useEffect, useState } from "react";
import {
  BarChart3,
  BrainCircuit,
  ChevronDown,
  CircleHelp,
  Code2,
  Database,
  FileSpreadsheet,
  LoaderCircle,
  MessageSquare,
  Send,
  Sparkles,
  Table2,
  TrendingUp,
  Trash2,
  Upload,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./App.css";

const API_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const examples = [
  "Which products have the highest total sales revenue?",
  "Show total quantity sold for each product",
  "Which product has the highest unit price?",
  "Show all products in the Electronics category",
];

const inrFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

function formatCurrency(value) {
  const number = Number(value);

  if (
    value === null ||
    value === undefined ||
    value === "" ||
    !Number.isFinite(number)
  ) {
    return "—";
  }

  return inrFormatter.format(number);
}

function formatValue(value, column = "") {
  if (value === null || value === undefined) return "—";

  if (/revenue|sales/i.test(column)) {
    return formatCurrency(value);
  }

  if (
    typeof value === "number" ||
    (typeof value === "string" && /^-?\d+(\.\d+)?$/.test(value))
  ) {
    return Number(value).toLocaleString("en-IN", {
      maximumFractionDigits: 2,
    });
  }

  return String(value);
}

function App() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("results");
  const [showSql, setShowSql] = useState(true);

  const [dataset, setDataset] = useState(null);
  const [savedDatasets, setSavedDatasets] = useState([]);
  const [datasetsLoading, setDatasetsLoading] = useState(true);
  const [datasetListError, setDatasetListError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [datasetMessage, setDatasetMessage] = useState("");
  const [deleting, setDeleting] = useState(false);

  async function loadSavedDatasets() {
    setDatasetsLoading(true);
    setDatasetListError("");

    try {
      const response = await fetch(`${API_URL}/api/datasets`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Unable to load saved datasets."
        );
      }

      const items = Array.isArray(data.datasets) ? data.datasets : [];
      setSavedDatasets(items);

      // Keep the selected dataset synchronized with its persisted copy.
      setDataset((current) => {
        if (!current) return current;
        return items.find((item) => item.dataset_id === current.dataset_id) || null;
      });
    } catch (err) {
      setDatasetListError(
        err.message === "Failed to fetch"
          ? "Cannot load saved datasets. Check that the backend is running."
          : err.message || "Unable to load saved datasets."
      );
    } finally {
      setDatasetsLoading(false);
    }
  }

  useEffect(() => {
    loadSavedDatasets();
  }, []);

  function selectSavedDataset(savedDataset) {
    if (loading || uploading || deleting) return;

    setDataset(savedDataset);
    setQuestion("");
    setResult(null);
    setError("");
    setUploadError("");
    setDatasetMessage("");
    setActiveTab("results");
  }

  async function uploadDataset(event) {
    const input = event.target;
    const file = input.files?.[0];

    // Allow selecting the same file again later.
    input.value = "";

    if (!file) return;

    const extension = file.name.split(".").pop()?.toLowerCase();

    if (!["csv", "xlsx"].includes(extension)) {
      setUploadError("Please select a CSV or XLSX file.");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setUploadError("File size must not exceed 5 MB.");
      return;
    }

    setUploading(true);
    setUploadError("");
    setDatasetMessage("");
    setError("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_URL}/api/upload`, {
        method: "POST",
        body: formData,
      });

      let data;

      try {
        data = await response.json();
      } catch {
        throw new Error("The server returned an invalid response.");
      }

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Unable to upload this file."
        );
      }

      if (
        !data.dataset_id ||
        !Array.isArray(data.columns) ||
        !Array.isArray(data.rows)
      ) {
        throw new Error("The server returned an invalid upload response.");
      }

      setDataset(data);
      await loadSavedDatasets();
      setDatasetMessage("Dataset uploaded and saved on this computer.");
      setQuestion("");
      setResult(null);
      setActiveTab("results");
    } catch (err) {
      setUploadError(
        err.message === "Failed to fetch"
          ? "Cannot connect to the backend. Make sure FastAPI is running at http://127.0.0.1:8000."
          : err.message || "Upload failed. Please try again."
      );
    } finally {
      setUploading(false);
    }
  }

  async function askQuestion(value = question) {
    const cleanQuestion = value.trim();

    if (!cleanQuestion || loading || uploading || deleting) return;

    setQuestion(cleanQuestion);
    setLoading(true);
    setError("");
    setResult(null);
    setActiveTab("results");

    try {
      const endpoint = dataset
        ? `${API_URL}/api/upload/ask`
        : `${API_URL}/api/ask`;

      const requestBody = dataset
        ? {
            question: cleanQuestion,
            dataset_id: dataset.dataset_id,
          }
        : {
            question: cleanQuestion,
          };

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      let data;

      try {
        data = await response.json();
      } catch {
        throw new Error(
          "The server returned an invalid response. Please try again."
        );
      }

      if (!response.ok) {
        const detail =
          typeof data.detail === "string"
            ? data.detail
            : "Unable to process your question.";

        if (response.status === 429) {
          throw new Error(
            dataset
              ? "Gemini is temporarily rate-limiting requests. Your uploaded dataset is still saved. Please wait a little and try again."
              : detail ||
                "Gemini API rate limit or quota reached. Please wait before trying again."
          );
        }

        throw new Error(detail);
      }

      if (!Array.isArray(data.columns) || !Array.isArray(data.rows)) {
        throw new Error("The server response is missing query results.");
      }

      setResult({
        ...data,
        source: dataset ? "upload" : "mysql",
      });
    } catch (err) {
      const message = err.message || "";

      if (
        message === "Failed to fetch" ||
        message.includes("NetworkError")
      ) {
        setError(
          "Cannot connect to the backend. Make sure FastAPI is running at http://127.0.0.1:8000."
        );
      } else {
        setError(message || "Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  async function deleteDataset() {
    if (!dataset || loading || uploading || deleting) return;

    const confirmed = window.confirm(
      `Permanently delete ${dataset.filename} from this computer? This cannot be undone.`
    );
    if (!confirmed) return;

    setDeleting(true);
    setUploadError("");
    setDatasetMessage("");
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/api/upload/${encodeURIComponent(dataset.dataset_id)}`,
        { method: "DELETE" }
      );

      let data = {};
      try {
        data = await response.json();
      } catch {
        // The API may return an empty response body.
      }

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Unable to delete this dataset."
        );
      }

      setDataset(null);
      setResult(null);
      setQuestion("");
      setActiveTab("results");
      await loadSavedDatasets();
      setDatasetMessage("Dataset permanently deleted.");
    } catch (err) {
      setUploadError(
        err.message === "Failed to fetch"
          ? "Cannot connect to the backend. Make sure FastAPI is running at http://127.0.0.1:8000."
          : err.message || "Unable to delete this dataset. Please try again."
      );
    } finally {
      setDeleting(false);
    }
  }

  function clearDataset() {
    if (loading || uploading || deleting) return;

    setDataset(null);
    setResult(null);
    setError("");
    setUploadError("");
    setDatasetMessage("");
    setQuestion("");
    setActiveTab("results");
  }

  const revenueColumn = result?.columns?.find((column) =>
    /revenue|sales/i.test(column)
  );

  const labelColumn =
    result?.columns?.find((column) =>
      /product_name|product|category|name/i.test(column)
    ) || result?.columns?.[0];

  const chartData =
    result?.rows?.map((row) => ({
      name: String(row[labelColumn] ?? "Result"),
      value: Number(row[revenueColumn]),
    })) || [];

  const hasChart =
    Boolean(revenueColumn) &&
    chartData.length > 0 &&
    chartData.every((item) => Number.isFinite(item.value));

  const totalRevenue = hasChart
    ? chartData.reduce((sum, item) => sum + item.value, 0)
    : null;

  const resultSourceLabel = result?.filename
    ? result.filename
    : result?.source === "upload"
      ? "uploaded dataset"
      : "MySQL";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#home">
          <span className="brand-icon">
            <BrainCircuit size={24} />
          </span>
          <span>
            <strong>QueryWise</strong>
            <small>AI ANALYTICS</small>
          </span>
        </a>

        <div className="workspace-label">WORKSPACE</div>

        <button className="nav-item active">
          <MessageSquare size={18} />
          <span>Ask your data</span>
        </button>

        <div className="sidebar-section">
          <div className="workspace-label">YOUR DATA</div>

          <button
            type="button"
            className={`connection-item sidebar-data-item ${
              !dataset ? "data-item-selected" : ""
            }`}
            onClick={clearDataset}
            disabled={loading || uploading || deleting}
          >
            <span className="database-icon">
              <Database size={17} />
            </span>
            <span className="sidebar-dataset-label">
              <strong>querywise_db</strong>
              <small>MySQL database</small>
            </span>
            {!dataset && <span className="status-dot" />}
          </button>

          {datasetsLoading && (
            <p className="sidebar-data-message">Loading saved datasets...</p>
          )}

          {datasetListError && (
            <p className="sidebar-data-error" role="alert">
              {datasetListError}
              <button type="button" onClick={loadSavedDatasets}>
                Retry
              </button>
            </p>
          )}

          {!datasetsLoading && !datasetListError && savedDatasets.length === 0 && (
            <p className="sidebar-data-message">No uploaded datasets yet.</p>
          )}

          {savedDatasets.map((savedDataset) => (
            <button
              type="button"
              key={savedDataset.dataset_id}
              className={`connection-item sidebar-data-item ${
                dataset?.dataset_id === savedDataset.dataset_id
                  ? "data-item-selected"
                  : ""
              }`}
              onClick={() => selectSavedDataset(savedDataset)}
              disabled={loading || uploading || deleting}
              title={`Select ${savedDataset.filename}`}
            >
              <span className="database-icon">
                <FileSpreadsheet size={17} />
              </span>
              <span className="sidebar-dataset-label">
                <strong>{savedDataset.filename}</strong>
                <small>
                  {savedDataset.row_count} rows · {savedDataset.column_count} columns
                </small>
              </span>
              {dataset?.dataset_id === savedDataset.dataset_id && (
                <span className="status-dot" />
              )}
            </button>
          ))}
        </div>

        <div className="sidebar-bottom">
          <div className="security-note">
            <span className="security-icon">
              <Database size={17} />
            </span>
            <strong>Read-only queries</strong>
            <p>
              SQL queries are validated before execution against your data.
            </p>
          </div>

          <div className="sidebar-footer">
            <span className="avatar">Q</span>
            <span>
              <strong>QueryWise AI</strong>
              <small>Natural language to SQL</small>
            </span>
          </div>
        </div>
      </aside>

      <main className="main-content" id="home">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span> <strong>Ask your data</strong>
          </div>
          <div className="topbar-status">
            <span className="status-dot" />
            <span>API workspace</span>
          </div>
        </header>

        <section className="content">
          <div className="welcome">
            <div className="eyebrow">
              <Sparkles size={15} />
              YOUR AI DATA ANALYST
            </div>
            <h1>
              Make your data <span>talk.</span>
            </h1>
            <p>
              Ask business questions in plain English. Get SQL, results, and
              insights from your database or uploaded file.
            </p>
          </div>

          <section className="question-card">
            <label htmlFor="question-input">
              What would you like to know?
            </label>
            <textarea
              id="question-input"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  askQuestion();
                }
              }}
              placeholder={
                dataset
                  ? `Ask a question about ${dataset.filename}...`
                  : "e.g. Which products generated the most revenue?"
              }
              maxLength={500}
              rows={3}
              disabled={loading || uploading || deleting}
            />

            <div className="question-actions">
              <span className="input-hint">
                <CircleHelp size={14} />
                Enter to ask · Shift + Enter for a new line
              </span>
              <button
                className="ask-button"
                onClick={() => askQuestion()}
                disabled={loading || uploading || deleting || !question.trim()}
              >
                {loading ? (
                  <LoaderCircle className="spin" size={17} />
                ) : (
                  <Send size={16} />
                )}
                {loading ? "Analyzing..." : "Ask QueryWise"}
              </button>
            </div>
          </section>

          <section className="upload-card">
            <div className="upload-card-heading">
              <div className="upload-icon">
                <FileSpreadsheet size={22} />
              </div>
              <div>
                <h3>Analyze your own dataset</h3>
                <p>Upload a CSV or Excel file to ask questions about its data.</p>
              </div>
            </div>

            <label
              className={`upload-dropzone ${uploading ? "upload-disabled" : ""}`}
            >
              {uploading ? (
                <LoaderCircle className="spin" size={22} />
              ) : (
                <Upload size={22} />
              )}
              <strong>
                {uploading ? "Uploading file..." : "Choose a CSV or XLSX file"}
              </strong>
              <span>Maximum file size: 5 MB</span>
              <input
                type="file"
                accept=".csv,.xlsx"
                onChange={uploadDataset}
                disabled={uploading || loading || deleting}
              />
            </label>

            {uploadError && (
              <p className="upload-error" role="alert">
                {uploadError}
              </p>
            )}

            {datasetMessage && (
              <p className="upload-success" role="status">
                {datasetMessage}
              </p>
            )}

            {dataset && (
              <div className="uploaded-dataset">
                <div className="uploaded-dataset-info">
                  <FileSpreadsheet size={20} />
                  <div>
                    <strong>{dataset.filename}</strong>
                    <span>
                      {dataset.row_count} rows · {dataset.column_count} columns
                    </span>
                  </div>
                </div>

                <div className="dataset-actions">
                  <button
                    type="button"
                    className="clear-dataset-button"
                    onClick={clearDataset}
                    disabled={loading || uploading || deleting}
                  >
                    Use MySQL instead
                  </button>
                  <button
                    type="button"
                    className="clear-dataset-button delete-dataset-button"
                    onClick={deleteDataset}
                    disabled={loading || uploading || deleting}
                  >
                    {deleting ? (
                      <LoaderCircle className="spin" size={15} />
                    ) : (
                      <Trash2 size={15} />
                    )}
                    {deleting ? "Deleting..." : "Delete dataset"}
                  </button>
                </div>

                <div className="dataset-preview">
                  <strong>Data preview</strong>
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          {dataset.columns.map((column) => (
                            <th key={column.name}>{column.name}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {dataset.rows.map((row, index) => (
                          <tr key={index}>
                            {dataset.columns.map((column) => (
                              <td key={column.name}>
                                {formatValue(row[column.name], column.name)}
                              </td>
                            ))}
                          </tr>
                        ))}
                        {dataset.rows.length === 0 && (
                          <tr>
                            <td colSpan={dataset.columns.length}>
                              No preview rows available.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </section>

          <section className="examples-section">
            <div className="section-heading">
              <span>TRY ASKING</span>
              <span className="suggestion-caption">
                {dataset ? "Example questions for your data" : "Example questions"}
              </span>
            </div>
            <div className="example-list">
              {examples.map((example) => (
                <button
                  className="example-chip"
                  key={example}
                  onClick={() => askQuestion(example)}
                  disabled={loading || uploading || deleting}
                >
                  <Sparkles size={14} />
                  {example}
                </button>
              ))}
            </div>
          </section>

          {loading && (
            <section className="state-card">
              <LoaderCircle className="spin" size={25} />
              <strong>Analyzing your question</strong>
              <p>Generating SQL and querying your data...</p>
            </section>
          )}

          {error && (
            <section className="error-card" role="alert">
              <strong>We couldn't answer that yet</strong>
              <p>{error}</p>
              <button
                className="retry-button"
                onClick={() => askQuestion()}
                disabled={loading}
              >
                Try again
              </button>
            </section>
          )}

          {result && !loading && (
            <section className="results-section">
              <div className="results-title">
                <div>
                  <div className="eyebrow">
                    <TrendingUp size={15} />
                    QUERY COMPLETE
                  </div>
                  <h2>Your results</h2>
                  <p>{result.question || question}</p>
                </div>
                <span className="success-pill">
                  <span className="status-dot" />
                  Success
                </span>
              </div>

              <div className="metric-grid">
                <div className="metric-card">
                  <div className="metric-top">
                    <span>Rows returned</span>
                    <Table2 size={18} />
                  </div>
                  <strong>
                    {Number(
                      result.row_count ?? result.rows.length
                    ).toLocaleString("en-IN")}
                  </strong>
                  <small>Matching records</small>
                </div>

                <div className="metric-card">
                  <div className="metric-top">
                    <span>Columns</span>
                    <Database size={18} />
                  </div>
                  <strong>{result.columns.length}</strong>
                  <small>Fields returned</small>
                </div>

                {totalRevenue !== null && (
                  <div className="metric-card">
                    <div className="metric-top">
                      <span>Total revenue</span>
                      <TrendingUp size={18} />
                    </div>
                    <strong>{formatCurrency(totalRevenue)}</strong>
                    <small>Sum of returned revenue values</small>
                  </div>
                )}
              </div>

              {hasChart && (
                <div className="panel chart-panel">
                  <div className="panel-heading">
                    <div>
                      <h3>Revenue by product</h3>
                      <p>Comparison from your query results</p>
                    </div>
                    <BarChart3 size={20} />
                  </div>
                  <div className="chart-container">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={chartData}
                        margin={{
                          top: 12,
                          right: 12,
                          left: 8,
                          bottom: 8,
                        }}
                      >
                        <CartesianGrid
                          strokeDasharray="3 3"
                          vertical={false}
                          stroke="#e8edf5"
                        />
                        <XAxis
                          dataKey="name"
                          tick={{ fill: "#64748b", fontSize: 12 }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <YAxis
                          tick={{ fill: "#64748b", fontSize: 11 }}
                          axisLine={false}
                          tickLine={false}
                          width={85}
                          tickFormatter={(value) =>
                            `₹${new Intl.NumberFormat("en-IN", {
                              notation: "compact",
                              maximumFractionDigits: 1,
                            }).format(value)}`
                          }
                        />
                        <Tooltip
                          formatter={(value) => [
                            formatCurrency(value),
                            "Revenue",
                          ]}
                          contentStyle={{
                            borderRadius: 10,
                            border: "1px solid #e2e8f0",
                          }}
                        />
                        <Bar
                          dataKey="value"
                          fill="#5368e8"
                          radius={[6, 6, 0, 0]}
                          maxBarSize={72}
                          activeBar={false}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              <div className="panel">
                <div className="panel-heading results-panel-heading">
                  <div>
                    <h3>Query results</h3>
                    <p>
                      {result.rows.length} records returned by {resultSourceLabel}
                    </p>
                  </div>
                  <div className="tab-switch">
                    <button
                      className={activeTab === "results" ? "selected" : ""}
                      onClick={() => setActiveTab("results")}
                    >
                      <Table2 size={15} /> Table
                    </button>
                    <button
                      className={activeTab === "json" ? "selected" : ""}
                      onClick={() => setActiveTab("json")}
                    >
                      <Code2 size={15} /> JSON
                    </button>
                  </div>
                </div>

                {activeTab === "results" ? (
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          {result.columns.map((column) => (
                            <th key={column}>
                              {column.replaceAll("_", " ")}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {result.rows.map((row, index) => (
                          <tr key={index}>
                            {result.columns.map((column) => (
                              <td key={column}>
                                {formatValue(row[column], column)}
                              </td>
                            ))}
                          </tr>
                        ))}
                        {result.rows.length === 0 && (
                          <tr>
                            <td colSpan={Math.max(result.columns.length, 1)}>
                              No matching records found.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <pre className="json-view">
                    {JSON.stringify(result.rows, null, 2)}
                  </pre>
                )}
              </div>

              <div className="panel sql-panel">
                <button
                  className="sql-toggle"
                  onClick={() => setShowSql(!showSql)}
                >
                  <span className="sql-heading">
                    <Code2 size={18} />
                    <span>
                      <strong>Generated SQL</strong>
                      <small>
                        Validated query executed against {resultSourceLabel}
                      </small>
                    </span>
                  </span>
                  <ChevronDown
                    size={18}
                    className={showSql ? "chevron-open" : ""}
                  />
                </button>
                {showSql && (
                  <pre className="sql-code">
                    <code>{result.sql}</code>
                  </pre>
                )}
              </div>
            </section>
          )}

          {!result && !loading && !error && (
            <div className="empty-state">
              <div className="empty-icon">
                <BarChart3 size={25} />
              </div>
              <strong>Your next insight starts here</strong>
              <p>
                Ask a question above to turn your business data into useful
                results.
              </p>
            </div>
          )}

          <footer className="page-footer">
            <span>QueryWise AI</span>
            <span>Natural language · SQL · Analytics</span>
          </footer>
        </section>
      </main>
    </div>
  );
}

export default App;
  