import FormInput from "../components/FormInput";
import { useState } from "react";

const DashboardPage = () => {
  const [question, setQuestion] = useState("");
  return (
    <div className="h-screen w-full flex justify-center items-center ">
      <div className="w-1/2 flex flex-col items-center gap-8">
        <h1 className="text-3xl font-bold text-black dark:text-white ">
          Tôi có thể giúp gì cho bạn?
        </h1>
        <div className="w-full bg-white dark:bg-[#63636377] rounded-2xl p-4 shadow-[0_2px_10px_rgba(0,0,0,0.15)] transition-colors duration-1000">
          <FormInput question={question} setQuestion={setQuestion} />
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
