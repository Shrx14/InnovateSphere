import Header from "../layout/Header";
import Footer from "../layout/Footer";
import { PageTransition } from "@/components/PageTransition";
import StarfieldBackground from "@/components/StarfieldBackground";

const PublicShell = ({ children }) => {
  return (
    <div className="min-h-screen dark:text-white text-neutral-900 relative flex flex-col" style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      <StarfieldBackground />

      <Header />

      <main className="relative z-10 flex-1">
        <PageTransition>{children}</PageTransition>
      </main>

      <Footer />
    </div>
  );
};

export default PublicShell;
