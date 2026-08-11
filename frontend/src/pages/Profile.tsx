import {
  Mail,
  Building2,
  ShieldCheck,
  UserRound,
  KeyRound,
  CircleCheck,
} from "lucide-react";

import { useAuth } from "../context/AuthContext";

export default function Profile() {
  const { user } = useAuth();

  if (!user) {
    return (
      <div className="profile-page">
        <div className="profile-loading">
          Loading profile...
        </div>
      </div>
    );
  }

  const name = user.name || "User";

  const initials = name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map(
      (part) =>
        part.charAt(0).toUpperCase()
    )
    .join("");

  const roleLabel = (user.role || "employee")
    .split("_")
    .map(
      (part) =>
        part.charAt(0).toUpperCase() +
        part.slice(1)
    )
    .join(" ");

  const department =
    user.department || "General";

  const isActive = true;

  return (
    <div className="profile-page">

      {/* PAGE HEADER */}

      <div className="page-heading">
        <div>
          <h1>My Profile</h1>

          <p>
            Manage your enterprise account
            and access information.
          </p>
        </div>
      </div>


      {/* PROFILE HERO */}

      <section className="profile-hero">

        <div className="profile-avatar">
          {initials}
        </div>

        <div className="profile-identity">

          <div className="profile-name-row">

            <h2>
              {name}
            </h2>

            <span
              className={
                isActive
                  ? "profile-status active"
                  : "profile-status paused"
              }
            >
              <CircleCheck size={13} />

              {isActive
                ? "Active"
                : "Paused"}
            </span>

          </div>

          <p className="profile-role">
            {roleLabel}
          </p>

          <div className="profile-meta">

            <span>
              <Building2 size={15} />

              {department}
            </span>

            <span>
              <Mail size={15} />

              {user.email}
            </span>

          </div>

        </div>

      </section>


      {/* ACCOUNT INFORMATION */}

      <section className="profile-section">

        <div className="profile-section-heading">

          <div className="section-icon">
            <UserRound size={18} />
          </div>

          <div>

            <h2>
              Account Information
            </h2>

            <p>
              Your current enterprise
              identity and access details.
            </p>

          </div>

        </div>


        <div className="profile-info-grid">

          {/* EMAIL */}

          <div className="profile-info-card">

            <span>
              Email Address
            </span>

            <strong>
              {user.email}
            </strong>

            <Mail size={18} />

          </div>


          {/* DEPARTMENT */}

          <div className="profile-info-card">

            <span>
              Department
            </span>

            <strong>
              {department}
            </strong>

            <Building2 size={18} />

          </div>


          {/* ROLE */}

          <div className="profile-info-card">

            <span>
              Access Role
            </span>

            <strong>
              {roleLabel}
            </strong>

            <ShieldCheck size={18} />

          </div>


          {/* USER ID */}

          <div className="profile-info-card">

            <span>
              User ID
            </span>

            <strong>
              #{user.id}
            </strong>

            <UserRound size={18} />

          </div>

        </div>

      </section>


      {/* SECURITY */}

      <section className="profile-section">

        <div className="profile-section-heading">

          <div className="section-icon">
            <ShieldCheck size={18} />
          </div>

          <div>

            <h2>
              Security & Access
            </h2>

            <p>
              Your account access is
              controlled by enterprise
              authentication.
            </p>

          </div>

        </div>


        <div className="security-card">

          <div className="security-card-icon">
            <KeyRound size={21} />
          </div>

          <div className="security-card-content">

            <strong>
              Password & Authentication
            </strong>

            <span>
              Your account is protected
              by secure enterprise
              authentication.
            </span>

          </div>

          <span className="security-protected">
            Protected
          </span>

        </div>

      </section>

    </div>
  );
}