import {
  Navigate,
} from "react-router-dom";

import { useAuth } from "../context/AuthContext";


interface AdminRouteProps {
  children: React.ReactNode;
}


export default function AdminRoute({
  children,
}: AdminRouteProps) {

  const { user } = useAuth();

  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }

  if (user.role !== "admin") {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    );
  }

  return children;
}