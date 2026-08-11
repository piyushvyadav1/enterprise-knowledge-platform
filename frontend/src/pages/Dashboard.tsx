import {
  useEffect,
  useMemo,
  CSSProperties,
  useState,
} from "react";

import {
  Bot,
  CheckCircle2,
  FileText,
  RefreshCw,
  Upload,
  Clock3,
  ArrowRight,
  ShieldCheck,
  Search,
  Users,
} from "lucide-react";

import { useAuth } from "../context/AuthContext";
import api from "../services/api";

interface KnowledgeDocument {
  id: number;
  name: string;
  status: string;
  uploaded_at: string;
}

export default function Dashboard() {
  const { user } = useAuth();

  const [documents, setDocuments] =
    useState<KnowledgeDocument[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await api.get<KnowledgeDocument[]>(
          "/documents/"
        );

      setDocuments(response.data);
    } catch (err: any) {
      console.error(
        "DASHBOARD LOAD ERROR:",
        err
      );

      setError(
        err.response?.data?.detail ||
          "Unable to load dashboard data."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const totalDocuments =
    documents.length;

  const approvedDocuments =
    documents.filter(
      (document) =>
        document.status.toLowerCase() ===
        "approved"
    ).length;

  const pendingDocuments =
    documents.filter((document) =>
      ["pending", "processing", "review"]
        .includes(
          document.status.toLowerCase()
        )
    ).length;

  const sevenDaysAgo = useMemo(() => {
    const date = new Date();
    date.setDate(date.getDate() - 7);
    return date;
  }, []);

  const recentUploads =
    documents.filter((document) => {
      const uploadedDate =
        new Date(document.uploaded_at);

      return uploadedDate >= sevenDaysAgo;
    }).length;

  const approvalRate =
    totalDocuments > 0
      ? Math.round(
          (approvedDocuments /
            totalDocuments) *
            100
        )
      : 0;

  const recentDocuments =
    [...documents]
      .sort(
        (a, b) =>
          new Date(b.uploaded_at).getTime() -
          new Date(a.uploaded_at).getTime()
      )
      .slice(0, 5);

  const role =
    user?.role?.toLowerCase() ||
    "employee";

  const isAdmin =
    role === "admin" ||
    role === "ceo";

  const roleLabel =
    role
      .split("_")
      .map(
        (part) =>
          part.charAt(0).toUpperCase() +
          part.slice(1)
      )
      .join(" ");

  const formatDate = (
    value: string
  ) => {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "Unknown date";
    }

    return date.toLocaleDateString(
      undefined,
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
      }
    );
  };

  return (
    <div className="dashboard-page">

      {/* =================================================
          HEADER
          ================================================= */}

      <div className="dashboard-header">

        <div>
          <div className="dashboard-eyebrow">
            Enterprise Knowledge Intelligence
          </div>

          <h1>
            Welcome back,{" "}
            {user?.name || "User"}
          </h1>

          <p>
            Monitor your knowledge base,
            discover trusted information,
            and use AI to find answers faster.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button dashboard-refresh"
          onClick={loadDashboard}
          disabled={loading}
        >
          <RefreshCw
            size={16}
            className={
              loading
                ? "dashboard-spin"
                : ""
            }
          />

          {loading
            ? "Refreshing..."
            : "Refresh"}
        </button>

      </div>


      {/* =================================================
          STATUS STRIP
          ================================================= */}

      <div className="dashboard-status-strip">

        <div className="dashboard-status-left">

          <span className="dashboard-online-dot" />

          <span>
            Knowledge platform operational
          </span>

        </div>

        <span className="dashboard-role">
          {roleLabel}
        </span>

      </div>


      {/* =================================================
          ERROR
          ================================================= */}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}


      {/* =================================================
          KPI CARDS
          ================================================= */}

      <div className="dashboard-kpi-grid">

        <div className="dashboard-kpi-card">

          <div className="dashboard-kpi-icon blue">
            <FileText size={19} />
          </div>

          <div>
            <span>
              Total Documents
            </span>

            <strong>
              {loading
                ? "..."
                : totalDocuments}
            </strong>

            <small>
              Knowledge base size
            </small>
          </div>

        </div>


        <div className="dashboard-kpi-card">

          <div className="dashboard-kpi-icon green">
            <CheckCircle2 size={19} />
          </div>

          <div>
            <span>
              Approved
            </span>

            <strong>
              {loading
                ? "..."
                : approvedDocuments}
            </strong>

            <small>
              Trusted documents
            </small>
          </div>

        </div>


        <div className="dashboard-kpi-card">

          <div className="dashboard-kpi-icon purple">
            <Upload size={19} />
          </div>

          <div>
            <span>
              Recent Uploads
            </span>

            <strong>
              {loading
                ? "..."
                : recentUploads}
            </strong>

            <small>
              Last 7 days
            </small>
          </div>

        </div>


        <div className="dashboard-kpi-card">

          <div className="dashboard-kpi-icon orange">
            <ShieldCheck size={19} />
          </div>

          <div>
            <span>
              Approval Rate
            </span>

            <strong>
              {loading
                ? "..."
                : `${approvalRate}%`}
            </strong>

            <small>
              Knowledge quality
            </small>
          </div>

        </div>

      </div>


      {/* =================================================
          MAIN GRID
          ================================================= */}

      <div className="dashboard-main-grid">

        {/* KNOWLEDGE HEALTH */}

        <section className="dashboard-card dashboard-health-card">

          <div className="dashboard-card-heading">

            <div>
              <h2>
                Knowledge Health
              </h2>

              <p>
                Current state of your
                enterprise knowledge base.
              </p>
            </div>

            <ShieldCheck
              size={20}
            />

          </div>


          <div className="knowledge-health">

           <div
            className="knowledge-health-ring"
            style={
              {
                "--approval": approvalRate,
              } as React.CSSProperties
            }
          >

              <div>
                <strong>
                  {loading
                    ? "..."
                    : `${approvalRate}%`}
                </strong>

                <span>
                  approved
                </span>
              </div>

            </div>

            <div className="health-details">

              <div className="health-row">
                <span>
                  <i className="health-dot approved" />
                  Approved
                </span>

                <strong>
                  {approvedDocuments}
                </strong>
              </div>

              <div className="health-row">
                <span>
                  <i className="health-dot pending" />
                  Pending / Review
                </span>

                <strong>
                  {pendingDocuments}
                </strong>
              </div>

              <div className="health-row">
                <span>
                  <i className="health-dot total" />
                  Total
                </span>

                <strong>
                  {totalDocuments}
                </strong>
              </div>

            </div>

          </div>

        </section>


        {/* QUICK ACTIONS */}

        <section className="dashboard-card">

          <div className="dashboard-card-heading">

            <div>
              <h2>
                Quick Actions
              </h2>

              <p>
                Jump directly into common
                knowledge tasks.
              </p>
            </div>

            <ArrowRight size={20} />

          </div>


          <div className="dashboard-actions">

            <a
              href="/chat"
              className="dashboard-action"
            >
              <div className="dashboard-action-icon">
                <Bot size={18} />
              </div>

              <div>
                <strong>
                  Ask AI
                </strong>

                <span>
                  Search trusted enterprise
                  knowledge.
                </span>
              </div>

              <ArrowRight size={16} />
            </a>


            {isAdmin && (
              <a
                href="/upload"
                className="dashboard-action"
              >
                <div className="dashboard-action-icon">
                  <Upload size={18} />
                </div>

                <div>
                  <strong>
                    Upload Document
                  </strong>

                  <span>
                    Add knowledge to the
                    enterprise repository.
                  </span>
                </div>

                <ArrowRight size={16} />
              </a>
            )}


            <a
              href="/documents"
              className="dashboard-action"
            >
              <div className="dashboard-action-icon">
                <Search size={18} />
              </div>

              <div>
                <strong>
                  Browse Documents
                </strong>

                <span>
                  Explore documents you
                  can access.
                </span>
              </div>

              <ArrowRight size={16} />
            </a>


            {isAdmin && (
              <a
                href="/users"
                className="dashboard-action"
              >
                <div className="dashboard-action-icon">
                  <Users size={18} />
                </div>

                <div>
                  <strong>
                    Manage Users
                  </strong>

                  <span>
                    Manage enterprise users
                    and access.
                  </span>
                </div>

                <ArrowRight size={16} />
              </a>
            )}

          </div>

        </section>

      </div>


      {/* =================================================
          RECENT DOCUMENTS
          ================================================= */}

      <section className="dashboard-card dashboard-recent-card">

        <div className="dashboard-card-heading">

          <div>
            <h2>
              Recent Knowledge
            </h2>

            <p>
              Recently uploaded documents
              in the knowledge repository.
            </p>
          </div>

          <a
            href="/documents"
            className="dashboard-view-link"
          >
            View all
            <ArrowRight size={15} />
          </a>

        </div>


        {loading ? (

          <div className="dashboard-empty">
            <RefreshCw
              size={18}
              className="dashboard-spin"
            />

            <span>
              Loading recent knowledge...
            </span>
          </div>

        ) : recentDocuments.length === 0 ? (

          <div className="dashboard-empty">

            <FileText size={22} />

            <div>
              <strong>
                No documents yet
              </strong>

              <span>
                Your enterprise knowledge
                repository is ready.
              </span>
            </div>

          </div>

        ) : (

          <div className="dashboard-document-list">

            {recentDocuments.map(
              (document) => {

                const approved =
                  document.status
                    .toLowerCase() ===
                  "approved";

                return (
                  <div
                    className="dashboard-document-row"
                    key={document.id}
                  >

                    <div className="dashboard-document-icon">
                      <FileText
                        size={17}
                      />
                    </div>

                    <div className="dashboard-document-info">

                      <strong
                        title={
                          document.name
                        }
                      >
                        {document.name}
                      </strong>

                      <span>
                        <Clock3
                          size={12}
                        />

                        {formatDate(
                          document.uploaded_at
                        )}
                      </span>

                    </div>

                    <span
                      className={
                        approved
                          ? "dashboard-doc-status approved"
                          : "dashboard-doc-status"
                      }
                    >
                      {document.status}
                    </span>

                  </div>
                );
              }
            )}

          </div>

        )}

      </section>


      {/* =================================================
          AI BANNER
          ================================================= */}

      <section className="dashboard-ai-banner">

        <div className="dashboard-ai-icon">
          <Bot size={25} />
        </div>

        <div className="dashboard-ai-content">

          <span>
            KNOWLEDGE ASSISTANT
          </span>

          <h2>
            Have a question about
            company knowledge?
          </h2>

          <p>
            Ask the local AI assistant and
            receive answers grounded in
            approved enterprise documents.
          </p>

        </div>

        <a
          href="/chat"
          className="dashboard-ai-button"
        >
          Ask the AI
          <ArrowRight size={16} />
        </a>

      </section>

    </div>
  );
}