import React, { useState, useEffect } from "react";
import { useNavigation } from "../contexts/NavigationContext";
import HistoryAnalytics from "../components/HistoryAnalytics";
import ErrorBoundary from "../components/ErrorBoundary";

const HistoryPage = () => {
  const { goToDashboard, goToAnalysis } = useNavigation();
  const [hasError, setHasError] = useState(false);

  const handleBackToDashboard = () => {
    goToDashboard();
  };

  const handleViewHistoryDetails = (item) => {
    // Store the data in sessionStorage to persist across navigation
    sessionStorage.setItem('currentAnalysis', JSON.stringify(item));
    goToAnalysis(item.id);
  };

  // Simple fallback component if HistoryAnalytics fails
  const FallbackHistory = () => {
    const [analyses, setAnalyses] = useState([]);

    useEffect(() => {
      try {
        const storedAnalyses = JSON.parse(localStorage.getItem("recentAnalyses")) || [];
        setAnalyses(storedAnalyses);
      } catch (error) {
        console.error("Error loading analyses:", error);
      }
    }, []);

    return (
      <div style={{ padding: '2rem' }}>
        <div style={{ marginBottom: '2rem' }}>
          <h1>History & Analytics</h1>
          <button onClick={handleBackToDashboard} style={{
            padding: '0.5rem 1rem',
            cursor: 'pointer',
            marginRight: '1rem'
          }}>
            Back to Dashboard
          </button>
        </div>

        <div>
          <h2>Recent Analyses ({analyses.length})</h2>
          {analyses.length === 0 ? (
            <p>No analyses found. Upload some resumes to see them here.</p>
          ) : (
            <div style={{ display: 'grid', gap: '1rem' }}>
              {analyses.map((analysis) => (
                <div key={analysis.id} style={{
                  border: '1px solid #ccc',
                  padding: '1rem',
                  borderRadius: '4px'
                }}>
                  <h3>{analysis.candidateName || analysis.fileName || 'Unknown'}</h3>
                  <p>Score: {analysis.score || 0}%</p>
                  <p>Date: {analysis.date ? new Date(analysis.date).toLocaleDateString() : 'Unknown'}</p>
                  <button onClick={() => handleViewHistoryDetails(analysis)} style={{
                    padding: '0.25rem 0.5rem',
                    cursor: 'pointer'
                  }}>
                    View Details
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  if (hasError) {
    return <FallbackHistory />;
  }

  return (
    <div className="history-page">
      <ErrorBoundary>
        <HistoryAnalytics
          onBackToDashboard={handleBackToDashboard}
          onViewDetails={handleViewHistoryDetails}
        />
      </ErrorBoundary>
    </div>
  );
};

export default HistoryPage;