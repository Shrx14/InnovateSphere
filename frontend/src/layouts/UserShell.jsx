import UserNav from "../user/UserNav";

const UserShell = ({ children }) => {
  return (
    <div className="min-h-screen bg-neutral-950 text-white">
      <UserNav />

      <main>
        {children}
      </main>
    </div>
  );
};

export default UserShell;
