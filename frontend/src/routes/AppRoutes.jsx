import React from "react";
import { Routes, Route, Navigate, useParams } from "react-router-dom";
import DashboardPage from "../pages/DashboardPage";
import HistoryPage from "../pages/HistoryPage";
import AnalysisPage from "../pages/AnalysisPage";
import SettingsPageWrapper from "../pages/SettingsPageWrapper";
import NotFoundPage from "../pages/NotFoundPage";

// Redirect component for /resume/:id -> /analysis/:id
const ResumeRedirect = () => {
  const { id } = useParams();
  return <Navigate to={`/analysis/${id}`} replace />;
};

const AppRoutes = () => {
  return (
    <Routes>
      {/* Main Dashboard Route */}
      <Route path="/" element={<DashboardPage />} />

      {/* Dashboard alias */}
      <Route path="/dashboard" element={<Navigate to="/" replace />} />

      {/* History & Analytics Route */}
      <Route path="/history" element={<HistoryPage />} />
      <Route path="/analytics" element={<Navigate to="/history" replace />} />

      {/* Settings Route */}
      <Route path="/settings" element={<SettingsPageWrapper />} />

      {/* Individual Analysis Routes */}
      <Route path="/analysis/:id" element={<AnalysisPage />} />
      <Route path="/resume/:id" element={<ResumeRedirect />} />

      {/* Catch-all 404 route */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};

export default AppRoutes;