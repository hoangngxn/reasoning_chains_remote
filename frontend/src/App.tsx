import { useEffect } from "react";

import { sessionState, useChatSession } from "@chainlit/react-client";
import { Playground } from "./components/playground";
import { useRecoilValue } from "recoil";
import { Route, Routes } from "react-router-dom";
import SignUp from "@/pages/SignUp";
import Login from "@/pages/Login";

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
      <Route path="/login" element={<Login />} />
      <Route path="/sign-up" element={<SignUp />} />
    </Routes>
  );
}

export default App;
