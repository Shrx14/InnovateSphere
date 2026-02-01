import React, { useState, useEffect } from 'react';
import DashboardLayout from './DashboardLayout';
import Settings from './Settings';
import ProjectIdeas from '../legacy/ProjectIdeas';
import AdminDashboard from '../legacy/AdminDashboard';
import { API_BASE_URL } from '../config';

const InnovateSphereAuth = () => {
  const [currentView, setCurrentView] = useState('login');
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  // Function to decode JWT payload
  const decodeJWT = (token) => {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload;
    } catch (e) {
      return null;
    }
  };

  // Centralized auth hydration function
  const hydrateUserFromToken = (token) => {
    const payload = decodeJWT(token);
    if (!payload || !payload.exp || payload.exp < Date.now() / 1000) {
      return null;
    }
    const role = payload.role;
    const username = payload.username || 'User';
    const email = payload.email || 'user@example.com';
    return {
      username,
      email,
      role,
      skill_level: 'beginner',
      preferred_domains: []
    };
  };

  // Route guard: check for token on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      const userData = hydrateUserFromToken(token);
      if (userData) {
        setUser(userData);
      } else {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_email');
      }
    }
  }, []);

  // Validation functions
  const validateEmail = (email) => {
    const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return pattern.test(email);
  };

  const validatePassword = (password) => {
    const minLength = 8;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

    const errors = [];
    if (password.length < minLength) errors.push("at least 8 characters");
    if (!hasUpperCase) errors.push("one uppercase letter");
    if (!hasLowerCase) errors.push("one lowercase letter");
    if (!hasNumbers) errors.push("one number");
    if (!hasSpecialChar) errors.push("one special character");

    return errors.length === 0 ? { isValid: true } : { 
      isValid: false, 
      error: `Password must contain ${errors.join(", ")}`
    };
  };

  const validateUsername = (username) => {
    if (username.length < 6 || username.length > 16) {
      return { isValid: false, error: "Username must be between 6 and 16 characters" };
    }
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      return { isValid: false, error: "Username can only contain letters, numbers, and underscores" };
    }
    return { isValid: true };
  };

  // Registration Component
  const Register = () => {
    const [formData, setFormData] = useState({
      email: '',
      username: '',
      password: '',
      confirmPassword: '',
      preferred_domains: [],
      skill_level: 'beginner'
    });
    const [fieldErrors, setFieldErrors] = useState({
      email: '',
      username: '',
      password: ''
    });
    const domains = ['AI & ML', 'Web Development', 'Blockchain', 'IoT', 'Mobile Development', 'Data Science'];
    const skillLevels = ['beginner', 'intermediate', 'expert'];

    const handleInputChange = (event) => {
      const { name, value } = event.target;
      setFormData(prev => ({ ...prev, [name]: value }));
      
      // Clear any previous error for this field
      setFieldErrors(prev => ({ ...prev, [name]: '' }));

      // Validate on input change
      if (name === 'email' && value) {
        if (!validateEmail(value)) {
          setFieldErrors(prev => ({ ...prev, email: 'Invalid email format' }));
        }
      } else if (name === 'password' && value) {
        const result = validatePassword(value);
        if (!result.isValid) {
          setFieldErrors(prev => ({ ...prev, password: result.error }));
        }
      } else if (name === 'username' && value) {
        const result = validateUsername(value);
        if (!result.isValid) {
          setFieldErrors(prev => ({ ...prev, username: result.error }));
        }
      }
    };

    const handleDomainToggle = (domain) => {
      setFormData(prev => ({
        ...prev,
        preferred_domains: prev.preferred_domains.includes(domain)
          ? prev.preferred_domains.filter(d => d !== domain)
          : [...prev.preferred_domains, domain]
      }));
    };

    const handleSubmit = async (event) => {
      event.preventDefault();
      
      // Clear all previous errors
      setFieldErrors({
        email: '',
        username: '',
        password: ''
      });
      setMessage({ type: '', text: '' });

      // Validate all fields
      let hasErrors = false;
      
      if (!validateEmail(formData.email)) {
        setFieldErrors(prev => ({ ...prev, email: 'Invalid email format' }));
        hasErrors = true;
      }

      const passwordValidation = validatePassword(formData.password);
      if (!passwordValidation.isValid) {
        setFieldErrors(prev => ({ ...prev, password: passwordValidation.error }));
        hasErrors = true;
      }

      const usernameValidation = validateUsername(formData.username);
      if (!usernameValidation.isValid) {
        setFieldErrors(prev => ({ ...prev, username: usernameValidation.error }));
        hasErrors = true;
      }

      if (formData.password !== formData.confirmPassword) {
        setMessage({ type: 'error', text: 'Passwords do not match!' });
        return;
      }

      if (hasErrors) {
        setMessage({ type: 'error', text: 'Please fix all field errors before submitting' });
        return;
      }

      setLoading(true);
      try {
        const response = await fetch(`${API_BASE_URL}/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: formData.email,
            username: formData.username,
            password: formData.password,
            preferred_domains: formData.preferred_domains,
            skill_level: formData.skill_level
          })
        });
        const data = await response.json();

        if (response.ok) {
          setMessage({ type: 'success', text: 'Registration successful! Please login.' });
          setTimeout(() => setCurrentView('login'), 2000);
        } else {
          if (data.type === 'EXISTING_EMAIL') {
            setMessage({ 
              type: 'info', 
              text: 'This email is already registered. Would you like to login instead?' 
            });
            setTimeout(() => setCurrentView('login'), 2000);
          } else {
            setMessage({ type: 'error', text: data.error || 'Registration failed' });
          }
        }
      } catch (error) {
        setMessage({ type: 'error', text: 'Network error. Please try again.' });
      } finally {
        setLoading(false);
      }
    };
    return (
      <div className="w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center">Register for InnovateSphere</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              required
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                fieldErrors.email ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {fieldErrors.email && (
              <p className="mt-1 text-sm text-red-600">{fieldErrors.email}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Username</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              required
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                fieldErrors.username ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {fieldErrors.username && (
              <p className="mt-1 text-sm text-red-600">{fieldErrors.username}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Password
              <span className="ml-1 text-xs text-gray-500">
                (min. 8 characters, include uppercase, lowercase, number, and special character)
              </span>
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              required
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                fieldErrors.password ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {fieldErrors.password && (
              <p className="mt-1 text-sm text-red-600">{fieldErrors.password}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Confirm Password</label>
            <input
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Preferred Domains</label>
            <div className="flex flex-wrap gap-2">
              {domains.map(domain => (
                <button
                  key={domain}
                  type="button"
                  onClick={() => handleDomainToggle(domain)}
                  className={`px-3 py-1 rounded-full text-sm ${
                    formData.preferred_domains.includes(domain)
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-700'
                  }`}
                >
                  {domain}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Skill Level</label>
            <select
              name="skill_level"
              value={formData.skill_level}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {skillLevels.map(level => (
                <option key={level} value={level}>
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 disabled:bg-gray-400"
          >
            {loading ? 'Registering...' : 'Register'}
          </button>
        </div>
      </div>
    );
  };

  // Login Component
  const Login = () => {
    const [formData, setFormData] = useState({
      email: '',
      password: ''
    });
    const handleInputChange = (event) => {
      const { name, value } = event.target;
      setFormData(prev => ({ ...prev, [name]: value }));
    };
    const handleSubmit = async (event) => {
      event.preventDefault();
      setLoading(true);
      setMessage({ type: '', text: '' });
      try {
        const response = await fetch(`${API_BASE_URL}/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(formData)
        });
        const data = await response.json();

        if (response.ok) {
          localStorage.setItem('access_token', data.access_token);
          const userData = hydrateUserFromToken(data.access_token);
          if (userData) {
            setUser(userData);
            setMessage({ type: 'success', text: 'Login successful!' });
          } else {
            setMessage({ type: 'error', text: 'Invalid token received' });
          }
        } else {
          setMessage({ type: 'error', text: data.error || 'Login failed' });
        }
      } catch (error) {
        setMessage({ type: 'error', text: 'Network error. Please try again.' });
      } finally {
        setLoading(false);
      }
    };
    return (
      <div className="w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center">Login to InnovateSphere</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 disabled:bg-gray-400"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </div>
      </div>
    );
  };

  // Dashboard Component
  const Dashboard = () => {
    const [currentPage, setCurrentPage] = useState('dashboard');
    
    const handleLogout = () => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_email');
      setUser(null);
      setCurrentView('login');
      setMessage({ type: 'success', text: 'Logged out successfully' });
    };

    const renderContent = () => {
      if (user?.role === 'admin' && (currentPage === 'settings' || currentPage === 'projects')) {
        return (
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl font-bold mb-8 text-red-600">Unauthorized</h2>
            <p className="text-gray-600">You do not have permission to access this page.</p>
          </div>
        );
      }
      switch(currentPage) {
        case 'admin':
          if (user?.role === 'admin') {
            return (
              <div className="max-w-4xl mx-auto text-center">
                <h2 className="text-3xl font-bold mb-8 text-orange-600">Legacy UI Deprecated</h2>
                <p className="text-gray-600">This component has been moved to src/legacy/ for reference. Enable ENABLE_LEGACY_UI to re-enable.</p>
              </div>
            );
          } else {
            return (
              <div className="max-w-4xl mx-auto text-center">
                <h2 className="text-3xl font-bold mb-8 text-red-600">Unauthorized</h2>
                <p className="text-gray-600">You do not have permission to access this page.</p>
              </div>
            );
          }
        case 'settings':
          return <Settings user={user} />;
        case 'projects':
          return (
            <div className="max-w-4xl mx-auto text-center">
              <h2 className="text-3xl font-bold mb-8 text-orange-600">Legacy UI Deprecated</h2>
              <p className="text-gray-600">This component has been moved to src/legacy/ for reference. Enable ENABLE_LEGACY_UI to re-enable.</p>
            </div>
          );
        default:
          return (
            <div className="max-w-6xl mx-auto">
              <h2 className="text-3xl font-bold mb-8 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Welcome back, {user?.username}! 👋
              </h2>

              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <h4 className="text-sm font-semibold text-gray-500 uppercase">Skill Level</h4>
                  <p className="text-2xl font-bold mt-2 capitalize">{user?.skill_level || 'Not Set'}</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <h4 className="text-sm font-semibold text-gray-500 uppercase">Domains of Interest</h4>
                  <p className="text-2xl font-bold mt-2">{user?.preferred_domains?.length || 0}</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <h4 className="text-sm font-semibold text-gray-500 uppercase">Project Ideas</h4>
                  <p className="text-2xl font-bold mt-2">Coming Soon</p>
                </div>
              </div>

              {/* Profile Section */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6 mb-8">
                <h3 className="text-xl font-semibold mb-4">Profile Details</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Email</label>
                    <p className="mt-1">{user?.email}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Username</label>
                    <p className="mt-1">{user?.username}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Domains</label>
                    <div className="mt-1 flex flex-wrap gap-2">
                      {user?.preferred_domains?.map(domain => (
                        <span key={domain} className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                          {domain}
                        </span>
                      )) || 'None selected'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Call to Action */}
              <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-lg p-8 text-white text-center">
                <h3 className="text-2xl font-bold mb-4">Ready to Discover Your Next Big Idea? 🚀</h3>
                <p className="text-lg mb-6 opacity-90">
                  Our AI is ready to help you generate innovative project ideas tailored to your interests and skill level.
                </p>
                <button
                  onClick={() => setCurrentPage('projects')}
                  className="bg-white text-blue-600 font-semibold py-3 px-8 rounded-full hover:bg-gray-100 transition-colors duration-200"
                >
                  Generate Ideas (Coming Soon!)
                </button>
              </div>

              {/* Next Steps Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <h4 className="font-semibold mb-2">🎯 Project Generation</h4>
                  <p className="text-gray-600">AI-powered project suggestions based on your interests and expertise.</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <h4 className="font-semibold mb-2">🔍 Novelty Scoring</h4>
                  <p className="text-gray-600">Advanced algorithms to evaluate the uniqueness of your project ideas.</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <h4 className="font-semibold mb-2">⚙️ Tech Stack</h4>
                  <p className="text-gray-600">Smart recommendations for the best technologies for your project.</p>
                </div>
              </div>
            </div>
          );
      }
    };

    return (
      <DashboardLayout onLogout={handleLogout} currentPage={currentPage} onPageChange={setCurrentPage} user={user}>
        {renderContent()}
      </DashboardLayout>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8">
        {/* Header */}
        <div className="mb-6 text-center">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">InnovateSphere</h1>
          <p className="text-gray-600 mt-2">AI-Powered Project Idea Navigator</p>
        </div>
        {/* Message Display */}
        {message.text && (
          <div className={`mb-4 p-3 rounded ${
            message.type === 'error' 
              ? 'bg-red-100 text-red-700' 
              : message.type === 'info'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-green-100 text-green-700'
          }`}>
            {message.text}
          </div>
        )}
        {/* Main Content */}
        {user ? (
          <Dashboard />
        ) : (
          <>
            {currentView === 'login' ? <Login /> : <Register />}
            <div className="mt-4 text-center">
              <button
                onClick={() => {
                  setCurrentView(currentView === 'login' ? 'register' : 'login');
                  setMessage({ type: '', text: '' });
                }}
                className="text-blue-500 hover:underline"
              >
                {currentView === 'login'
                   ? "Don't have an account? Register"
                   : 'Already have an account? Login'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default InnovateSphereAuth;