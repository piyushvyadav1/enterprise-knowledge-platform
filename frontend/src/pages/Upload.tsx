import { useState, type FormEvent } from "react";

import {
  FileText,
  UploadCloud,
} from "lucide-react";

import api from "../services/api";
import { useAuth } from "../context/AuthContext";

export default function Upload() {
  const { user } = useAuth();

  // =====================================================
  // FORM STATE
  // =====================================================

  const [name, setName] = useState("");
  const [department, setDepartment] = useState("");
  const [version, setVersion] = useState("1.0");
  const [accessLevel, setAccessLevel] = useState("department");
  const [file, setFile] = useState<File | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // =====================================================
  // ONLY ADMIN CAN UPLOAD
  // =====================================================

  const isAdmin = user?.role === "admin";

  // =====================================================
  // SUBMIT
  // =====================================================

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!isAdmin) {
      setError(
        "You do not have permission to upload documents."
      );
      return;
    }

    if (!file) {
      setError("Please select a PDF document.");
      return;
    }

    if (file.type !== "application/pdf") {
      setError("Only PDF documents are allowed.");
      return;
    }

    if (file.size > 20 * 1024 * 1024) {
      setError("The PDF must be smaller than 20 MB.");
      return;
    }

    if (!name.trim()) {
      setError("Please enter a document name.");
      return;
    }

    if (!department.trim()) {
      setError("Please enter a department.");
      return;
    }

    if (!version.trim()) {
      setError("Please enter a version.");
      return;
    }

    const allowedAccessLevels = [
      "public",
      "department",
      "company-wide",
      "private",
    ];

    if (!allowedAccessLevels.includes(accessLevel)) {
      setError("Invalid document access level.");
      return;
    }

    const formData = new FormData();

    formData.append("name", name.trim());
    formData.append("department", department.trim());
    formData.append("version", version.trim());
    formData.append("access_level", accessLevel);
    formData.append("file", file);

    try {
      setLoading(true);

      await api.post(
        "/documents/upload",
        formData
      );

      setSuccess(
        "Document uploaded successfully."
      );

      setName("");
      setDepartment("");
      setVersion("1.0");
      setAccessLevel("department");
      setFile(null);

      const fileInput =
        document.getElementById(
          "document-file"
        ) as HTMLInputElement | null;

      if (fileInput) {
        fileInput.value = "";
      }
    } catch (error: any) {
      console.error("UPLOAD ERROR:", error);

      setError(
        error?.response?.data?.detail ||
          "Document upload failed."
      );
    } finally {
      setLoading(false);
    }
  };

  // =====================================================
  // NON-ADMIN VIEW
  // =====================================================

  if (!isAdmin) {
    return (
      <div>
        <div className="page-heading">
          <h1>Upload Document</h1>

          <p>
            You do not have permission to upload
            documents. Only administrators can
            upload enterprise documents.
          </p>
        </div>
      </div>
    );
  }

  // =====================================================
  // ADMIN UPLOAD UI
  // =====================================================

  return (
    <div>
      <div className="page-heading">
        <h1>Upload Document</h1>

        <p>
          Add enterprise knowledge to the
          platform.
        </p>
      </div>

      <div className="upload-panel">
        <form onSubmit={handleSubmit}>
          <label>
            Document Name
          </label>

          <input
            value={name}
            onChange={(event) =>
              setName(event.target.value)
            }
            placeholder="Enter document name"
            required
          />

          <label>
            Department
          </label>

          <input
            value={department}
            onChange={(event) =>
              setDepartment(event.target.value)
            }
            placeholder="e.g. HR, Sales, Marketing, Finance"
            required
          />

          <label>
            Version
          </label>

          <input
            value={version}
            onChange={(event) =>
              setVersion(event.target.value)
            }
            placeholder="1.0"
            required
          />

          <label>
            Document Access
          </label>

          <select
            value={accessLevel}
            onChange={(event) =>
              setAccessLevel(event.target.value)
            }
          >
            <option value="public">
              Public
            </option>

            <option value="department">
              Department Only
            </option>

            <option value="company-wide">
              Company Wide
            </option>

            <option value="private">
              Private
            </option>
          </select>

          <small>
            {accessLevel === "public" &&
              "Accessible to all authenticated enterprise users."}

            {accessLevel === "department" &&
              "Only users in the selected department can access it."}

            {accessLevel === "company-wide" &&
              "Accessible across the enterprise."}

            {accessLevel === "private" &&
              "Only the document owner or uploader can access it."}
          </small>

          <label>
            PDF Document
          </label>

          <label className="file-drop">
            {file ? (
              <>
                <FileText size={30} />

                <strong>
                  {file.name}
                </strong>
              </>
            ) : (
              <>
                <UploadCloud size={34} />

                <strong>
                  Select PDF document
                </strong>

                <span>
                  Maximum size: 20 MB
                </span>
              </>
            )}

            <input
              id="document-file"
              type="file"
              accept="application/pdf,.pdf"
              onChange={(event) => {
                const selectedFile =
                  event.target.files?.[0] ??
                  null;

                setFile(selectedFile);
                setError("");
                setSuccess("");
              }}
            />
          </label>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {success && (
            <div className="success-message">
              {success}
            </div>
          )}

          <button
            type="submit"
            className="primary-button"
            disabled={loading}
          >
            {loading
              ? "Uploading..."
              : "Upload Document"}
          </button>
        </form>
      </div>
    </div>
  );
}