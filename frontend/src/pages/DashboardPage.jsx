import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useNavigation } from "../contexts/NavigationContext";
import EnhancedDashboard from "../components/EnhancedDashboard";
import { API_ENDPOINTS } from "../config/api";

const DashboardPage = () => {
  const navigate = useNavigate();
  const { goToAnalysis } = useNavigation();
  // Removed unused state variables
  const [candidatesData] = useState([]);

  const handleUploadSuccess = (data) => {
    console.log("Upload success data:", data);
    // Upload success handled by EnhancedDashboard component
  };

  const handleViewCandidateDetails = (analysis) => {
    // Ensure we have an ID - use existing one or generate if missing
    if (!analysis.id) {
      console.error("Analysis missing ID:", analysis);
      return;
    }

    // Store the analysis data in sessionStorage to persist across navigation
    sessionStorage.setItem('currentAnalysis', JSON.stringify(analysis));
    // Navigate to the analysis page with the analysis ID
    goToAnalysis(analysis.id);
  };


  return (
    <EnhancedDashboard
      candidatesData={candidatesData}
      onNavigateToUpload={() => navigate('/')}
      onViewDetails={handleViewCandidateDetails}
      onUploadSuccess={handleUploadSuccess}
    />
  );
};

export default DashboardPage;