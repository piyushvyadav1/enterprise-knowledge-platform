import {
  useEffect,
  useState,
  type FormEvent,
} from "react";

import {
  BrainCircuit,
  LockKeyhole,
  Mail,
} from "lucide-react";

import axios from "axios";

import {
  useNavigate,
} from "react-router-dom";

import {
  useAuth,
} from "../context/AuthContext";


export default function Login() {

  const {
    login,
    user,
  } = useAuth();

  const navigate = useNavigate();


  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [error, setError] =
    useState("");

  const [loading, setLoading] =
    useState(false);


  // --------------------------------------------------
  // Redirect if already logged in
  // --------------------------------------------------

  useEffect(() => {

    if (user) {

      navigate(
        "/dashboard",
        {
          replace: true,
        }
      );

    }

  }, [
    user,
    navigate,
  ]);


  // --------------------------------------------------
  // Login form submit
  // --------------------------------------------------

  const handleSubmit = async (
    event: FormEvent
  ) => {

    event.preventDefault();

    setError("");
    setLoading(true);


    try {

      await login(
        email.trim(),
        password
      );

      navigate(
        "/dashboard",
        {
          replace: true,
        }
      );

    } catch (err) {

      console.error(
        "LOGIN ERROR:",
        err
      );


      // ----------------------------------------------
      // Axios/API errors
      // ----------------------------------------------

      if (
        axios.isAxiosError(err)
      ) {

        // Wrong email/password
        if (
          err.response?.status === 401
        ) {

          setError(
            "Invalid email or password."
          );

        }

        // Backend cannot be reached
        else if (
          !err.response
        ) {

          setError(
            "Cannot connect to the server."
          );

        }

        // Backend returned another error
        else {

          const detail =
            err.response?.data?.detail;

          if (
            typeof detail === "string"
          ) {

            setError(detail);

          } else {

            setError(
              "Login failed. Please try again."
            );

          }

        }

      }

      // ----------------------------------------------
      // Frontend / unexpected error
      // ----------------------------------------------

      else {

        setError(
          "Something went wrong after login."
        );

      }

    } finally {

      setLoading(false);

    }

  };


  // --------------------------------------------------
  // UI
  // --------------------------------------------------

  return (

    <div className="login-page">

      <div className="login-card">

        <div className="brand-icon">

          <BrainCircuit
            size={32}
          />

        </div>


        <h1>
          Enterprise Knowledge
        </h1>


        <h2>
          Intelligence Platform
        </h2>


        <p className="login-subtitle">

          Secure access to enterprise knowledge
          and AI intelligence.

        </p>


        <form
          onSubmit={handleSubmit}
        >

          {/* EMAIL */}

          <label>
            Email
          </label>


          <div className="input-wrapper">

            <Mail
              size={18}
            />


            <input
              type="email"
              placeholder="name@enterprise.com"
              value={email}
              onChange={(event) =>
                setEmail(
                  event.target.value
                )
              }
              autoComplete="email"
              required
            />

          </div>


          {/* PASSWORD */}

          <label>
            Password
          </label>


          <div className="input-wrapper">

            <LockKeyhole
              size={18}
            />


            <input
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(event) =>
                setPassword(
                  event.target.value
                )
              }
              autoComplete="current-password"
              required
            />

          </div>


          {/* ERROR */}

          {error && (

            <div className="error-message">

              {error}

            </div>

          )}


          {/* LOGIN BUTTON */}

          <button
            className="primary-button"
            type="submit"
            disabled={loading}
          >

            {
              loading
                ? "Signing in..."
                : "Sign In"
            }

          </button>

        </form>


        <div className="login-footer">

          Enterprise Knowledge Intelligence
          Platform • Version 1

        </div>

      </div>

    </div>

  );

}