import React from 'react';

const Footer = () => {
  return (
    <footer className="border-t border-neutral-800 mt-24">
      <div className="max-w-7xl mx-auto px-6 py-10 text-sm text-neutral-500 flex justify-between">
        <span>© {new Date().getFullYear()} InnovateSphere</span>
        <span>Evidence-driven innovation</span>
      </div>
    </footer>
  );
};

export default Footer;
