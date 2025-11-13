import React, { useCallback, useEffect, useMemo, useState } from "react";
import { API_BASE_URL, API_TOKEN } from "./config";
import {
  HealthResponse,
  KnowledgeItemRow,
  KnowledgeListResponse,
  QueueMetrics,
} from "./types";

const STATUS_FILTERS = [
  { label: "All", value: "all" },
  { label: "Pending", value: "pending" },
  { label: "Processing", value: "processing" },
  { label: "Ready", value: "ready_for_distillation" },
  { label: "Errors", value: "error" },
];

const STATUS_OPTIONS = [
  { label: "Pending", value: "pending" },
  { label: "Processing", value: "processing" },
  { label: "Ready for Distillation", value: "ready_for_distillation" },
  { label: "Error", value: "error" },
];

async function fetchJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: HeadersInit = {
    ...(options.headers || {}),
    ...(API_TOKEN ? { "X-Console-Token": API_TOKEN } : {}),
  };
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

function formatDate(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

function statusBadge(status: string) {
  const normalized = status.toLowerCase();
  const label = normalized.replace(/_/g, " ");
  return (
    <span className={`badge badge-${normalized.replace(/[^a-z]/g, "-")}`}>
      {label}
    </span>
  );
}

type ViewMode = "dashboard" | "knowledge";

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [metrics, setMetrics] = useState<QueueMetrics | null>(null);
  const [knowledge, setKnowledge] = useState<KnowledgeListResponse | null>(null);
  const [selectedItem, setSelectedItem] = useState<KnowledgeItemRow | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [statusFilter, setStatusFilter] = useState("error");
  const [view, setView] = useState<ViewMode>("dashboard");
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [knowledgeLoading, setKnowledgeLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [editFields, setEditFields] = useState({
    title: "",
    status: "pending",
    last_error: "",
  });
  const [isSaving, setIsSaving] = useState(false);
  const [editMessage, setEditMessage] = useState<string | null>(null);

  const refreshDashboard = useCallback(async () => {
    setDashboardLoading(true);
    setError(null);
    try {
      const [healthData, metricsData, logsData] = await Promise.all([
        fetchJson<HealthResponse>("/health"),
        fetchJson<QueueMetrics>("/metrics"),
        fetchJson<{ lines: string[] }>("/logs?lines=150"),
      ]);
      setHealth(healthData);
      setMetrics(metricsData);
      setLogs(logsData.lines ?? []);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setDashboardLoading(false);
    }
  }, []);

  const refreshKnowledge = useCallback(async () => {
    setKnowledgeLoading(true);
    setError(null);
    try {
      const endpoint =
        statusFilter === "all"
          ? "/knowledge-items?limit=50"
          : `/knowledge-items?status=${statusFilter}&limit=50`;
      const knowledgeData = await fetchJson<KnowledgeListResponse>(endpoint);
      setKnowledge(knowledgeData);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load knowledge items");
    } finally {
      setKnowledgeLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    if (view === "dashboard") {
      refreshDashboard();
    } else {
      refreshKnowledge();
    }
  }, [view, refreshDashboard, refreshKnowledge]);

  useEffect(() => {
    if (knowledge?.items?.length) {
      setSelectedItem((current) => {
        if (!current) {
          return knowledge.items[0];
        }
        return knowledge.items.find((item) => item.id === current.id) ?? knowledge.items[0];
      });
    } else {
      setSelectedItem(null);
    }
  }, [knowledge]);
  useEffect(() => {
    if (selectedItem) {
      setEditFields({
        title: selectedItem.title ?? "",
        status: selectedItem.status,
        last_error: selectedItem.last_error ?? "",
      });
    } else {
      setEditFields({
        title: "",
        status: "pending",
        last_error: "",
      });
    }
    setEditMessage(null);
  }, [selectedItem]);

  const handleRetry = async (itemId: string) => {
    try {
      await fetchJson(`/knowledge-items/${itemId}/retry`, {
        method: "POST",
      });
      await refreshKnowledge();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to retry knowledge item"
      );
    }
  };

  const handleFieldChange =
    (field: "title" | "status" | "last_error") =>
    (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
      const value = event.target.value;
      setEditFields((prev) => ({ ...prev, [field]: value }));
    };

  const resetEditFields = () => {
    if (!selectedItem) return;
    setEditFields({
      title: selectedItem.title ?? "",
      status: selectedItem.status,
      last_error: selectedItem.last_error ?? "",
    });
    setEditMessage(null);
    setError(null);
  };

  const handleSaveEdits = async () => {
    if (!selectedItem) {
      return;
    }
    setIsSaving(true);
    setEditMessage(null);
    try {
      await fetchJson(`/knowledge-items/${selectedItem.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(editFields),
      });
      await refreshKnowledge();
      setEditMessage("Saved changes.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to save knowledge item"
      );
    } finally {
      setIsSaving(false);
    }
  };

  const queueSummary = useMemo(() => {
    if (!metrics) return null;
    const pendingTotal = Object.values(metrics.queued_tasks).reduce(
      (sum, count) => sum + count,
      0
    );
    return { pendingTotal };
  }, [metrics]);

  const knowledgeItems = knowledge?.items ?? [];
  const isDashboard = view === "dashboard";
  const currentLoading = isDashboard ? dashboardLoading : knowledgeLoading;
  const handleRefresh = isDashboard ? refreshDashboard : refreshKnowledge;

  const handleViewChange = (next: ViewMode) => {
    if (view === next) return;
    setError(null);
    setView(next);
  };

  return (
    <div className="app-shell">
      <header>
        <h1>Backend Service Console</h1>
        <p>Operational overview of Synapse capture services.</p>
        <div className="top-nav">
          <button
            className={isDashboard ? "active" : ""}
            onClick={() => handleViewChange("dashboard")}
          >
            Dashboard
          </button>
          <button
            className={!isDashboard ? "active" : ""}
            onClick={() => handleViewChange("knowledge")}
          >
            Knowledge Items
          </button>
        </div>
        <div className="actions">
          <button onClick={handleRefresh} disabled={currentLoading}>
            {currentLoading ? "Refreshing..." : "Refresh"}
          </button>
          {lastUpdated && (
            <span className="secondary">Last updated: {lastUpdated}</span>
          )}
        </div>
        {error && (
          <div className="card" style={{ border: "1px solid #f87171" }}>
            <strong>Error:</strong> {error}
          </div>
        )}
      </header>

      {isDashboard ? (
        <>
          <section className="card">
            <h2>Service Health</h2>
            <div className="grid cols-3">
              {health &&
                Object.entries(health.components).map(([name, status]) => (
                  <div key={name}>
                    <h3>{name}</h3>
                    <p className={`status-${status.status}`}>
                      {status.status.toUpperCase()}
                    </p>
                    {status.detail && <small>{status.detail}</small>}
                  </div>
                ))}
            </div>
          </section>

          <section className="card">
            <h2>Queue & Worker Metrics</h2>
            {metrics && queueSummary && (
              <>
                <p>Queued tasks: {queueSummary.pendingTotal}</p>
                <div className="grid cols-3">
                  {metrics.workers.map((worker) => (
                    <div key={worker.name}>
                      <strong>{worker.name}</strong>
                      <p>PID: {worker.pid}</p>
                      <p>Active: {metrics.active_tasks[worker.name] ?? 0}</p>
                      <p>
                        Processed:{" "}
                        {Object.values(worker.processed).reduce(
                          (sum, val) => sum + val,
                          0
                        )}
                      </p>
                    </div>
                  ))}
                </div>
              </>
            )}
          </section>

          <section className="card">
            <h2>Recent Logs</h2>
            <div className="logs">
              {logs.length === 0 && <p>No log entries yet.</p>}
              {logs.map((line, index) => (
                <div key={`${line}-${index}`}>{line}</div>
              ))}
            </div>
          </section>
        </>
      ) : (
        <section className="knowledge-section">
          <div className="card knowledge-controls">
            <div className="filter-buttons">
              {STATUS_FILTERS.map((option) => (
                <button
                  key={option.value}
                  className={statusFilter === option.value ? "active" : ""}
                  onClick={() => setStatusFilter(option.value)}
                >
                  {option.label}
                </button>
              ))}
            </div>
            {knowledgeLoading && <p className="helper-text">Loading knowledge items…</p>}
          </div>
          <div className="knowledge-layout">
            <div className="card knowledge-table-card">
              <table className="table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Status</th>
                    <th>Source</th>
                    <th>Last Error</th>
                    <th>Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {knowledgeItems.map((item) => (
                    <tr
                      key={item.id}
                      className={selectedItem?.id === item.id ? "selected" : ""}
                      onClick={() => setSelectedItem(item)}
                    >
                      <td>{item.id.slice(0, 8)}</td>
                      <td>{statusBadge(item.status)}</td>
                      <td>
                        <span className="pill">{item.source_type}</span>
                      </td>
                      <td>
                        {item.last_error ? (
                          <span className="error-text">
                            {item.last_error.slice(0, 60)}
                            {item.last_error.length > 60 ? "…" : ""}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td>{formatDate(item.processed_at || item.created_at)}</td>
                    </tr>
                  ))}
                  {!knowledgeItems.length && !knowledgeLoading && (
                    <tr>
                      <td colSpan={5}>No knowledge items match this filter.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="card knowledge-detail-card">
              <h3>Knowledge Item Details</h3>
              {selectedItem ? (
                <>
                  <div className="detail-form">
                    <label>
                      <span>Title</span>
                      <input
                        type="text"
                        value={editFields.title}
                        onChange={handleFieldChange("title")}
                        placeholder="Enter title"
                      />
                    </label>
                    <label>
                      <span>Status</span>
                      <select value={editFields.status} onChange={handleFieldChange("status")}>
                        {STATUS_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      <span>Last Error</span>
                      <textarea
                        value={editFields.last_error}
                        onChange={handleFieldChange("last_error")}
                        placeholder="Add error context"
                        rows={3}
                      />
                    </label>
                  </div>
                  <div className="detail-actions">
                    <button onClick={handleSaveEdits} disabled={isSaving}>
                      {isSaving ? "Saving…" : "Save Changes"}
                    </button>
                    <button className="secondary" type="button" onClick={resetEditFields}>
                      Reset
                    </button>
                    <button
                      className="ghost"
                      type="button"
                      onClick={() => handleRetry(selectedItem.id)}
                    >
                      Retry Capture
                    </button>
                  </div>
                  {editMessage && <p className="success-text">{editMessage}</p>}
                  <div className="detail-grid">
                    <p>
                      <strong>Title:</strong> {selectedItem.title ?? "Untitled"}
                    </p>
                    <p>
                      <strong>Status:</strong> {statusBadge(selectedItem.status)}
                    </p>
                    <p>
                      <strong>Source:</strong> {selectedItem.source_type}
                    </p>
                    <p>
                      <strong>Source URL:</strong>{" "}
                      {selectedItem.source_url ? (
                        <a href={selectedItem.source_url} target="_blank" rel="noreferrer">
                          {selectedItem.source_url}
                        </a>
                      ) : (
                        "—"
                      )}
                    </p>
                    <p>
                      <strong>Created:</strong> {formatDate(selectedItem.created_at)}
                    </p>
                    <p>
                      <strong>Processed:</strong> {formatDate(selectedItem.processed_at)}
                    </p>
                    <p>
                      <strong>Transcript:</strong>{" "}
                      {selectedItem.has_transcript ? (
                        <span className="pill success">Available</span>
                      ) : (
                        <span className="pill muted">Not available</span>
                      )}
                    </p>
                    <p>
                      <strong>Last Error:</strong> {selectedItem.last_error ?? "None"}
                    </p>
                  </div>
                  {selectedItem.last_error && (
                    <div className="error-panel">
                      <strong>Latest Error</strong>
                      <pre>{selectedItem.last_error}</pre>
                    </div>
                  )}
                  <div className="detail-actions">
                    <button onClick={() => handleRetry(selectedItem.id)}>Retry capture</button>
                  </div>
                </>
              ) : (
                <p>Select a knowledge item to view details and retry options.</p>
              )}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
