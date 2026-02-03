import React, { createContext, useContext, useState, useEffect } from 'react';
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
  const navigate = useNavigate();

  // Decode JWT payload
  const decodeJWT = (token) => {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload;
    } catch (e) {
      console.error('Failed to decode JWT:', e);
      return null;
    }
  };

  // Hydrate user from token
  const hydrateUserFromToken = (token) => {
    const payload = decodeJWT(token);
    if (!payload || !payload.exp || payload.exp < Date.now() / 1000) {
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
  };

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
  }, []);

  // Login function
  const login = (newToken) => {
    localStorage.setItem('access_token', newToken);
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
        navigate('/explore');
      }
    } else {
      console.error('Login failed: invalid token received');
      logout('Invalid token received');
    }
  };

  // Logout function
  const logout = (reason = 'User logout') => {
    console.log('Logout triggered:', reason);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_email');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    setIsAdmin(false);
    navigate('/');
  };

  const value = {
    user,
    token,
    isAuthenticated,
    isAdmin,
    login,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
