import Header from "../layout/Header";
import { PageTransition } from "@/components/PageTransition";
import StarfieldBackground from "@/components/StarfieldBackground";
import Footer from "@/components/Footer";

const PublicShell = ({ children }) => {
  return (
    <div className="min-h-screen bg-neutral-950 text-white relative">
      <StarfieldBackground />
      <div className="relative z-10">
        <Header />
        <main>
          <PageTransition>{children}</PageTransition>
        </main>
        <Footer />
      </div>
    </div>
  );
};

export default PublicShell;
