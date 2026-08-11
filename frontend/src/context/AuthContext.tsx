import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import api from "../services/api";

import type {
  LoginResponse,
  User,
} from "../types/auth";


interface AuthContextType {

  user: User | null;

  loading: boolean;

  login: (
    email: string,
    password: string
  ) => Promise<void>;

  logout: () => void;

}


const AuthContext =
  createContext<
    AuthContextType | undefined
  >(undefined);


// =====================================================
// AUTH PROVIDER
// =====================================================

export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {

  const [
    user,
    setUser,
  ] = useState<User | null>(
    null
  );


  const [
    loading,
    setLoading,
  ] = useState(true);


  // ===================================================
  // RESTORE LOGIN SESSION
  // ===================================================

  useEffect(() => {

    const restoreSession =
      async () => {

        const token =
          localStorage.getItem(
            "access_token"
          );


        // No token = not logged in
        if (!token) {

          setUser(null);

          setLoading(false);

          return;

        }


        try {

          // Validate existing token
          // and retrieve current user.

          const response =
            await api.get<User>(
              "/auth/me"
            );


          setUser(
            response.data
          );

        } catch (error) {

          console.error(
            "SESSION RESTORE ERROR:",
            error
          );


          // Token is invalid/expired
          localStorage.removeItem(
            "access_token"
          );


          setUser(null);

        } finally {

          setLoading(false);

        }

      };


    restoreSession();

  }, []);


  // ===================================================
  // LOGIN
  // ===================================================

  const login = async (
    email: string,
    password: string
  ) => {

    // OAuth2PasswordRequestForm expects:
    //
    // username
    // password

    const form =
      new URLSearchParams();


    form.append(
      "username",
      email
    );


    form.append(
      "password",
      password
    );


    // -------------------------------------------------
    // LOGIN REQUEST
    // -------------------------------------------------

    const response =
      await api.post<LoginResponse>(
        "/auth/login",
        form,
        {
          headers: {

            "Content-Type":
              "application/x-www-form-urlencoded",

          },
        }
      );


    // -------------------------------------------------
    // GET TOKEN
    // -------------------------------------------------

    const token =
      response.data.access_token;


    if (!token) {

      throw new Error(
        "Backend did not return an access token."
      );

    }


    // -------------------------------------------------
    // SAVE TOKEN
    // -------------------------------------------------

    localStorage.setItem(
      "access_token",
      token
    );


    // -------------------------------------------------
    // BACKEND MAY ALREADY RETURN USER
    // -------------------------------------------------

    if (
      response.data.user
    ) {

      setUser(
        response.data.user
      );

      return;

    }


    // -------------------------------------------------
    // OTHERWISE GET USER FROM /auth/me
    // -------------------------------------------------

    try {

      const meResponse =
        await api.get<User>(
          "/auth/me"
        );


      setUser(
        meResponse.data
      );

    } catch (error) {

      // Login succeeded but retrieving
      // the user failed.
      //
      // Remove token so we don't leave
      // a broken session behind.

      localStorage.removeItem(
        "access_token"
      );


      setUser(null);


      throw error;

    }

  };


  // ===================================================
  // LOGOUT
  // ===================================================

  const logout = () => {

    localStorage.removeItem(
      "access_token"
    );


    setUser(null);

  };


  // ===================================================
  // PROVIDER
  // ===================================================

  return (

    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
      }}
    >

      {children}

    </AuthContext.Provider>

  );

}


// =====================================================
// AUTH HOOK
// =====================================================

export function useAuth() {

  const context =
    useContext(
      AuthContext
    );


  if (!context) {

    throw new Error(
      "useAuth must be used inside AuthProvider"
    );

  }


  return context;

}