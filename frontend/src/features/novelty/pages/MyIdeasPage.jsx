import { Navigate } from 'react-router-dom';

/**
 * MyIdeasPage has been merged into UserDashboard.
 * This component redirects for backward compatibility.
 */
const MyIdeasPage = () => <Navigate to="/user/dashboard" replace />;

export default MyIdeasPage;
