import {
  Bot,
  FileText,
  LayoutDashboard,
  LogOut,
  Upload,
  User,
  Users,
} from "lucide-react";

import {
  NavLink,
  Outlet,
} from "react-router-dom";

import { useAuth } from "../context/AuthContext";


export default function DashboardLayout() {

  const {
    user,
    logout,
  } = useAuth();


  return (
    <div className="app-shell">

      <aside className="sidebar">

        <div className="sidebar-brand">

          <div className="brand-mark">
            EK
          </div>

          <div>
            <strong>
              Knowledge AI
            </strong>

            <span>
              Enterprise Intelligence
            </span>
          </div>

        </div>


        <nav>

          <NavLink to="/dashboard">
            <LayoutDashboard size={19} />
            Dashboard
          </NavLink>

          <NavLink to="/documents">
            <FileText size={19} />
            Documents
          </NavLink>


          {(user?.role === "admin" ||
            user?.role === "knowledge_manager") && (

            <NavLink to="/upload">
              <Upload size={19} />
              Upload
            </NavLink>

          )}

          {user?.role === "admin" && (
            <NavLink to="/users">
              <Users size={19} />
              User Management
            </NavLink>
          )}


          <NavLink to="/chat">
            <Bot size={19} />
            AI Chat
          </NavLink>

          <NavLink to="/profile">
            <User size={19} />
            Profile
          </NavLink>

        </nav>


        <div className="sidebar-user">

          <div>

            <strong>
              {user?.name}
            </strong>

            <span>
              {user?.role
                .replace("_", " ")}
            </span>

          </div>


          <button onClick={logout}>
            <LogOut size={18} />
          </button>

        </div>

      </aside>


      <main className="main-content">
        <Outlet />
      </main>

    </div>
  );
}