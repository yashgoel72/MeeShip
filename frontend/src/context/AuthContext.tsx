import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";
import { getMe } from '../services/api';
import { getCreditBalance } from '../services/paymentApi';
import { User } from '../types';

export interface AuthContextType {
  user: User | null;
  token: string | null;
  setToken: (token: string | null) => void;
  isAuthenticated: boolean;
  logout: () => void;
  refreshCredits: () => Promise<void>;
  loginWithKinde: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem("jwt") || null);
  const [user, setUser] = useState<User | null>(null);

  // Check for token in URL params (from Kinde callback)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get('token');
    
    if (urlToken) {
      // Store token and clean up URL
      setToken(urlToken);
      localStorage.setItem("jwt", urlToken);
      
      // Remove token from URL without page reload
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const refreshCredits = useCallback(async () => {
    if (!token) return;
    try {
      const bal = await getCreditBalance();
      setUser((prev) => prev ? { ...prev, credits: bal.credits, creditsExpiresAt: bal.expires_at } : prev);
    } catch {
      // Ignore errors
    }
  }, [token]);

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      if (!token) {
        localStorage.removeItem("jwt");
        setUser(null);
        return;
      }

      localStorage.setItem("jwt", token);

      try {
        const res = await getMe();
        if (cancelled) return;
        const me = res.data as any;
        
        // Fetch credit balance
        let credits = 0;
        let creditsExpiresAt: string | null = null;
        try {
          const bal = await getCreditBalance();
          credits = bal.credits;
          creditsExpiresAt = bal.expires_at ?? null;
        } catch {
          // Ignore - new user may not have credits yet
        }

        setUser({
          id: me.id,
          email: me.email,
          name: me.full_name || me.email?.split('@')?.[0] || 'Seller',
          trialCount: 3,
          isUpgraded: Boolean(me.isUpgraded ?? me.is_upgraded ?? (me.subscriptionTier === 'pro' || me.subscription_tier === 'pro')),
          credits,
          creditsExpiresAt,
        });
      } catch {
        // Token invalid/expired
        if (cancelled) return;
        localStorage.removeItem("jwt");
        setUser(null);
        setToken(null);
      }
    };

    run();

    return () => {
      cancelled = true;
    };
  }, [token]);

  const loginWithKinde = () => {
    // Redirect to backend Kinde login endpoint
    const backendLoginUrl = import.meta.env.VITE_BACKEND_LOGIN_URL || 'http://localhost:8000/api/auth/kinde/login';
    window.location.href = backendLoginUrl;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("jwt");
    
    // Redirect to backend Kinde logout endpoint
    const backendLogoutUrl = import.meta.env.VITE_BACKEND_LOGOUT_URL || 'http://localhost:8000/api/auth/kinde/logout';
    window.location.href = backendLogoutUrl;
  };

  const value: AuthContextType = { 
    user, 
    token, 
    setToken, 
    isAuthenticated: !!token, 
    logout, 
    refreshCredits,
    loginWithKinde
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
};
