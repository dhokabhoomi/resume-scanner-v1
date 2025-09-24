import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useTheme } from "../contexts/ThemeContext";
import "./NotFoundPage.css";

const NotFoundPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isDark } = useTheme();

  return (
    <div className={`not-found-page ${isDark ? "dark" : ""}`}>
      <div className="not-found-container">
        <div className="not-found-content">
          <div className="not-found-icon">
            <i className="bi bi-search"></i>
          </div>
          <h1 className="not-found-title">Page Not Found</h1>
          <p className="not-found-message">
            Sorry, the page <code>{location.pathname}</code> doesn't exist.
          </p>
          <p className="not-found-suggestion">
            You might be looking for one of these pages:
          </p>

          <div className="not-found-actions">
            <button
              onClick={() => navigate('/')}
              className="btn-primary"
            >
              <i className="bi bi-house"></i>
              Go to Dashboard
            </button>

            <button
              onClick={() => navigate('/history')}
              className="btn-secondary"
            >
              <i className="bi bi-graph-up"></i>
              View History & Analytics
            </button>

            <button
              onClick={() => navigate(-1)}
              className="btn-tertiary"
            >
              ← Go Back
            </button>
          </div>

          <div className="not-found-links">
            <h3>Quick Links:</h3>
            <ul>
              <li>
                <button onClick={() => navigate('/')} className="link-button">
                  Resume Upload & Analysis
                </button>
              </li>
              <li>
                <button onClick={() => navigate('/history')} className="link-button">
                  History & Analytics Dashboard
                </button>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotFoundPage;