import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useNavigation } from "../contexts/NavigationContext";
import AnalysisResultsPage from "../components/AnalysisResultsPage";

const AnalysisPage = () => {
  const { goToHistory, goToDashboard } = useNavigation();
  const { id } = useParams();
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadAnalysisData = () => {
      try {
        // First try to get from sessionStorage (set by HistoryPage)
        const storedAnalysis = sessionStorage.getItem('currentAnalysis');

        if (storedAnalysis) {
          const parsed = JSON.parse(storedAnalysis);
          // Handle both string and number ID comparisons
          if (String(parsed.id) === String(id)) {
            setAnalysisData(parsed);
            setLoading(false);
            return;
          }
        }

        // Fallback: Try to find in localStorage recentAnalyses
        const recentAnalyses = JSON.parse(localStorage.getItem('recentAnalyses')) || [];
        const foundAnalysis = recentAnalyses.find(analysis => String(analysis.id) === String(id));

        if (foundAnalysis) {
          // Debug logging for troubleshooting
          console.log("AnalysisPage - Found analysis:", foundAnalysis);
          console.log("AnalysisPage - Analysis status:", foundAnalysis.status);
          console.log("AnalysisPage - fullAnalysis present:", !!foundAnalysis.fullAnalysis);
          console.log("AnalysisPage - full_analysis present:", !!foundAnalysis.full_analysis);
          console.log("AnalysisPage - Keys in analysis:", Object.keys(foundAnalysis));

          // Check if analysis is still processing
          if (foundAnalysis.status === "processing") {
            setError("Analysis is still processing. Please wait for completion before viewing details.");
            setLoading(false);
            return;
          }

          // Get full analysis from either fullAnalysis or full_analysis field
          const fullAnalysisData = foundAnalysis.fullAnalysis || foundAnalysis.full_analysis;

          // Transform to the expected format
          const transformedData = {
            id: foundAnalysis.id,
            candidateName: foundAnalysis.candidateName ||
                          foundAnalysis.name ||
                          fullAnalysisData?.analysis?.candidate_name ||
                          foundAnalysis.fileName?.replace(/\.[^/.]+$/, "") ||
                          "Unknown Candidate",
            fileName: foundAnalysis.fileName,
            position: fullAnalysisData?.analysis?.target_position || "General Application",
            date: foundAnalysis.date ? foundAnalysis.date.split("T")[0] : new Date().toISOString().split("T")[0],
            overallScore: foundAnalysis.score || fullAnalysisData?.analysis?.overall_score || 0,
            skills: foundAnalysis.priorities || [],
            fullAnalysis: fullAnalysisData,
            full_analysis: foundAnalysis.full_analysis, // Include both formats for compatibility
            uploadedAt: foundAnalysis.uploadedAt,
            jobId: foundAnalysis.jobId,
            status: foundAnalysis.status || "completed",
          };

          setAnalysisData(transformedData);
        } else {
          setError("Analysis not found. It may have been deleted or expired.");
        }
      } catch (err) {
        console.error("Error loading analysis data:", err);
        setError("Failed to load analysis data.");
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      loadAnalysisData();
    } else {
      setError("Invalid analysis ID.");
      setLoading(false);
    }
  }, [id]);

  const handleBackToDashboard = () => {
    // Clear the stored analysis data
    sessionStorage.removeItem('currentAnalysis');
    goToDashboard();
  };

  const handleDownloadReportCSV = () => {
    if (!analysisData) return;

    // Get current priority configuration from settings
    let selectedPriorities = [];
    let priorityWeights = {};

    try {
      const savedSettings = localStorage.getItem("resumeAnalyzerSettings");
      if (savedSettings) {
        const settings = JSON.parse(savedSettings);
        selectedPriorities = settings.defaultPriorities || ["Technical Skills", "Work Experience", "Academic Performance"];
      } else {
        selectedPriorities = ["Technical Skills", "Work Experience", "Academic Performance"];
      }

      // Calculate priority weights
      if (selectedPriorities.length > 0) {
        const totalPriorities = selectedPriorities.length;
        for (let i = 0; i < totalPriorities; i++) {
          const priority = selectedPriorities[i];
          const weight = Math.round(((totalPriorities - i) / ((totalPriorities * (totalPriorities + 1)) / 2)) * 100);
          priorityWeights[priority] = weight;
        }
      }
    } catch (error) {
      console.error("Error getting priority settings:", error);
      selectedPriorities = ["Technical Skills", "Work Experience", "Academic Performance"];
    }

    // Map priority names to their scores in the analysis
    const scoreMapping = {
      "Technical Skills": analysisData.fullAnalysis?.analysis?.technical_skills_score ||
                       analysisData.fullAnalysis?.analysis?.skills_score ||
                       analysisData.technicalSkills || 0,
      "Work Experience": analysisData.fullAnalysis?.analysis?.experience_score ||
                       analysisData.fullAnalysis?.analysis?.work_experience_score ||
                       analysisData.experience || 0,
      "Academic Performance": analysisData.fullAnalysis?.analysis?.academic_performance_score ||
                            analysisData.fullAnalysis?.analysis?.education_score ||
                            analysisData.education || 0,
      "Project Experience": analysisData.fullAnalysis?.analysis?.project_experience_score ||
                          analysisData.fullAnalysis?.analysis?.projects_score || 0,
      "Certifications": analysisData.fullAnalysis?.analysis?.certifications_score ||
                      analysisData.fullAnalysis?.analysis?.certification_score || 0,
      "Resume Formatting": analysisData.fullAnalysis?.analysis?.resume_formatting_score ||
                         analysisData.fullAnalysis?.analysis?.formatting_score || 0,
      "Skill Diversity": analysisData.fullAnalysis?.analysis?.skill_diversity_score ||
                       analysisData.fullAnalysis?.analysis?.diversity_score || 0,
      "Extracurricular Activities": analysisData.fullAnalysis?.analysis?.extracurricular_score ||
                                  analysisData.fullAnalysis?.analysis?.extracurriculars_score || 0,
      "CGPA Scores": analysisData.fullAnalysis?.analysis?.cgpa_score ||
                   analysisData.fullAnalysis?.analysis?.gpa_score || 0
    };

    // Create CSV content
    const csvHeaders = ["Field", "Value"];
    const csvRows = [
      ["Candidate Name", analysisData.candidateName],
      ["File Name", analysisData.fileName],
      ["Analysis Date", new Date(analysisData.date).toLocaleDateString()],
      ["Overall Score", `${analysisData.overallScore}%`],
      ["", ""], // Empty row for separation
      ["Selected Priority Configuration", selectedPriorities.join(', ')],
      ["", ""], // Empty row for separation
    ];

    // Add priority scores and weights
    selectedPriorities.forEach(priority => {
      csvRows.push([`${priority} Score`, scoreMapping[priority] || 0]);
      csvRows.push([`${priority} Weight`, `${priorityWeights[priority] || 0}%`]);
    });

    // Add skills/priorities list if available
    if (analysisData.priorities && analysisData.priorities.length > 0) {
      csvRows.push(["", ""]); // Empty row for separation
      csvRows.push(["Skills/Priorities", ""]);
      analysisData.priorities.forEach((skill, index) => {
        csvRows.push([`Skill ${index + 1}`, skill]);
      });
    }

    const csvContent = [
      csvHeaders.join(","),
      ...csvRows.map(row => `"${row[0]}","${row[1]}"`)
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${analysisData.candidateName.replace(/[^a-zA-Z0-9]/g, "_")}_analysis_report.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handleDownloadReportPDF = () => {
    if (!analysisData) return;

    // Get current priority configuration from settings
    let selectedPriorities = [];
    let priorityWeights = {};

    try {
      const savedSettings = localStorage.getItem("resumeAnalyzerSettings");
      if (savedSettings) {
        const settings = JSON.parse(savedSettings);
        selectedPriorities = settings.defaultPriorities || ["Technical Skills", "Work Experience", "Academic Performance"];
      } else {
        selectedPriorities = ["Technical Skills", "Work Experience", "Academic Performance"];
      }

      // Calculate priority weights
      if (selectedPriorities.length > 0) {
        const totalPriorities = selectedPriorities.length;
        for (let i = 0; i < totalPriorities; i++) {
          const priority = selectedPriorities[i];
          const weight = Math.round(((totalPriorities - i) / ((totalPriorities * (totalPriorities + 1)) / 2)) * 100);
          priorityWeights[priority] = weight;
        }
      }
    } catch (error) {
      console.error("Error getting priority settings:", error);
      selectedPriorities = ["Technical Skills", "Work Experience", "Academic Performance"];
    }

    // Map priority names to their scores in the analysis
    const scoreMapping = {
      "Technical Skills": analysisData.fullAnalysis?.analysis?.technical_skills_score ||
                       analysisData.fullAnalysis?.analysis?.skills_score ||
                       analysisData.technicalSkills || 0,
      "Work Experience": analysisData.fullAnalysis?.analysis?.experience_score ||
                       analysisData.fullAnalysis?.analysis?.work_experience_score ||
                       analysisData.experience || 0,
      "Academic Performance": analysisData.fullAnalysis?.analysis?.academic_performance_score ||
                            analysisData.fullAnalysis?.analysis?.education_score ||
                            analysisData.education || 0,
      "Project Experience": analysisData.fullAnalysis?.analysis?.project_experience_score ||
                          analysisData.fullAnalysis?.analysis?.projects_score || 0,
      "Certifications": analysisData.fullAnalysis?.analysis?.certifications_score ||
                      analysisData.fullAnalysis?.analysis?.certification_score || 0,
      "Resume Formatting": analysisData.fullAnalysis?.analysis?.resume_formatting_score ||
                         analysisData.fullAnalysis?.analysis?.formatting_score || 0,
      "Skill Diversity": analysisData.fullAnalysis?.analysis?.skill_diversity_score ||
                       analysisData.fullAnalysis?.analysis?.diversity_score || 0,
      "Extracurricular Activities": analysisData.fullAnalysis?.analysis?.extracurricular_score ||
                                  analysisData.fullAnalysis?.analysis?.extracurriculars_score || 0,
      "CGPA Scores": analysisData.fullAnalysis?.analysis?.cgpa_score ||
                   analysisData.fullAnalysis?.analysis?.gpa_score || 0
    };

    // Create HTML content for PDF
    const htmlContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Resume Analysis Report - ${analysisData.candidateName}</title>
          <style>
            body {
              font-family: Arial, sans-serif;
              margin: 40px;
              line-height: 1.6;
              color: #333;
            }
            .header {
              text-align: center;
              border-bottom: 3px solid #4f46e5;
              padding-bottom: 20px;
              margin-bottom: 30px;
            }
            .header h1 {
              color: #4f46e5;
              margin: 0;
              font-size: 28px;
            }
            .header h2 {
              color: #666;
              margin: 10px 0 0 0;
              font-weight: normal;
              font-size: 18px;
            }
            .section {
              margin-bottom: 30px;
            }
            .section h3 {
              color: #4f46e5;
              border-bottom: 2px solid #e5e7eb;
              padding-bottom: 10px;
              margin-bottom: 15px;
            }
            .info-grid {
              display: grid;
              grid-template-columns: 1fr 1fr;
              gap: 20px;
              margin-bottom: 20px;
            }
            .info-item {
              display: flex;
              justify-content: space-between;
              padding: 10px;
              background-color: #f9fafb;
              border-radius: 6px;
            }
            .info-label {
              font-weight: bold;
              color: #374151;
            }
            .info-value {
              color: #6b7280;
            }
            .score-grid {
              display: grid;
              grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
              gap: 15px;
              margin-top: 20px;
            }
            .score-item {
              padding: 15px;
              border: 1px solid #e5e7eb;
              border-radius: 8px;
              background-color: #f9fafb;
            }
            .score-name {
              font-weight: bold;
              color: #374151;
              margin-bottom: 5px;
            }
            .score-value {
              font-size: 24px;
              font-weight: bold;
              color: #4f46e5;
            }
            .score-weight {
              font-size: 12px;
              color: #6b7280;
              margin-top: 5px;
            }
            .skills-list {
              display: flex;
              flex-wrap: wrap;
              gap: 8px;
              margin-top: 10px;
            }
            .skill-tag {
              background-color: #4f46e5;
              color: white;
              padding: 4px 8px;
              border-radius: 4px;
              font-size: 12px;
            }
            .overall-score {
              text-align: center;
              font-size: 48px;
              font-weight: bold;
              color: #4f46e5;
              margin: 20px 0;
            }
            .generated-date {
              text-align: center;
              color: #6b7280;
              font-size: 12px;
              margin-top: 40px;
              border-top: 1px solid #e5e7eb;
              padding-top: 20px;
            }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>Resume Analysis Report</h1>
            <h2>${analysisData.candidateName}</h2>
          </div>

          <div class="section">
            <h3>Basic Information</h3>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">Candidate Name:</span>
                <span class="info-value">${analysisData.candidateName}</span>
              </div>
              <div class="info-item">
                <span class="info-label">File Name:</span>
                <span class="info-value">${analysisData.fileName}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Analysis Date:</span>
                <span class="info-value">${new Date(analysisData.date).toLocaleDateString()}</span>
              </div>
            </div>
          </div>

          <div class="section">
            <h3>Overall Score</h3>
            <div class="overall-score">${analysisData.overallScore}%</div>
          </div>

          <div class="section">
            <h3>Priority Configuration</h3>
            <div class="info-item">
              <span class="info-label">Selected Priorities:</span>
              <span class="info-value">${selectedPriorities.join(', ')}</span>
            </div>
          </div>

          <div class="section">
            <h3>Priority Scores & Weights</h3>
            <div class="score-grid">
              ${selectedPriorities.map(priority => `
                <div class="score-item">
                  <div class="score-name">${priority}</div>
                  <div class="score-value">${scoreMapping[priority] || 0}</div>
                  <div class="score-weight">Weight: ${priorityWeights[priority] || 0}%</div>
                </div>
              `).join('')}
            </div>
          </div>

          ${analysisData.priorities && analysisData.priorities.length > 0 ? `
          <div class="section">
            <h3>Skills & Priorities</h3>
            <div class="skills-list">
              ${analysisData.priorities.map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
            </div>
          </div>
          ` : ''}

          <div class="generated-date">
            Report generated on ${new Date().toLocaleString()}
          </div>
        </body>
      </html>
    `;

    // Create a new window to print the PDF
    const printWindow = window.open('', '_blank');
    printWindow.document.write(htmlContent);
    printWindow.document.close();

    // Wait for content to load then trigger print dialog
    setTimeout(() => {
      printWindow.print();
    }, 500);
  };

  const [showExportDropdown, setShowExportDropdown] = useState(false);

  const handleShareReport = () => {
    if (!analysisData) return;

    // Copy the current URL to clipboard
    navigator.clipboard.writeText(window.location.href).then(() => {
      alert(`Analysis link copied to clipboard! Share this URL: ${window.location.href}`);
    }).catch(() => {
      alert(`Share this URL: ${window.location.href}`);
    });
  };

  if (loading) {
    return (
      <div className="analysis-page-container">
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <p>Loading analysis...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analysis-page-container">
        <div className="error-container">
          <h2>Analysis Not Found</h2>
          <p>{error}</p>
          <div className="error-actions">
            <button onClick={goToHistory} className="btn-primary">
              Back to History
            </button>
            <button onClick={goToDashboard} className="btn-secondary">
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Remove the blocking check - let AnalysisResultsPage handle missing data gracefully

  return (
    <div className="analysis-page-container">
      <AnalysisResultsPage
        analysisData={analysisData}
        onBackToDashboard={handleBackToDashboard}
        onDownloadReportCSV={handleDownloadReportCSV}
        onDownloadReportPDF={handleDownloadReportPDF}
        onShareReport={handleShareReport}
        showExportDropdown={showExportDropdown}
        setShowExportDropdown={setShowExportDropdown}
      />
    </div>
  );
};

export default AnalysisPage;