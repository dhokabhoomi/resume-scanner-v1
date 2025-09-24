import React from "react";
import { useLocation } from "react-router-dom";
import { useNavigation } from "../contexts/NavigationContext";
import { useTheme } from "../contexts/ThemeContext";
import "./StickyNavigation.css";

const StickyNavigation = () => {
  const location = useLocation();
  const { goToDashboard, goToHistory, goToSettings } = useNavigation();
  const { isDark, toggleTheme } = useTheme();

  const isActive = (path) => {
    if (path === "/" || path === "/dashboard") {
      return location.pathname === "/" || location.pathname === "/dashboard";
    }
    return location.pathname.startsWith(path);
  };

  return (
    <nav className="sticky-navigation">
      <div className="nav-container">
        <div className="nav-left">
          <div className="logo-section">
            <h1 className="nav-title">Resume Analyzer</h1>
          </div>
        </div>

        <div className="nav-center">
          <button
            className={`nav-button ${isActive("/") ? "active" : ""}`}
            onClick={goToDashboard}
            title="Go to Dashboard"
          >
            Dashboard
          </button>
          <button
            className={`nav-button ${isActive("/history") ? "active" : ""}`}
            onClick={goToHistory}
            title="View History & Analytics"
          >
            History & Analytics
          </button>
        </div>

        <div className="nav-right">
          <button
            className={`nav-button ${isActive("/settings") ? "active" : ""}`}
            onClick={goToSettings}
            title="Settings"
          >
            Settings
          </button>
          <button
            className="theme-toggle"
            onClick={toggleTheme}
            title={`Switch to ${isDark ? "light" : "dark"} mode`}
          >
            <i className={isDark ? "bi bi-sun" : "bi bi-moon"}></i>
          </button>
        </div>
      </div>
    </nav>
  );
};

export default StickyNavigation;
