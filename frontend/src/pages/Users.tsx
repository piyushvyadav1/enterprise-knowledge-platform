import { useEffect, useState, type FormEvent } from "react";
import axios from "axios";

interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  department: string;
  is_active: boolean;
}

const API_URL = "http://127.0.0.1:8000/api/v1";

const ROLE_OPTIONS = [
  { value: "employee", label: "Employee" },
  { value: "tl", label: "Team Leader" },
  { value: "hr", label: "HR" },
  { value: "ceo", label: "CEO" },
  { value: "knowledge_manager", label: "Knowledge Manager" },
  { value: "admin", label: "Admin" },
];

const DEPARTMENT_OPTIONS = [
  "General",
  "HR",
  "Sales",
  "Marketing",
  "Finance",
  "IT",
  "Operations",
];

export default function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [registering, setRegistering] = useState(false);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showRegister, setShowRegister] = useState(false);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("employee");
  const [department, setDepartment] = useState("General");

  const getAuthConfig = () => ({
    headers: {
      Authorization: `Bearer ${localStorage.getItem("access_token")}`,
    },
  });

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await axios.get(
        `${API_URL}/users/`,
        getAuthConfig()
      );

      setUsers(response.data);
    } catch (err: any) {
      console.error(err);
      setError(
        err?.response?.data?.detail || "Unable to load users."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const resetRegisterForm = () => {
    setName("");
    setEmail("");
    setPassword("");
    setRole("employee");
    setDepartment("General");
  };

  const registerUser = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (name.trim().length < 2) {
      setError("Name must contain at least 2 characters.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    try {
      setRegistering(true);

      const response = await axios.post(
        `${API_URL}/users/`,
        {
          name: name.trim(),
          email: email.trim().toLowerCase(),
          password,
          role,
          department,
        },
        getAuthConfig()
      );

      setUsers((current) => [...current, response.data]);
      setSuccess(`User "${response.data.name}" was registered successfully.`);
      resetRegisterForm();
      setShowRegister(false);
    } catch (err: any) {
      console.error(err);
      setError(
        err?.response?.data?.detail || "Unable to register user."
      );
    } finally {
      setRegistering(false);
    }
  };

  const changeRole = async (userId: number, newRole: string) => {
    const currentUser = users.find((user) => user.id === userId);
    if (!currentUser || currentUser.role === newRole) return;

    try {
      setUpdatingId(userId);
      setError("");
      setSuccess("");

      const response = await axios.patch(
        `${API_URL}/users/${userId}/role`,
        { role: newRole },
        getAuthConfig()
      );

      setUsers((current) =>
        current.map((user) =>
          user.id === userId
            ? { ...user, role: response.data.role }
            : user
        )
      );

      setSuccess(`Role updated for ${currentUser.name}.`);
    } catch (err: any) {
      console.error(err);
      setError(
        err?.response?.data?.detail || "Role update failed."
      );
      await loadUsers();
    } finally {
      setUpdatingId(null);
    }
  };

  const changeDepartment = async (
    userId: number,
    newDepartment: string
  ) => {
    const currentUser = users.find((user) => user.id === userId);
    if (!currentUser || currentUser.department === newDepartment) return;

    try {
      setUpdatingId(userId);
      setError("");
      setSuccess("");

      const response = await axios.patch(
        `${API_URL}/users/${userId}/department`,
        { department: newDepartment },
        getAuthConfig()
      );

      setUsers((current) =>
        current.map((user) =>
          user.id === userId
            ? {
                ...user,
                department: response.data.department,
              }
            : user
        )
      );

      setSuccess(`Department updated for ${currentUser.name}.`);
    } catch (err: any) {
      console.error(err);
      setError(
        err?.response?.data?.detail ||
          "Department update failed."
      );
      await loadUsers();
    } finally {
      setUpdatingId(null);
    }
  };

  const toggleUser = async (userId: number, active: boolean) => {
    const currentUser = users.find((user) => user.id === userId);
    if (!currentUser) return;

    try {
      setUpdatingId(userId);
      setError("");
      setSuccess("");

      const response = await axios.patch(
        `${API_URL}/users/${userId}/status`,
        { is_active: active },
        getAuthConfig()
      );

      setUsers((current) =>
        current.map((user) =>
          user.id === userId
            ? { ...user, is_active: response.data.is_active }
            : user
        )
      );

      setSuccess(
        active
          ? `${currentUser.name} has been resumed.`
          : `${currentUser.name} has been paused.`
      );
    } catch (err: any) {
      console.error(err);
      setError(
        err?.response?.data?.detail ||
          "Unable to change user status."
      );
      await loadUsers();
    } finally {
      setUpdatingId(null);
    }
  };

  const deleteUser = async (user: User) => {
    const confirmed = window.confirm(
      `Delete "${user.name}" permanently?\n\nThis cannot be undone.`
    );

    if (!confirmed) return;

    try {
      setUpdatingId(user.id);
      setError("");
      setSuccess("");

      await axios.delete(
        `${API_URL}/users/${user.id}`,
        getAuthConfig()
      );

      setUsers((current) =>
        current.filter((item) => item.id !== user.id)
      );

      setSuccess(`${user.name} was deleted.`);
    } catch (err: any) {
      console.error(err);
      setError(
        err?.response?.data?.detail ||
          "Unable to delete user."
      );
    } finally {
      setUpdatingId(null);
    }
  };

  const formatRole = (value: string) =>
    value
      .split("_")
      .map(
        (word) =>
          word.charAt(0).toUpperCase() + word.slice(1)
      )
      .join(" ");

  if (loading) {
    return (
      <div className="users-page">
        <h1>User Management</h1>
        <p>Loading users...</p>
      </div>
    );
  }

  return (
    <div className="users-page">
      <div className="users-header">
        <div>
          <h1>User Management</h1>
          <p>Register users and manage enterprise access.</p>
        </div>

        <button
          type="button"
          className="primary-button"
          onClick={() => {
            setShowRegister((value) => !value);
            setError("");
            setSuccess("");
          }}
        >
          {showRegister ? "Close Registration" : "Register User"}
        </button>
      </div>

      {error && <div className="users-error">{error}</div>}
      {success && <div className="users-success">{success}</div>}

      {showRegister && (
        <div className="register-user-panel">
          <h2>Register New User</h2>

          <form onSubmit={registerUser}>
            <label htmlFor="user-name">Full Name</label>
            <input
              id="user-name"
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Enter full name"
              required
            />

            <label htmlFor="user-email">Email</label>
            <input
              id="user-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="user@company.com"
              required
            />

            <label htmlFor="user-password">Password</label>
            <input
              id="user-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Minimum 8 characters"
              minLength={8}
              required
            />

            <label htmlFor="user-role">Role</label>
            <select
              id="user-role"
              value={role}
              onChange={(event) => setRole(event.target.value)}
            >
              {ROLE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            <label htmlFor="user-department">Department</label>
            <select
              id="user-department"
              value={department}
              onChange={(event) => setDepartment(event.target.value)}
            >
              {DEPARTMENT_OPTIONS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>

            <div>
              <button
                type="submit"
                className="primary-button"
                disabled={registering}
              >
                {registering ? "Creating User..." : "Create User"}
              </button>

              <button
                type="button"
                className="secondary-button"
                disabled={registering}
                onClick={() => {
                  resetRegisterForm();
                  setShowRegister(false);
                }}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="users-table-wrapper">
        <table className="users-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Email</th>
              <th>Department</th>
              <th>Current Role</th>
              <th>Change Role</th>
              <th>Change Department</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            {users.map((user) => {
              const busy = updatingId === user.id;

              return (
                <tr key={user.id}>
                  <td>
                    <div className="user-name">{user.name}</div>
                    <div className="user-id">User #{user.id}</div>
                  </td>

                  <td>{user.email}</td>

                  <td>
                    <strong>{user.department || "General"}</strong>
                  </td>

                  <td>
                    <span className={`role-badge role-${user.role}`}>
                      {formatRole(user.role)}
                    </span>
                  </td>

                  <td>
                    <select
                      className="role-select"
                      value={user.role}
                      disabled={busy}
                      onChange={(event) =>
                        changeRole(user.id, event.target.value)
                      }
                    >
                      {ROLE_OPTIONS.map((option) => (
                        <option
                          key={option.value}
                          value={option.value}
                        >
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </td>

                  <td>
                    <select
                      className="department-select"
                      value={user.department || "General"}
                      disabled={busy}
                      onChange={(event) =>
                        changeDepartment(
                          user.id,
                          event.target.value
                        )
                      }
                    >
                      {DEPARTMENT_OPTIONS.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                  </td>

                  <td>
                    <span
                      className={
                        user.is_active
                          ? "status-active"
                          : "status-paused"
                      }
                    >
                      {user.is_active ? "Active" : "Paused"}
                    </span>
                  </td>

                  <td>
                    <div className="user-actions">
                      <button
                        type="button"
                        className="secondary-button"
                        disabled={busy}
                        onClick={() =>
                          toggleUser(
                            user.id,
                            !user.is_active
                          )
                        }
                      >
                        {user.is_active ? "Pause" : "Resume"}
                      </button>

                      <button
                        type="button"
                        className="danger-button"
                        disabled={busy}
                        onClick={() => deleteUser(user)}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {users.length === 0 && (
          <div className="empty-users">No users found.</div>
        )}
      </div>
    </div>
  );
}