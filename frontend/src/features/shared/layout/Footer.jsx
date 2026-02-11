import React from 'react';

const Footer = () => {
  return (
    <footer className="border-t border-neutral-800 mt-24">
      <div className="max-w-7xl mx-auto px-6 py-10 text-sm text-neutral-400 flex flex-col items-center space-y-4">
        <div className="text-center">
          <p>Research-grounded innovation</p>
        </div>
        <div className="flex space-x-6">
          <a href="#" className="hover:text-neutral-300">About</a>
          <a href="#" className="hover:text-neutral-300">Documentation</a>
          <a href="#" className="hover:text-neutral-300">Contact</a>
        </div>
        <div>
          <p>© {new Date().getFullYear()} InnovateSphere</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
