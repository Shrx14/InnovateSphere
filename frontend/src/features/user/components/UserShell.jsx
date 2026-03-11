import UserNav from "./UserNav";
import Footer from "../../shared/layout/Footer";
import { PageTransition } from "@/components/PageTransition";
import StarfieldBackground from "@/components/StarfieldBackground";

const UserShell = ({ children }) => {
  return (
    <div className="min-h-screen text-white relative flex flex-col" style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      <StarfieldBackground />

      <UserNav />

      <main className="relative z-10 flex-1">
        <PageTransition>{children}</PageTransition>
      </main>

      <Footer hideGetStarted />
    </div>
  );
};

export default UserShell;
