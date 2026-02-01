import React from 'react';
import Header from '../../shared/layout/Header';
import Footer from '../../shared/layout/Footer';

const AppShell = ({ children }) => {
  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col">
      <Header />
      <main className="flex-1">
        {children}
      </main>
      <Footer />
    </div>
  );
};

export default AppShell;
