import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import sidebarIcon from "../assets/img/sidebar.svg";
import newChatIcon from "../assets/img/newchat.svg";
import codecompleteImgLight from "./../assets/img/Logo-light.svg";
import codecompleteImgDark from "./../assets/img/Logo-dark.svg";
import googleIcon from "./../assets/img/google-icon.png";
import moonIcon from "./../assets/img/moon.svg";
import sunIcon from "./../assets/img/sun.svg";
import logoutIcon from "./../assets/img/logout.svg";
import { useChatSession } from "@chainlit/react-client";
import { useNavigate } from "react-router-dom";
import { useApp } from "@/context/AppContext";
interface HeaderProps {
  isSidebarOpen: boolean;
  setIsSidebarOpen: (open: boolean) => void;
}

const Header: React.FC<HeaderProps> = ({ isSidebarOpen, setIsSidebarOpen }) => {
  const navigate = useNavigate();
  const { user, setUserInfor } = useApp();
  const [isOpen, setIsOpen] = useState(false);
  const [isDark, setIsDark] = useState(
    localStorage.getItem("theme") === "dark"
  );
  const { disconnect } = useChatSession();

  const handleLogout = () => {
    localStorage.removeItem("token");
    setUserInfor({ token: "", email: "", isAuthenticated: false });
    disconnect();
    navigate("/login");
  };
  useEffect(() => {
    const root = document.documentElement;
    root.classList.add("transition-colors", "duration-2");

    if (isDark) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [isDark]);

  return (
    <div className="w-full flex justify-between items-center pl-5 pr-10 absolute top-0">
      <div className="flex items-center gap-5">
        {!isSidebarOpen && (
          <div className="flex gap-5">
            <button onClick={() => setIsSidebarOpen(true)}>
              <img
                src={sidebarIcon}
                alt="Open Sidebar"
                className="w-6 h-6 dark:invert transition-all duration-1000"
              />
            </button>
            <Link to="/dashboard">
              <img
                src={newChatIcon}
                alt="New Chat"
                className="w-8 h-8 dark:invert transition-all duration-1000"
              />
            </Link>
          </div>
        )}
        {/* Logo */}
        <div className="w-22 h-20 py-4">
          <img
            src={isDark ? codecompleteImgDark : codecompleteImgLight}
            alt="Code Complete"
            className="w-full h-full object-contain"
          />
        </div>
      </div>

      <div className="flex gap-5 items-center">
        {/* Toggle Light/Dark Mode */}
        <div
          className="w-6 h-6 cursor-pointer"
          onClick={() => setIsDark(!isDark)}
        >
          <img
            src={isDark ? moonIcon : sunIcon}
            alt="theme-icon"
            className="w-full h-full"
          />
        </div>

        {/* Google Avatar */}
        <div
          className="relative w-8 h-8 cursor-pointer"
          onClick={() => setIsOpen(!isOpen)}
        >
          <img src={googleIcon} alt="Google" className="w-full h-full" />
          {isOpen && (
            <div className="absolute right-0 mt-2 w-55 bg-white dark:bg-gray-800 shadow-lg rounded-md text-gray-700 dark:text-gray-200 z-50">
              <div className="p-3 flex flex-col justify-center items-center">
                <img className="w-12 h-12" src={googleIcon} alt="" />
                <span className="text-sm mt-2">{user?.email}</span>
              </div>
              <div className="p-3 flex justify-center border-t dark:border-gray-700">
                <img
                  className="opacity-70 dark:invert mr-2"
                  src={logoutIcon}
                  alt=""
                />
                <button
                  className="dark:hover:text-red-400"
                  onClick={handleLogout}
                >
                  Đăng xuất
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Header;
