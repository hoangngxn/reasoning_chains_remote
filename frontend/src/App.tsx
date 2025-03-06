import { useEffect } from "react";
import { sessionState, useChatSession } from "@chainlit/react-client";
import { useRecoilValue } from "recoil";
import { Route, Routes } from "react-router-dom";
import SignUp from "@/pages/SignUp";
import Login from "@/pages/Login";
import DashboardLayout from "@/layouts/DashboardLayout";
import DashboardPage from "@/pages/DashboardPage";
import ChatPage from "./pages/ChatPage";

const userEnv = {};
function App() {
  const { connect } = useChatSession();
  const session = useRecoilValue(sessionState);
  useEffect(() => {
    if (session?.socket.connected) {
      return;
    }
    fetch("http://localhost:80/custom-auth", { credentials: "include" }).then(
      () => {
        connect({
          userEnv,
        });
      }
    );
  }, [connect]);

  return (
    <Routes>
      <Route path="/dashboard" element={<DashboardLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="chats/:id" element={<ChatPage />} />
        </Route>
      <Route path="/login" element={<Login />} />
      <Route path="/sign-up" element={<SignUp />} />
    </Routes>
  );
}

export default App;
