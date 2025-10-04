import React from 'react';
import { FiCpu, FiArrowRight, FiStar, FiTrendingUp } from 'react-icons/fi';

const ProjectIdeas = ({ user }) => {
  return (
    <div className="max-w-6xl mx-auto">
      <h2 className="text-3xl font-bold mb-8 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
        Project Ideas
      </h2>

      {/* Coming Soon Banner */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-8 text-white mb-8">
        <div className="flex flex-col md:flex-row items-center justify-between">
          <div className="mb-6 md:mb-0">
            <h3 className="text-2xl font-bold mb-2">AI-Powered Project Generation</h3>
            <p className="text-blue-100">
              Generate innovative project ideas tailored to your skills and interests.
            </p>
          </div>
          <div className="flex items-center space-x-2 bg-white/20 rounded-full px-6 py-3">
            <FiCpu className="w-5 h-5" />
            <span className="font-semibold">Coming Soon</span>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-center w-12 h-12 bg-blue-100 text-blue-600 rounded-lg mb-4">
            <FiCpu className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-semibold mb-2">AI Generation</h3>
          <p className="text-gray-600">
            Advanced AI algorithms to generate unique project ideas based on your profile
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-center w-12 h-12 bg-purple-100 text-purple-600 rounded-lg mb-4">
            <FiStar className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-semibold mb-2">Personalized Match</h3>
          <p className="text-gray-600">
            Ideas matched to your skill level and preferred technology domains
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-center w-12 h-12 bg-indigo-100 text-indigo-600 rounded-lg mb-4">
            <FiTrendingUp className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-semibold mb-2">Innovation Score</h3>
          <p className="text-gray-600">
            Each idea rated for novelty and market potential
          </p>
        </div>
      </div>

      {/* Newsletter Signup */}
      <div className="bg-gray-50 rounded-xl p-8 border border-gray-100">
        <h3 className="text-xl font-semibold mb-4">Get Notified</h3>
        <p className="text-gray-600 mb-6">
          Be the first to know when our AI project generator launches.
        </p>
        <div className="flex gap-4">
          <input
            type="email"
            placeholder="Enter your email"
            className="flex-1 px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            defaultValue={user?.email}
          />
          <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 flex items-center">
            Notify Me
            <FiArrowRight className="ml-2" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProjectIdeas;