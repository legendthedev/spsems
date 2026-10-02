import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import ThemePromptModal from './components/ThemePromptModal';
import PlatformLandingPage from './pages/PlatformLandingPage';
import LandingPage        from './pages/LandingPage';
import RegisterPage       from './pages/RegisterPage';
import RegisterLecturerPage from './pages/RegisterLecturerPage';
import RegisterAdminPage  from './pages/RegisterAdminPage';
import InstitutionalOnboardingPage from './pages/InstitutionalOnboardingPage';
import StudentPortal      from './pages/StudentPortal';
import SupervisorPortal   from './pages/SupervisorPortal';
import AdminPortal        from './pages/AdminPortal';
import SiwesPortal        from './pages/SiwesPortal';
import HostelPortal       from './pages/HostelPortal';

function PrivateRoute({ children, role }) {
  const { user, loading } = useAuth();
  if (loading) return <div style={styles.loader}>Loading…</div>;
  if (!user)   return <Navigate to="/login" replace />;
  if (role && user.role !== role) return <Navigate to="/" replace />;
  return children;
}

function AppRoutes() {
  const { user, loading } = useAuth();
  if (loading) return <div style={styles.loader}>Loading…</div>;

  return (
    <Routes>
      <Route path="/"                   element={user ? <Navigate to={`/${user.role}`} replace /> : <PlatformLandingPage />} />
      <Route path="/login"              element={<LandingPage />} />
      <Route path="/login/:slug"        element={<LandingPage />} />
      <Route path="/login/:slug/:portalId" element={<LandingPage />} />
      <Route path="/portal/:slug/siwes" element={<SiwesPortal />} />
      <Route path="/siwes"              element={<SiwesPortal />} />
      <Route path="/portal/:slug/hostel" element={<HostelPortal />} />
      <Route path="/hostel"             element={<HostelPortal />} />
      <Route path="/portal/:slug/spsems" element={user ? <Navigate to={`/${user.role}`} replace /> : <LandingPage />} />
      <Route path="/portal/:slug"       element={<LandingPage />} />
      <Route path="/kwasu"              element={<LandingPage />} />
      <Route path="/onboard"            element={<InstitutionalOnboardingPage />} />
      <Route path="/onboarding"         element={<InstitutionalOnboardingPage />} />
      <Route path="/institutions/onboard" element={<InstitutionalOnboardingPage />} />
      <Route path="/register"           element={<RegisterPage />} />
      <Route path="/register/lecturer"  element={<RegisterLecturerPage />} />
      <Route path="/register/admin"     element={<RegisterAdminPage />} />
      <Route path="/student"            element={<PrivateRoute role="student"><StudentPortal /></PrivateRoute>} />
      <Route path="/supervisor"         element={<PrivateRoute role="supervisor"><SupervisorPortal /></PrivateRoute>} />
      <Route path="/admin"              element={<PrivateRoute role="admin"><AdminPortal /></PrivateRoute>} />
      <Route path="*"                   element={<Navigate to="/" replace />} />
    </Routes>
  );
}

const styles = {
  loader: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    height: '100vh', fontSize: 18, color: '#16a34a', fontWeight: 600,
  },
};

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Toaster position="top-right" toastOptions={{ duration: 4000 }} />
          <ThemePromptModal />
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}
