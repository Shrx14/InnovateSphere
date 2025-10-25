import React, { useState } from 'react';
import { FiUser, FiLock, FiGlobe } from 'react-icons/fi';
import { API_BASE_URL } from '../config';

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

const Settings = ({ user }) => {
  const [activeTab, setActiveTab] = useState('profile');
  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmNewPassword: ''
  });
  const [fieldErrors, setFieldErrors] = useState({
    newPassword: '',
    confirmNewPassword: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState(null);


  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear previous error for this field
    setFieldErrors(prev => ({ ...prev, [name]: '' }));

    // Validate new password as user types
    if (name === 'newPassword' && value) {
      const result = validatePassword(value);
      if (!result.isValid) {
        setFieldErrors(prev => ({ ...prev, newPassword: result.error }));
      }
    }

    // Validate confirm password match
    if (name === 'confirmNewPassword' && value) {
      if (value !== formData.newPassword) {
        setFieldErrors(prev => ({ ...prev, confirmNewPassword: 'Passwords do not match' }));
      }
    }
  };

  const handlePasswordChange = async () => {
    // Reset errors
    setFieldErrors({
      newPassword: '',
      confirmNewPassword: ''
    });
    setMessage(null);

    // Validate new password
    const passwordValidation = validatePassword(formData.newPassword);
    if (!passwordValidation.isValid) {
      setFieldErrors(prev => ({ ...prev, newPassword: passwordValidation.error }));
      return;
    }

    // Validate password match
    if (formData.newPassword !== formData.confirmNewPassword) {
      setFieldErrors(prev => ({ ...prev, confirmNewPassword: 'Passwords do not match' }));
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: user.email,
          current_password: formData.currentPassword,
          new_password: formData.newPassword
        })
      });

      const data = await response.json();

      if (response.ok) {
        setMessage({ type: 'success', text: 'Password updated successfully!' });
        setFormData({ currentPassword: '', newPassword: '', confirmNewPassword: '' });
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to update password' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };



  const SettingsTab = ({ icon: Icon, title, isActive, onClick }) => (
    <button
      onClick={onClick}
      className={`flex items-center p-3 w-full rounded-lg transition-all duration-200 ${
        isActive
          ? 'bg-blue-50 text-blue-600'
          : 'text-gray-600 hover:bg-gray-50'
      }`}
    >
      <Icon className="w-5 h-5 mr-3" />
      <span className="font-medium">{title}</span>
    </button>
  );

  return (
    <div className="max-w-6xl mx-auto">
      <h2 className="text-3xl font-bold mb-8 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
        Settings
      </h2>
      
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Settings Navigation */}
          <div className="space-y-2">
            <SettingsTab
              icon={FiUser}
              title="Profile"
              isActive={activeTab === 'profile'}
              onClick={() => setActiveTab('profile')}
            />
            <SettingsTab
              icon={FiLock}
              title="Security"
              isActive={activeTab === 'security'}
              onClick={() => setActiveTab('security')}
            />
            <SettingsTab
              icon={FiGlobe}
              title="Preferences"
              isActive={activeTab === 'preferences'}
              onClick={() => setActiveTab('preferences')}
            />

          </div>

          {/* Settings Content */}
          <div className="md:col-span-3">
            {activeTab === 'profile' && (
              <div className="space-y-6">
                <h3 className="text-xl font-semibold">Profile Settings</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email
                    </label>
                    <input
                      type="email"
                      value={user?.email}
                      className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      disabled
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Username
                    </label>
                    <input
                      type="text"
                      value={user?.username}
                      className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      disabled
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Skill Level
                    </label>
                    <select
                      value={user?.skill_level}
                      className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="beginner">Beginner</option>
                      <option value="intermediate">Intermediate</option>
                      <option value="expert">Expert</option>
                    </select>
                  </div>
                </div>
                <button className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                  Save Changes
                </button>
              </div>
            )}

            {activeTab === 'security' && (
              <div>
                <h3 className="text-xl font-semibold mb-6">Security Settings</h3>
                <div className="space-y-4">
                  <div className="p-6 rounded-lg border border-gray-200">
                    <h4 className="font-medium mb-4">Change Password</h4>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Current Password</label>
                        <input
                          type="password"
                          name="currentPassword"
                          value={formData.currentPassword}
                          onChange={handleInputChange}
                          className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          New Password
                          <span className="ml-1 text-xs text-gray-500">
                            (min. 8 characters, include uppercase, lowercase, number, and special character)
                          </span>
                        </label>
                        <input
                          type="password"
                          name="newPassword"
                          value={formData.newPassword}
                          onChange={handleInputChange}
                          className={`w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                            fieldErrors.newPassword ? 'border-red-500' : 'border-gray-300'
                          }`}
                        />
                        {fieldErrors.newPassword && (
                          <p className="mt-1 text-sm text-red-600">{fieldErrors.newPassword}</p>
                        )}
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Confirm New Password</label>
                        <input
                          type="password"
                          name="confirmNewPassword"
                          value={formData.confirmNewPassword}
                          onChange={handleInputChange}
                          className={`w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                            fieldErrors.confirmNewPassword ? 'border-red-500' : 'border-gray-300'
                          }`}
                        />
                        {fieldErrors.confirmNewPassword && (
                          <p className="mt-1 text-sm text-red-600">{fieldErrors.confirmNewPassword}</p>
                        )}
                      </div>
                      {message && (
                        <div className={`mt-2 p-2 rounded ${
                          message.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                        }`}>
                          {message.text}
                        </div>
                      )}
                      <button 
                        onClick={handlePasswordChange} 
                        disabled={isLoading}
                        className="mt-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 disabled:bg-gray-400"
                      >
                        {isLoading ? 'Updating...' : 'Update Password'}
                      </button>
                    </div>
                  </div>

                </div>
              </div>
            )}

            {activeTab === 'preferences' && (
              <div>
                <h3 className="text-xl font-semibold mb-6">Preferences</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 rounded-lg border border-gray-200">
                    <div>
                      <h4 className="font-medium">Email Notifications</h4>
                      <p className="text-sm text-gray-500">Receive updates about your project ideas</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" className="sr-only peer" />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              </div>
            )}


          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;