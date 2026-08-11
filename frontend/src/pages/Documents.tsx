import { useEffect, useState } from "react";

import {
  CheckCircle2,
  Eye,
  FileText,
  RefreshCw,
  Search,
  Trash2,
  XCircle,
  Play,
  Database,
} from "lucide-react";

import api from "../services/api";
import { useAuth } from "../context/AuthContext";


// ============================================================
// DOCUMENT TYPE
// ============================================================

interface KnowledgeDocument {
  id: number;

  name: string;

  original_filename: string;

  department: string;

  version: string;

  status: string;

  file_size: number;

  page_count: number | null;

  uploaded_by: number;

  uploaded_at: string;

  processing_status?: string;

  indexing_status?: string;

  chunk_count?: number;

  indexed_chunk_count?: number;
}


// ============================================================
// COMPONENT
// ============================================================

export default function Documents() {

  const { user } = useAuth();

  // ============================================================
  // STATE
  // ============================================================

  const [documents, setDocuments] =
    useState<KnowledgeDocument[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [search, setSearch] =
    useState("");

  const [deletingId, setDeletingId] =
    useState<number | null>(null);

  const [actionId, setActionId] =
    useState<number | null>(null);

  const [readingId, setReadingId] =
    useState<number | null>(null);


  // ============================================================
  // PERMISSIONS
  // ============================================================

  const isAdmin =
    user?.role === "admin";

  const canManageProcessing =
    user?.role === "admin" ||
    user?.role === "knowledge_manager";

  const canReview =
    user?.role === "admin" ||
    user?.role === "knowledge_manager";

  const canDelete =
    user?.role === "admin";


  // ============================================================
  // LOAD DOCUMENTS
  // ============================================================

  const loadDocuments = async () => {

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
        "LOAD DOCUMENTS ERROR:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "Unable to load documents."
      );

    } finally {

      setLoading(false);

    }
  };


  // ============================================================
  // INITIAL LOAD
  // ============================================================

  useEffect(() => {

    loadDocuments();

  }, []);


  // ============================================================
  // READ DOCUMENT
  // ============================================================

  const readDocument = async (
    document: KnowledgeDocument
  ) => {

    let pdfWindow: Window | null = null;

    try {

      setReadingId(document.id);
      setError("");

      pdfWindow =
        window.open(
          "",
          "_blank"
        );

      if (!pdfWindow) {

        setError(
          "Unable to open the document. Please allow pop-ups."
        );

        setReadingId(null);

        return;
      }


      pdfWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Opening document...</title>

          <style>
            body {
              margin: 0;
              height: 100vh;
              display: flex;
              align-items: center;
              justify-content: center;
              font-family: Arial, sans-serif;
              background: #f8fafc;
              color: #334155;
            }

            .loading {
              text-align: center;
            }

            .spinner {
              width: 36px;
              height: 36px;
              margin: 0 auto 16px;
              border: 4px solid #e2e8f0;
              border-top-color: #2563eb;
              border-radius: 50%;
              animation: spin 0.8s linear infinite;
            }

            @keyframes spin {
              to {
                transform: rotate(360deg);
              }
            }
          </style>
        </head>

        <body>

          <div class="loading">

            <div class="spinner"></div>

            <div>
              Opening document...
            </div>

          </div>

        </body>
        </html>
      `);


      const response =
        await api.get(
          `/documents/${document.id}/file`,
          {
            responseType: "blob",
          }
        );


      const pdfBlob =
        new Blob(
          [response.data],
          {
            type: "application/pdf",
          }
        );


      const pdfUrl =
        URL.createObjectURL(
          pdfBlob
        );


      pdfWindow.location.href =
        pdfUrl;


      setTimeout(() => {

        URL.revokeObjectURL(
          pdfUrl
        );

      }, 60000);

    } catch (err: any) {

      console.error(
        "READ DOCUMENT ERROR:",
        err
      );

      if (
        pdfWindow &&
        !pdfWindow.closed
      ) {

        pdfWindow.close();

      }

      let message =
        "Unable to open this document.";

      if (err.response?.data) {

        try {

          if (
            err.response.data instanceof Blob
          ) {

            const text =
              await err.response.data.text();

            const parsed =
              JSON.parse(text);

            message =
              parsed.detail ||
              message;

          } else {

            message =
              err.response.data.detail ||
              message;

          }

        } catch {

          message =
            "Unable to open this document.";

        }

      }

      setError(message);

    } finally {

      setReadingId(null);

    }
  };


  // ============================================================
  // PROCESS DOCUMENT
  // ============================================================

  const processDocument = async (
    document: KnowledgeDocument
  ) => {

    const confirmed =
      window.confirm(
        `Process "${document.name}"?\n\n` +
        "The PDF will be extracted and converted into searchable knowledge chunks."
      );

    if (!confirmed) {
      return;
    }


    try {

      setActionId(document.id);
      setError("");


      /*
       * Mark processing immediately in UI.
       */

      setDocuments(
        current =>
          current.map(
            item =>
              item.id === document.id
                ? {
                    ...item,
                    processing_status:
                      "processing",
                  }
                : item
          )
      );


      await api.post(
        `/documents/${document.id}/process`
      );


      /*
       * Reload from backend so we get:
       *
       * processing_status
       * chunk_count
       * etc.
       */

      await loadDocuments();


    } catch (err: any) {

      console.error(
        "PROCESS DOCUMENT ERROR:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "Unable to process document."
      );

      await loadDocuments();

    } finally {

      setActionId(null);

    }
  };


  // ============================================================
  // INDEX DOCUMENT
  // ============================================================

  const indexDocument = async (
    document: KnowledgeDocument
  ) => {

    if (
      document.processing_status !==
      "processed"
    ) {

      setError(
        "Document must be processed before indexing."
      );

      return;
    }


    const confirmed =
      window.confirm(
        `Index "${document.name}"?\n\n` +
        "The processed document will be added to the AI search index."
      );

    if (!confirmed) {
      return;
    }


    try {

      setActionId(document.id);
      setError("");


      /*
       * Mark indexing immediately.
       */

      setDocuments(
        current =>
          current.map(
            item =>
              item.id === document.id
                ? {
                    ...item,
                    indexing_status:
                      "indexing",
                  }
                : item
          )
      );


      await api.post(
        `/documents/${document.id}/index`
      );


      /*
       * Reload backend data.
       */

      await loadDocuments();


    } catch (err: any) {

      console.error(
        "INDEX DOCUMENT ERROR:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "Unable to index document."
      );

      await loadDocuments();

    } finally {

      setActionId(null);

    }
  };


  // ============================================================
  // APPROVE
  // ============================================================

  const approveDocument = async (
    document: KnowledgeDocument
  ) => {

    const confirmed =
      window.confirm(
        `Approve "${document.name}"?\n\n` +
        "This document will become trusted enterprise knowledge."
      );

    if (!confirmed) {
      return;
    }


    try {

      setActionId(document.id);
      setError("");


      await api.patch(
        `/documents/${document.id}/approve`
      );


      await loadDocuments();


    } catch (err: any) {

      console.error(
        "APPROVE ERROR:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "Unable to approve document."
      );

    } finally {

      setActionId(null);

    }
  };


  // ============================================================
  // REJECT
  // ============================================================

  const rejectDocument = async (
    document: KnowledgeDocument
  ) => {

    const confirmed =
      window.confirm(
        `Reject "${document.name}"?\n\n` +
        "Rejected documents will not be treated as trusted knowledge."
      );

    if (!confirmed) {
      return;
    }


    try {

      setActionId(document.id);
      setError("");


      await api.patch(
        `/documents/${document.id}/reject`
      );


      await loadDocuments();


    } catch (err: any) {

      console.error(
        "REJECT ERROR:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "Unable to reject document."
      );

    } finally {

      setActionId(null);

    }
  };


  // ============================================================
  // DELETE
  // ============================================================

  const deleteDocument = async (
    document: KnowledgeDocument
  ) => {

    const confirmed =
      window.confirm(
        `Are you sure you want to delete "${document.name}"?\n\n` +
        "This will permanently remove the PDF and its metadata."
      );

    if (!confirmed) {
      return;
    }


    try {

      setDeletingId(document.id);
      setError("");


      await api.delete(
        `/documents/${document.id}`
      );


      setDocuments(
        current =>
          current.filter(
            item =>
              item.id !== document.id
          )
      );


    } catch (err: any) {

      console.error(
        "DELETE ERROR:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "Unable to delete document."
      );

    } finally {

      setDeletingId(null);

    }
  };


  // ============================================================
  // SEARCH
  // ============================================================

  const filteredDocuments =
    documents.filter(
      document => {

        const query =
          search
            .trim()
            .toLowerCase();

        if (!query) {
          return true;
        }

        return (

          document.name
            .toLowerCase()
            .includes(query)

          ||

          document.department
            .toLowerCase()
            .includes(query)

          ||

          document.original_filename
            .toLowerCase()
            .includes(query)

          ||

          document.version
            .toLowerCase()
            .includes(query)

          ||

          document.status
            .toLowerCase()
            .includes(query)

          ||

          (
            document.processing_status ||
            ""
          )
            .toLowerCase()
            .includes(query)

          ||

          (
            document.indexing_status ||
            ""
          )
            .toLowerCase()
            .includes(query)

        );

      }
    );


  // ============================================================
  // FORMAT SIZE
  // ============================================================

  const formatSize = (
    bytes: number
  ) => {

    if (bytes < 1024) {
      return `${bytes} B`;
    }

    if (
      bytes <
      1024 * 1024
    ) {

      return `${(
        bytes / 1024
      ).toFixed(1)} KB`;

    }

    return `${(
      bytes /
      (1024 * 1024)
    ).toFixed(1)} MB`;
  };


  // ============================================================
  // FORMAT DATE
  // ============================================================

  const formatDate = (
    date: string
  ) => {

    return new Date(
      date
    ).toLocaleDateString();

  };


  // ============================================================
  // FORMAT STATUS
  // ============================================================

  const formatStatus = (
    value?: string
  ) => {

    if (!value) {
      return "Pending";
    }

    return (
      value.charAt(0).toUpperCase() +
      value.slice(1)
    );

  };


  // ============================================================
  // UI
  // ============================================================

  return (

    <div>

      {/* ========================================================
          HEADER
          ======================================================== */}

      <div className="document-header">

        <div className="page-heading">

          <h1>
            Document Library
          </h1>

          <p>
            Browse, read, review and manage
            enterprise knowledge documents.
          </p>

        </div>


        <button
          type="button"
          className="secondary-button"
          onClick={loadDocuments}
          disabled={loading}
        >

          <RefreshCw size={17} />

          {loading
            ? "Loading..."
            : "Refresh"}

        </button>

      </div>


      {/* ========================================================
          SEARCH
          ======================================================== */}

      <div className="document-toolbar">

        <Search size={19} />

        <input
          type="text"
          placeholder="Search documents..."
          value={search}
          onChange={
            event =>
              setSearch(
                event.target.value
              )
          }
        />

      </div>


      {/* ========================================================
          ERROR
          ======================================================== */}

      {error && (

        <div className="error-message">
          {error}
        </div>

      )}


      {/* ========================================================
          LOADING
          ======================================================== */}

      {loading ? (

        <div className="empty-state">

          <RefreshCw size={36} />

          <h3>
            Loading documents
          </h3>

          <p>
            Retrieving enterprise knowledge documents.
          </p>

        </div>

      ) : filteredDocuments.length === 0 ? (

        <div className="empty-state">

          <FileText size={40} />

          <h3>

            {search
              ? "No matching documents"
              : "No documents found"}

          </h3>

          <p>

            {search
              ? "Try a different search."
              : "Upload enterprise documents to start building your knowledge base."}

          </p>

        </div>

      ) : (

        /* ========================================================
           TABLE
           ======================================================== */

        <div className="document-table-wrapper">

          <table className="document-table">

            <thead>

              <tr>

                <th>
                  Document
                </th>

                <th>
                  Department
                </th>

                <th>
                  Version
                </th>

                <th>
                  Status
                </th>

                <th>
                  Processing
                </th>

                <th>
                  Indexing
                </th>

                <th>
                  Pages
                </th>

                <th>
                  Size
                </th>

                <th>
                  Uploaded
                </th>

                <th>
                  Actions
                </th>

              </tr>

            </thead>


            <tbody>

              {filteredDocuments.map(
                document => {

                  const actionRunning =
                    actionId ===
                    document.id;

                  const deleting =
                    deletingId ===
                    document.id;

                  const reading =
                    readingId ===
                    document.id;


                  const processing =
                    document.processing_status ===
                    "processing";


                  const processed =
                    document.processing_status ===
                    "processed";


                  const processingFailed =
                    document.processing_status ===
                    "failed";


                  const indexing =
                    document.indexing_status ===
                    "indexing";


                  const indexed =
                    document.indexing_status ===
                    "indexed";


                  return (

                    <tr
                      key={document.id}
                    >

                      {/* DOCUMENT */}

                      <td>

                        <div className="document-name">

                          <div className="pdf-icon">

                            <FileText
                              size={19}
                            />

                          </div>


                          <div>

                            <strong>
                              {document.name}
                            </strong>

                            <span>
                              {
                                document.original_filename
                              }
                            </span>

                          </div>

                        </div>

                      </td>


                      {/* DEPARTMENT */}

                      <td>
                        {document.department}
                      </td>


                      {/* VERSION */}

                      <td>
                        v{document.version}
                      </td>


                      {/* STATUS */}

                      <td>

                        <span
                          className={
                            `status-badge ${document.status.toLowerCase()}`
                          }
                        >

                          {formatStatus(
                            document.status
                          )}

                        </span>

                      </td>


                      {/* PROCESSING */}

                      <td>

                        <span
                          className={
                            `status-badge ${
                              document.processing_status ||
                              "pending"
                            }`
                          }
                        >

                          {formatStatus(
                            document.processing_status
                          )}

                        </span>

                      </td>


                      {/* INDEXING */}

                      <td>

                        <span
                          className={
                            `status-badge ${
                              document.indexing_status ||
                              "pending"
                            }`
                          }
                        >

                          {formatStatus(
                            document.indexing_status
                          )}

                        </span>

                      </td>


                      {/* PAGES */}

                      <td>
                        {document.page_count ?? "—"}
                      </td>


                      {/* SIZE */}

                      <td>
                        {formatSize(
                          document.file_size
                        )}
                      </td>


                      {/* DATE */}

                      <td>
                        {formatDate(
                          document.uploaded_at
                        )}
                      </td>


                      {/* ACTIONS */}

                      <td>

                        <div className="document-actions">


                          {/* ==================================================
                              READ
                              ================================================== */}

                          <button
                            type="button"
                            className="read-button"
                            onClick={() =>
                              readDocument(
                                document
                              )
                            }
                            disabled={
                              reading ||
                              deleting ||
                              actionRunning
                            }
                            title="Read document"
                          >

                            <Eye size={16} />

                            {reading
                              ? "Opening..."
                              : "Read"}

                          </button>


                          {/* ==================================================
                              PROCESS
                              ADMIN + KNOWLEDGE MANAGER
                              ================================================== */}

                          {canManageProcessing && (

                            <button
                              type="button"
                              className="process-button"
                              onClick={() =>
                                processDocument(
                                  document
                                )
                              }
                              disabled={
                                actionRunning ||
                                deleting ||
                                reading ||
                                processing ||
                                indexed
                              }
                              title={
                                indexed
                                  ? "Document already indexed"
                                  : processed
                                    ? "Document already processed"
                                    : "Process document"
                              }
                            >

                              <Play size={16} />

                              {processing
                                ? "Processing..."
                                : processed
                                  ? "Processed"
                                  : processingFailed
                                    ? "Retry Process"
                                    : "Process"}

                            </button>

                          )}


                          {/* ==================================================
                              INDEX
                              ADMIN + KNOWLEDGE MANAGER
                              ================================================== */}

                          {canManageProcessing && (

                            <button
                              type="button"
                              className="index-button"
                              onClick={() =>
                                indexDocument(
                                  document
                                )
                              }
                              disabled={
                                actionRunning ||
                                deleting ||
                                reading ||
                                indexing ||
                                !processed ||
                                indexed
                              }
                              title={
                                !processed
                                  ? "Process the document first"
                                  : indexed
                                    ? "Document already indexed"
                                    : "Index document"
                              }
                            >

                              <Database size={16} />

                              {indexing
                                ? "Indexing..."
                                : indexed
                                  ? "Indexed"
                                  : "Index"}

                            </button>

                          )}


                          {/* ==================================================
                              APPROVE
                              ================================================== */}

                          {canReview &&
                            document.status !==
                              "approved" && (

                            <button
                              type="button"
                              className="approve-button"
                              onClick={() =>
                                approveDocument(
                                  document
                                )
                              }
                              disabled={
                                actionRunning ||
                                deleting ||
                                reading ||
                                !processed ||
                                !indexed
                              }
                              title={
                                !processed
                                  ? "Process document first"
                                  : !indexed
                                    ? "Index document first"
                                    : "Approve document"
                              }
                            >

                              <CheckCircle2
                                size={16}
                              />

                              Approve

                            </button>

                          )}


                          {/* ==================================================
                              REJECT
                              ================================================== */}

                          {canReview &&
                            document.status !==
                              "rejected" && (

                            <button
                              type="button"
                              className="reject-button"
                              onClick={() =>
                                rejectDocument(
                                  document
                                )
                              }
                              disabled={
                                actionRunning ||
                                deleting ||
                                reading
                              }
                              title="Reject document"
                            >

                              <XCircle
                                size={16}
                              />

                              Reject

                            </button>

                          )}


                          {/* ==================================================
                              DELETE
                              ADMIN ONLY
                              ================================================== */}

                          {canDelete && (

                            <button
                              type="button"
                              className="delete-button"
                              onClick={() =>
                                deleteDocument(
                                  document
                                )
                              }
                              disabled={
                                deleting ||
                                actionRunning ||
                                reading
                              }
                              title="Delete document"
                            >

                              <Trash2
                                size={16}
                              />

                              {deleting
                                ? "Deleting..."
                                : "Delete"}

                            </button>

                          )}

                        </div>

                      </td>

                    </tr>

                  );

                }
              )}

            </tbody>

          </table>

        </div>

      )}

    </div>

  );
}