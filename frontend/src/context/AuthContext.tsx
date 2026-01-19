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

// DEV MODE: Skip Kinde auth and provide mock user with unlimited credits
const DEV_SKIP_AUTH = import.meta.env.DEV;
const DEV_USER: User = {
  id: 'dev-user-123',
  email: 'dev@test.com',
  name: 'Dev User',
  trialCount: 999,
  isUpgraded: true,
  credits: 9999,
  creditsExpiresAt: null,
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(
    DEV_SKIP_AUTH ? 'dev-token' : (localStorage.getItem("jwt") || null)
  );
  const [user, setUser] = useState<User | null>(DEV_SKIP_AUTH ? DEV_USER : null);

  useEffect(() => {
    // Skip auth flow in dev mode
    if (DEV_SKIP_AUTH) {
      console.log('[DEV] Auth bypassed - using mock user with unlimited credits');
      return;
    }
    
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
    // Skip in dev mode
    if (DEV_SKIP_AUTH) return;
    
    if (!token) return;
    try {
      const bal = await getCreditBalance();
      setUser((prev) => prev ? { ...prev, credits: bal.credits, creditsExpiresAt: bal.expires_at } : prev);
    } catch {
      // Ignore errors
    }
  }, [token]);

  useEffect(() => {
    // Skip auth flow in dev mode
    if (DEV_SKIP_AUTH) return;
    
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
    // In dev mode, just set dev user
    if (DEV_SKIP_AUTH) {
      console.log('[DEV] Login - using mock user');
      setUser(DEV_USER);
      return;
    }
    
    // Redirect to backend Kinde login endpoint
    const backendLoginUrl = import.meta.env.VITE_BACKEND_LOGIN_URL || 'http://localhost:8000/api/auth/kinde/login';
    window.location.href = backendLoginUrl;
  };

  const logout = () => {
    // In dev mode, just reset to dev user
    if (DEV_SKIP_AUTH) {
      console.log('[DEV] Logout - resetting to mock user');
      setUser(DEV_USER);
      return;
    }
    
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
