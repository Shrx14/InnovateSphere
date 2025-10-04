import React, { useState } from 'react';
import { FiHome, FiCpu, FiSettings, FiLogOut, FiMenu, FiX, FiZap } from 'react-icons/fi';

const DashboardLayout = ({ children, onLogout, currentPage, onPageChange }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const handleLogout = () => {
    setShowLogoutConfirm(true);
  };

  const NavLink = ({ icon: Icon, text, isActive, onClick }) => (
    <button
      onClick={onClick}
      className={`flex items-center px-4 py-2 rounded-full transition-all duration-200 ${
        isActive 
          ? 'bg-blue-100 text-blue-600' 
          : 'text-gray-600 hover:bg-gray-50'
      }`}
    >
      <Icon className="w-5 h-5 mr-2" />
      <span>{text}</span>
    </button>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation Bar */}
      <nav className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Logo Icon Only */}
            <div className="flex items-center">
              <div className="flex items-center">
                <div className="flex items-center p-2 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 text-white">
                  <FiZap className="w-6 h-6" />
                </div>
              </div>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-4">
              <NavLink 
                icon={FiHome} 
                text="Dashboard" 
                isActive={currentPage === 'dashboard'} 
                onClick={() => onPageChange('dashboard')}
              />
              <NavLink 
                icon={FiCpu} 
                text="Project Ideas" 
                isActive={currentPage === 'projects'}
                onClick={() => onPageChange('projects')}
              />
              <NavLink 
                icon={FiSettings} 
                text="Settings" 
                isActive={currentPage === 'settings'}
                onClick={() => onPageChange('settings')}
              />
              <div className="h-6 w-px bg-gray-200 mx-2" /> {/* Divider */}
              <NavLink icon={FiLogOut} text="Logout" onClick={handleLogout} />
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden flex items-center">
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="text-gray-600 hover:text-gray-900 focus:outline-none"
              >
                {isMobileMenuOpen ? (
                  <FiX className="h-6 w-6" />
                ) : (
                  <FiMenu className="h-6 w-6" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden bg-white border-t border-gray-100">
            <div className="px-2 pt-2 pb-3 space-y-1">
              <NavLink 
                icon={FiHome} 
                text="Dashboard" 
                isActive={currentPage === 'dashboard'}
                onClick={() => onPageChange('dashboard')}
              />
              <NavLink 
                icon={FiCpu} 
                text="Project Ideas" 
                isActive={currentPage === 'projects'}
                onClick={() => onPageChange('projects')}
              />
              <NavLink 
                icon={FiSettings} 
                text="Settings" 
                isActive={currentPage === 'settings'}
                onClick={() => onPageChange('settings')}
              />
              <NavLink 
                icon={FiLogOut} 
                text="Logout" 
                onClick={handleLogout}
              />
            </div>
          </div>
        )}
      </nav>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Logout Confirmation Modal */}
      {showLogoutConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-medium mb-4">Confirm Logout</h3>
            <p className="text-gray-600 mb-6">Are you sure you want to logout?</p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowLogoutConfirm(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors duration-200"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowLogoutConfirm(false);
                  onLogout();
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const exportedComponent = DashboardLayout;
export default exportedComponent;