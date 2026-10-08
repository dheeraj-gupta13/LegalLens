import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, hasToken, setToken, setUnauthorizedHandler } from "../api/client.js";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(hasToken());

  const logout = useCallback(() => { setToken(null); setUser(null); }, []);

  useEffect(() => {
    setUnauthorizedHandler(logout);
    if (hasToken()) api.me().then((d) => setUser(d.user)).catch(logout).finally(() => setLoading(false));
  }, [logout]);

  const authenticate = async (kind, email, password) => {
    const d = await api[kind](email, password);
    setToken(d.access_token);
    setUser(d.user);
  };

  return (
    <AuthContext.Provider value={{ user, loading, logout, login: (e, p) => authenticate("login", e, p), register: (e, p) => authenticate("register", e, p) }}>
      {children}
    </AuthContext.Provider>
  );
}
