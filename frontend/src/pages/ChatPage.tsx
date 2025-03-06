import { useLocation } from "react-router-dom";
import { useState, useEffect, useRef } from "react";
import Markdown from "react-markdown";
import { chatHistories } from "@/dataExample";
import FormInput from "../components/FormInput";

const ChatPage = () => {
  const path = useLocation().pathname;
  const chatId = path.split("/").pop() || "1";
  const [history, setHistory] = useState(chatHistories[chatId]?.history || []);
  const [question, setQuestion] = useState("");
  useEffect(() => {
    setHistory(chatHistories[chatId]?.history || []);
  }, [chatId]);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    chatContainerRef.current?.scrollTo({
      top: chatContainerRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [history]);

  return (
    <div className="flex flex-col items-center h-full w-full mt-16  overflow-hidden relative">
      <div
        className="flex-1 overflow-auto w-full flex justify-center mb-28"
        ref={chatContainerRef}
      >
        <div className="w-[65%] flex flex-col gap-5 p-4 ">
          {history.map((message, i) => (
            <div
              key={i}
              className={`p-4 max-w-[80%] rounded-xl ${
                message.role === "user"
                  ? "bg-[#d1d1d164] self-end text-black dark:bg-[#63636377] dark:text-white transition-all duration-700"
                  : "self-start text-black  dark:text-white transition-all duration-1000"
              }`}
            >
              <Markdown>{message.parts[0].text}</Markdown>
            </div>
          ))}
        </div>
      </div>
      <div className="w-[65%] mb-5 absolute bottom-0 bg-white dark:bg-[#63636377] rounded-2xl p-4 shadow-[0_2px_10px_rgba(0,0,0,0.15)] transition-colors duration-1000">
        <FormInput question={question} setQuestion={setQuestion} />
      </div>
    </div>
  );
};

export default ChatPage;
