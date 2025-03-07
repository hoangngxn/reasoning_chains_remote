import { useEffect } from "react";
import { sessionState, useChatSession } from "@chainlit/react-client";
import { useRecoilValue } from "recoil";
import DashboardPage from "./pages/DashboardPage";
import Login from "./pages/Login";
import { Route, Routes, Navigate, Outlet } from "react-router-dom";
import SignUp from "@/pages/SignUp";
import DashboardLayout from "@/layouts/DashboardLayout";
import ChatPage from "@/pages/ChatPage";
import { useApp } from "./context/AppContext";
import OAuth2RedirectHandler from "@/components/OAuth2RedirectHandler";

function App() {
  const { user } = useApp();
  const { connect } = useChatSession();
  const session = useRecoilValue(sessionState);

  useEffect(() => {
    if (session?.socket.connected) return;
    if (user?.isAuthenticated) {
      const token = localStorage.getItem("token");
      connect({
        transports: ["websocket"],
        userEnv: {
          Authorization: `Bearer ${token}`,
          user_email: user.email,
        },
        withCredentials: true,
      });
    }
  }, [connect, user]);

  return (
    <Routes>
      <Route
        path="/"
        element={
          user?.isAuthenticated ? <DashboardLayout /> : <Navigate to="/login" />
        }
      />
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<DashboardLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="chats/:id" element={<ChatPage />} />
        </Route>
      </Route>
      <Route path="/login" element={<Login />} />
      <Route path="/sign-up" element={<SignUp />} />
      <Route path="/auth/google/callback" element={<OAuth2RedirectHandler />} />
    </Routes>
  );
}

// Protected Route Component
const ProtectedRoute = () => {
  const { user } = useApp();
  return user?.isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
};

export default App;
