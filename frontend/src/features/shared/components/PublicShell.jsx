import Header from "../layout/Header";
import { PageTransition } from "@/components/PageTransition";

const PublicShell = ({ children }) => {
  return (
    <div className="min-h-screen bg-neutral-950 text-white">
      <Header />

      <main>
        <PageTransition>{children}</PageTransition>
      </main>
    </div>
  );
};

export default PublicShell;
