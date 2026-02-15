import axios from 'axios';
import { API_BASE_URL } from '../config/config';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
});

// Request interceptor to add auth header
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Track whether a token refresh is already in progress
let isRefreshing = false;
let refreshSubscribers = [];

function onRefreshed(newToken) {
  refreshSubscribers.forEach((cb) => cb(newToken));
  refreshSubscribers = [];
}

function addRefreshSubscriber(callback) {
  refreshSubscribers.push(callback);
}

// Response interceptor — attempt transparent token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and we haven't retried yet, attempt refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem('refresh_token');

      if (refreshToken) {
        if (isRefreshing) {
          // Queue the request until refresh completes
          return new Promise((resolve) => {
            addRefreshSubscriber((newToken) => {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              resolve(api(originalRequest));
            });
          });
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
          const res = await axios.post(
            `${API_BASE_URL}/refresh`,
            {},
            { headers: { Authorization: `Bearer ${refreshToken}` } }
          );
          const newToken = res.data.access_token;
          localStorage.setItem('access_token', newToken);
          isRefreshing = false;
          onRefreshed(newToken);

          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        } catch (refreshErr) {
          isRefreshing = false;
          refreshSubscribers = [];
          // Refresh failed — force logout
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.dispatchEvent(new CustomEvent('auth:logout', { detail: 'Refresh token expired' }));
          return Promise.reject(refreshErr);
        }
      }

      // No refresh token — force logout
      window.dispatchEvent(new CustomEvent('auth:logout', { detail: 'API 401' }));
    }

    if (error.response?.status === 403) {
      console.log('Forbidden (403) — insufficient permissions');
    }

    return Promise.reject(error);
  }
);

export default api;
