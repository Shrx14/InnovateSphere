import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  // Decode JWT payload
  const decodeJWT = useCallback((token) => {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload;
    } catch (e) {
      console.error('Failed to decode JWT:', e);
      return null;
    }
  }, []);

  // Hydrate user from token
  const hydrateUserFromToken = useCallback((token) => {
    const payload = decodeJWT(token);
    // Use Math.floor to get integer seconds for proper comparison with JWT exp (which is in seconds)
    const now = Math.floor(Date.now() / 1000);
    if (!payload || !payload.exp || payload.exp < now) {
      console.log('Auth hydration failed: invalid or expired token');
      return null;
    }

    if (!payload.role) {
      console.log('Auth hydration failed: missing role in token');
      return null;
    }
    console.log('Auth hydration success');
    return {
      id: payload.sub || payload.id,
      email: payload.email,
      role: payload.role,
      preferred_domain_id: payload.preferred_domain_id
    };
  }, [decodeJWT]);

  // Hydrate auth state on app load
  useEffect(() => {
    const storedToken = localStorage.getItem('access_token');
    if (storedToken) {
      const userData = hydrateUserFromToken(storedToken);
      if (userData) {
        setToken(storedToken);
        setUser(userData);
        setIsAuthenticated(true);
        setIsAdmin(userData.role === 'admin');
      } else {
        // Invalid token, clear storage
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_email');
        setToken(null);
        setUser(null);
        setIsAuthenticated(false);
        setIsAdmin(false);
      }
    }
    // Always finish loading, even if no token found
    setIsLoading(false);
  }, [hydrateUserFromToken]);

  // Logout function
  const logout = useCallback(async (reason = 'User logout') => {
    console.log('Logout triggered:', reason);
    // Call backend logout endpoint (best-effort)
    try {
      const storedToken = localStorage.getItem('access_token');
      if (storedToken) {
        await fetch((process.env.REACT_APP_API_URL || 'http://localhost:5000/api') + '/logout', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${storedToken}` },
        });
      }
    } catch (e) {
      // Ignore errors - logout should always succeed client-side
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_email');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    setIsAdmin(false);
    navigate('/');
  }, [navigate]);

  // Listen for auth:logout events from API interceptor
  useEffect(() => {

    const handleAuthLogout = (event) => {
      console.log('Auth logout event received:', event.detail);
      logout('API authentication error');
    };

    window.addEventListener('auth:logout', handleAuthLogout);
    return () => {
      window.removeEventListener('auth:logout', handleAuthLogout);
    };
  }, [logout]);

  // Login function

  const login = (newToken, refreshToken) => {
    localStorage.setItem('access_token', newToken);
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }
    const userData = hydrateUserFromToken(newToken);
    if (userData) {
      setToken(newToken);
      setUser(userData);
      setIsAuthenticated(true);
      setIsAdmin(userData.role === 'admin');
      // Redirect based on role
      if (userData.role === 'admin') {
        navigate('/admin/review');
      } else {
        navigate('/user/dashboard');
      }
    } else {
      console.error('Login failed: invalid token received');
      logout('Invalid token received');
    }
  };

  const value = {

    user,
    token,
    isAuthenticated,
    isAdmin,
    isLoading,
    login,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
