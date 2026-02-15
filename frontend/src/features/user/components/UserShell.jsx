import UserNav from "./UserNav";
import { PageTransition } from "@/components/PageTransition";

const UserShell = ({ children }) => {
  return (
    <div className="min-h-screen bg-neutral-950 text-white">
      <UserNav />

      <main>
        <PageTransition>{children}</PageTransition>
      </main>
    </div>
  );
};

export default UserShell;
