import UserNav from "./UserNav";
import { PageTransition } from "@/components/PageTransition";
import StarfieldBackground from "@/components/StarfieldBackground";

const UserShell = ({ children }) => {
  return (
    <div className="min-h-screen bg-neutral-950 text-white relative">
      <StarfieldBackground />
      <div className="relative z-10">
        <UserNav />
        <main>
          <PageTransition>{children}</PageTransition>
        </main>
      </div>
    </div>
  );
};

export default UserShell;
