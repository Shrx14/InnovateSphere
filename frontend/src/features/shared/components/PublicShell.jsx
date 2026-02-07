import Header from "../layout/Header";

const PublicShell = ({ children }) => {
  return (
    <div className="min-h-screen bg-neutral-950 text-white">
      <Header />

      <main>
        {children}
      </main>
    </div>
  );
};

export default PublicShell;
