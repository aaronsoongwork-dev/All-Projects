import { createBrowserRouter, Navigate } from "react-router";
import { Root } from "./components/Root";
import { Dashboard } from "./components/Dashboard";
import { LiveRecording } from "./components/LiveRecording";
import { FileAnalysis } from "./components/FileAnalysis";
import { Reports } from "./components/Reports";
import { Analytics } from "./components/Analytics";
import { Settings } from "./components/Settings";
import { Profile } from "./components/Profile";
import { Login } from "./components/Login";
import { useAuth } from "./contexts/AuthContext";

// Restoring a Supabase session is asynchronous. Without this gate, a page
// refresh would briefly see isAuthenticated === false and bounce a signed-in
// user to /login before the session resolves.
function AuthPending() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <span className="size-5 rounded-full border-2 border-muted border-t-foreground animate-spin" />
    </div>
  );
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <AuthPending />;
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

function RedirectIfAuthed() {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <AuthPending />;
  return isAuthenticated ? <Navigate to="/" replace /> : <Login />;
}

export const router = createBrowserRouter([
  {
    path: "/login",
    Component: RedirectIfAuthed,
  },
  {
    path: "/",
    element: <RequireAuth><Root /></RequireAuth>,
    children: [
      { index: true, Component: Dashboard },
      { path: "live", Component: LiveRecording },
      { path: "upload", Component: FileAnalysis },
      { path: "reports", Component: Reports },
      { path: "analytics", Component: Analytics },
      { path: "settings", Component: Settings },
      { path: "profile", Component: Profile },
    ],
  },
]);
