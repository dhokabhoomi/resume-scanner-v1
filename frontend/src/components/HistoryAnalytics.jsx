import React, { useState, useEffect, useMemo } from "react";
import "./HistoryAnalytics.css";

// Function to determine department based on analysis data
const determineDepartment = (analysis) => {
  if (!analysis) return null;

  // Extract skills data from multiple potential sources
  const skillSources = [
    // From priorities array (most common)
    ...(analysis.priorities || []),
    ...(analysis.skills || []),

    // From fullAnalysis skills if available
    ...(analysis.fullAnalysis?.analysis?.skills?.content?.technical_skills?.programming_languages || []),
    ...(analysis.fullAnalysis?.analysis?.skills?.content?.technical_skills?.frameworks_libraries || []),
    ...(analysis.fullAnalysis?.analysis?.skills?.content?.hard_skills?.domain_specific || []),

    // From work experience and projects
    ...(analysis.fullAnalysis?.analysis?.work_experience?.content?.positions || []),
    ...(analysis.fullAnalysis?.analysis?.projects?.content?.project_names || []),
  ];

  // Create search text from skills and candidate info
  const searchText = [
    ...skillSources,
    analysis.candidateName || "",
    analysis.fileName || "",
    analysis.fullAnalysis?.analysis?.professional_summary?.content?.summary_text || ""
  ].join(" ").toLowerCase();

  // Simplified department keywords for better matching
  const departmentKeywords = {
    Engineering: [
      "software", "developer", "programming", "javascript", "python", "java", "react", "node",
      "frontend", "backend", "fullstack", "web development", "mobile development", "devops",
      "git", "database", "api", "framework", "html", "css", "angular", "vue", "spring"
    ],
    "Data Science": [
      "data science", "machine learning", "analytics", "python", "r programming", "sql",
      "tableau", "statistics", "data analysis", "ml", "ai", "tensorflow", "pandas", "numpy"
    ],
    Design: [
      "ui", "ux", "design", "figma", "photoshop", "adobe", "prototype", "wireframe",
      "user interface", "user experience", "graphic design", "visual design"
    ],
    Marketing: [
      "marketing", "digital marketing", "seo", "social media", "content marketing",
      "brand", "campaign", "advertising"
    ],
    Business: [
      "business analyst", "project manager", "management", "strategy", "operations",
      "finance", "accounting", "hr", "human resources"
    ]
  };

  // Find best matching department
  let bestMatch = null;
  let highestScore = 0;

  for (const [department, keywords] of Object.entries(departmentKeywords)) {
    const matchCount = keywords.filter(keyword =>
      searchText.includes(keyword.toLowerCase())
    ).length;

    if (matchCount > highestScore) {
      highestScore = matchCount;
      bestMatch = department;
    }
  }

  // Only return a department if we found actual matches
  return highestScore > 0 ? bestMatch : null;
};

const HistoryAnalytics = ({ onBackToDashboard, onViewDetails }) => {
  // Load real data from localStorage
  const [historyData, setHistoryData] = useState([]);

  useEffect(() => {
    const loadHistoryData = () => {
      const storedAnalyses =
        JSON.parse(localStorage.getItem("recentAnalyses")) || [];

      // Clean up old processing entries (older than 10 minutes)
      const tenMinutesAgo = Date.now() - 10 * 60 * 1000;
      const cleanedAnalyses = storedAnalyses.map((analysis) => {
        if (analysis.status === "processing") {
          const analysisTime = new Date(
            analysis.timestamp || analysis.date
          ).getTime();
          if (analysisTime < tenMinutesAgo) {
            // Mark old processing entries as completed
            return { ...analysis, status: "completed" };
          }
        }
        return analysis;
      });

      // Update localStorage if we made any changes
      if (JSON.stringify(cleanedAnalyses) !== JSON.stringify(storedAnalyses)) {
        localStorage.setItem("recentAnalyses", JSON.stringify(cleanedAnalyses));
      }

      // Transform the existing localStorage data to our expected format
      const transformedData = cleanedAnalyses.map((analysis) => {
        try {
          return {
        id: analysis.id,
        candidateName:
          analysis.candidateName ||
          analysis.fullAnalysis?.analysis?.basic_info?.content?.name ||
          analysis.fullAnalysis?.analysis?.candidate_name ||
          analysis.name?.replace(/\.[^/.]+$/, "") || // Remove file extension
          analysis.fileName?.replace(/\.[^/.]+$/, "") ||
          "Unknown Candidate",
        fileName: analysis.fileName,
        position:
          analysis.fullAnalysis?.analysis?.target_position ||
          "General Application",
        date: analysis.date
          ? analysis.date.split("T")[0]
          : new Date().toISOString().split("T")[0],
        overallScore: (() => {
          // Try multiple score extraction paths
          const possibleScores = [
            analysis.fullAnalysis?.analysis?.overall_score,
            analysis.fullAnalysis?.overall_score,
            analysis.score,
            analysis.overallScore,
            analysis.fullAnalysis?.data?.overall_score,
            analysis.fullAnalysis?.score,
          ];

          for (const score of possibleScores) {
            if (typeof score === "number" && score > 0) {
              console.log(`Score extracted for ${analysis.fileName}: ${score}`); // Debug log
              return Math.round(score);
            }
          }
          console.log(
            `No valid score found for ${analysis.fileName}, available:`,
            possibleScores
          ); // Debug log
          return 0;
        })(),
        technicalSkills:
          analysis.fullAnalysis?.analysis?.technical_skills_score ||
          analysis.score ||
          0,
        experience:
          analysis.fullAnalysis?.analysis?.experience_score ||
          analysis.score ||
          0,
        education:
          analysis.fullAnalysis?.analysis?.education_score ||
          analysis.score ||
          0,
        skills: analysis.priorities || [],
        department: (() => {
          try {
            return determineDepartment(analysis);
          } catch (error) {
            console.error("Error determining department for analysis:", analysis, error);
            return null;
          }
        })(),
        status: analysis.status || "completed",
            uploadedAt: analysis.uploadedAt,
            jobId: analysis.jobId,
            fullAnalysis: analysis.fullAnalysis, // Keep the full analysis for viewing details
          };
        } catch (error) {
          console.error("Error transforming analysis:", analysis, error);
          // Return a safe fallback object
          return {
            id: analysis.id || Math.random().toString(),
            candidateName: analysis.candidateName || analysis.fileName || "Unknown",
            fileName: analysis.fileName || "Unknown",
            position: "General Application",
            date: new Date().toISOString().split("T")[0],
            overallScore: 0,
            technicalSkills: 0,
            experience: 0,
            education: 0,
            skills: [],
            department: null,
            status: "completed",
            uploadedAt: analysis.uploadedAt,
            jobId: analysis.jobId,
            fullAnalysis: null,
          };
        }
      });

      setHistoryData(transformedData);
    };

    loadHistoryData();

    // Listen for storage changes to update data in real-time
    const handleStorageChange = (event) => {
      if (event.key === "recentAnalyses") {
        loadHistoryData();
      }
    };

    // Close dropdowns when clicking outside
    const handleClickOutside = (event) => {
      const dropdowns = document.querySelectorAll('.dropdown-menu');
      dropdowns.forEach(dropdown => {
        if (!dropdown.closest('.dropdown-wrapper').contains(event.target)) {
          dropdown.style.display = 'none';
        }
      });
    };

    window.addEventListener("storage", handleStorageChange);
    document.addEventListener("click", handleClickOutside);

    return () => {
      window.removeEventListener("storage", handleStorageChange);
      document.removeEventListener("click", handleClickOutside);
    };
  }, []);


  // Filter states
  const [filters, setFilters] = useState({
    dateRange: { start: "", end: "" },
    department: "",
    scoreRange: { min: 0, max: 100 },
    searchName: "",
    position: "",
  });

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  // Bulk actions states
  const [selectedItems, setSelectedItems] = useState([]);
  const [selectAll, setSelectAll] = useState(false);

  // Filtered and paginated data
  const filteredData = useMemo(() => {
    return historyData.filter((item) => {
      const matchesName = item.candidateName
        .toLowerCase()
        .includes(filters.searchName.toLowerCase());
      const matchesDepartment =
        !filters.department || item.department === filters.department;
      const matchesScore =
        item.overallScore >= filters.scoreRange.min &&
        item.overallScore <= filters.scoreRange.max;
      const matchesPosition =
        !filters.position ||
        item.position.toLowerCase().includes(filters.position.toLowerCase());

      let matchesDate = true;
      if (filters.dateRange.start && filters.dateRange.end) {
        const itemDate = new Date(item.date);
        const startDate = new Date(filters.dateRange.start);
        const endDate = new Date(filters.dateRange.end);
        matchesDate = itemDate >= startDate && itemDate <= endDate;
      }

      return (
        matchesName &&
        matchesDepartment &&
        matchesScore &&
        matchesDate &&
        matchesPosition
      );
    });
  }, [historyData, filters]);

  // Paginated data
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredData.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredData, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(filteredData.length / itemsPerPage);

  // Analytics calculations
  const analytics = useMemo(() => {
    if (filteredData.length === 0) return null;

    try {
      const avgScore =
        filteredData.reduce((sum, item) => {
          const score = typeof item.overallScore === 'number' ? item.overallScore : 0;
          return sum + score;
        }, 0) / filteredData.length;

    // Score distribution
    const scoreRanges = {
      "90-100": filteredData.filter((item) => {
        const score = typeof item.overallScore === 'number' ? item.overallScore : 0;
        return score >= 90;
      }).length,
      "80-89": filteredData.filter((item) => {
        const score = typeof item.overallScore === 'number' ? item.overallScore : 0;
        return score >= 80 && score < 90;
      }).length,
      "70-79": filteredData.filter((item) => {
        const score = typeof item.overallScore === 'number' ? item.overallScore : 0;
        return score >= 70 && score < 80;
      }).length,
      "60-69": filteredData.filter((item) => {
        const score = typeof item.overallScore === 'number' ? item.overallScore : 0;
        return score >= 60 && score < 70;
      }).length,
      "Below 60": filteredData.filter((item) => {
        const score = typeof item.overallScore === 'number' ? item.overallScore : 0;
        return score < 60;
      }).length,
    };

    // Most common skills
    const skillCounts = {};
    filteredData.forEach((item) => {
      // Ensure skills is an array before iterating
      const skills = Array.isArray(item.skills) ? item.skills : [];
      skills.forEach((skill) => {
        if (skill && typeof skill === 'string') {
          skillCounts[skill] = (skillCounts[skill] || 0) + 1;
        }
      });
    });
    const topSkills = Object.entries(skillCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10);

    // Department distribution
    const departmentCounts = {};
    filteredData.forEach((item) => {
      if (item.department) { // Only count items with actual departments
        departmentCounts[item.department] =
          (departmentCounts[item.department] || 0) + 1;
      }
    });

      return {
        avgScore: Math.round(avgScore * 10) / 10,
        totalCandidates: filteredData.length,
        scoreRanges,
        topSkills,
        departmentCounts,
      };
    } catch (error) {
      console.error("Error calculating analytics:", error);
      return null;
    }
  }, [filteredData]);

  const handleFilterChange = (filterType, value) => {
    setFilters((prev) => ({
      ...prev,
      [filterType]: value,
    }));
    setCurrentPage(1); // Reset to first page when filters change
  };

  const handleClearFilters = () => {
    setFilters({
      dateRange: { start: "", end: "" },
      department: "",
      scoreRange: { min: 0, max: 100 },
      searchName: "",
      position: "",
    });
    setCurrentPage(1);
    // Also clear selections when filters are cleared
    setSelectedItems([]);
    setSelectAll(false);
  };

  const getScoreColor = (score) => {
    if (score >= 90) return "#059669"; // green - excellent
    if (score >= 80) return "#2563eb"; // blue - good
    if (score >= 70) return "#d97706"; // amber - average
    if (score >= 60) return "#ea580c"; // orange - below average
    return "#dc2626"; // red - poor
  };

  // Action button handlers
  const handleViewDetails = (item) => {
    if (onViewDetails) {
      // Always try to show analysis if we have the handler, even with limited data
      onViewDetails(item);
    } else {
      // Fallback alert if no onViewDetails prop is provided
      alert(
        `View Details for ${item.candidateName}\n\nScore: ${
          item.overallScore
        }%\nFile: ${item.fileName}\nDate: ${new Date(
          item.date
        ).toLocaleDateString()}\n\n${
          !item.fullAnalysis
            ? "Note: Limited analysis data (bulk processed)"
            : ""
        }`
      );
    }
  };

  const handleDownloadReportCSV = (item) => {
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
      "Technical Skills": item.fullAnalysis?.analysis?.technical_skills_score ||
                       item.fullAnalysis?.analysis?.skills_score ||
                       item.technicalSkills || 0,
      "Work Experience": item.fullAnalysis?.analysis?.experience_score ||
                       item.fullAnalysis?.analysis?.work_experience_score ||
                       item.experience || 0,
      "Academic Performance": item.fullAnalysis?.analysis?.academic_performance_score ||
                            item.fullAnalysis?.analysis?.education_score ||
                            item.education || 0,
      "Project Experience": item.fullAnalysis?.analysis?.project_experience_score ||
                          item.fullAnalysis?.analysis?.projects_score || 0,
      "Certifications": item.fullAnalysis?.analysis?.certifications_score ||
                      item.fullAnalysis?.analysis?.certification_score || 0,
      "Resume Formatting": item.fullAnalysis?.analysis?.resume_formatting_score ||
                         item.fullAnalysis?.analysis?.formatting_score || 0,
      "Skill Diversity": item.fullAnalysis?.analysis?.skill_diversity_score ||
                       item.fullAnalysis?.analysis?.diversity_score || 0,
      "Extracurricular Activities": item.fullAnalysis?.analysis?.extracurricular_score ||
                                  item.fullAnalysis?.analysis?.extracurriculars_score || 0,
      "CGPA Scores": item.fullAnalysis?.analysis?.cgpa_score ||
                   item.fullAnalysis?.analysis?.gpa_score || 0
    };

    // Create CSV content
    const csvHeaders = [
      "Field", "Value"
    ];

    const csvRows = [
      ["Candidate Name", item.candidateName],
      ["File Name", item.fileName],
      ["Analysis Date", new Date(item.date).toLocaleDateString()],
      ["Overall Score", `${item.overallScore}%`],
      ["Status", item.status],
      ["", ""], // Empty row for separation
      ["Selected Priority Configuration", selectedPriorities.join(', ')],
      ["", ""], // Empty row for separation
    ];

    // Add priority scores and weights
    selectedPriorities.forEach(priority => {
      csvRows.push([`${priority} Score`, scoreMapping[priority] || 0]);
      csvRows.push([`${priority} Weight`, `${priorityWeights[priority] || 0}%`]);
    });

    // Add skills/priorities list
    if (item.skills && item.skills.length > 0) {
      csvRows.push(["", ""]); // Empty row for separation
      csvRows.push(["Skills/Priorities", ""]);
      item.skills.forEach((skill, index) => {
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
    a.download = `${item.candidateName.replace(/[^a-zA-Z0-9]/g, "_")}_analysis_report.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handleDownloadReportPDF = (item) => {
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
      "Technical Skills": item.fullAnalysis?.analysis?.technical_skills_score ||
                       item.fullAnalysis?.analysis?.skills_score ||
                       item.technicalSkills || 0,
      "Work Experience": item.fullAnalysis?.analysis?.experience_score ||
                       item.fullAnalysis?.analysis?.work_experience_score ||
                       item.experience || 0,
      "Academic Performance": item.fullAnalysis?.analysis?.academic_performance_score ||
                            item.fullAnalysis?.analysis?.education_score ||
                            item.education || 0,
      "Project Experience": item.fullAnalysis?.analysis?.project_experience_score ||
                          item.fullAnalysis?.analysis?.projects_score || 0,
      "Certifications": item.fullAnalysis?.analysis?.certifications_score ||
                      item.fullAnalysis?.analysis?.certification_score || 0,
      "Resume Formatting": item.fullAnalysis?.analysis?.resume_formatting_score ||
                         item.fullAnalysis?.analysis?.formatting_score || 0,
      "Skill Diversity": item.fullAnalysis?.analysis?.skill_diversity_score ||
                       item.fullAnalysis?.analysis?.diversity_score || 0,
      "Extracurricular Activities": item.fullAnalysis?.analysis?.extracurricular_score ||
                                  item.fullAnalysis?.analysis?.extracurriculars_score || 0,
      "CGPA Scores": item.fullAnalysis?.analysis?.cgpa_score ||
                   item.fullAnalysis?.analysis?.gpa_score || 0
    };

    // Create HTML content for PDF
    const htmlContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Resume Analysis Report - ${item.candidateName}</title>
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
            <h2>${item.candidateName}</h2>
          </div>

          <div class="section">
            <h3>Basic Information</h3>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">Candidate Name:</span>
                <span class="info-value">${item.candidateName}</span>
              </div>
              <div class="info-item">
                <span class="info-label">File Name:</span>
                <span class="info-value">${item.fileName}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Analysis Date:</span>
                <span class="info-value">${new Date(item.date).toLocaleDateString()}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Status:</span>
                <span class="info-value">${item.status}</span>
              </div>
            </div>
          </div>

          <div class="section">
            <h3>Overall Score</h3>
            <div class="overall-score">${item.overallScore}%</div>
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

          ${item.skills && item.skills.length > 0 ? `
          <div class="section">
            <h3>Skills & Priorities</h3>
            <div class="skills-list">
              ${item.skills.map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
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

  const handleDeleteAnalysis = (item) => {
    if (
      window.confirm(
        `Are you sure you want to delete the analysis for ${item.candidateName}?`
      )
    ) {
      const updatedAnalyses =
        JSON.parse(localStorage.getItem("recentAnalyses")) || [];
      const filteredAnalyses = updatedAnalyses.filter(
        (analysis) => analysis.id !== item.id
      );
      localStorage.setItem("recentAnalyses", JSON.stringify(filteredAnalyses));

      // Reload the data
      const loadHistoryData = () => {
        const storedAnalyses =
          JSON.parse(localStorage.getItem("recentAnalyses")) || [];
        const transformedData = storedAnalyses.map((analysis) => ({
          id: analysis.id,
          candidateName:
            analysis.candidateName ||
            analysis.fullAnalysis?.analysis?.basic_info?.content?.name ||
            analysis.fullAnalysis?.analysis?.candidate_name ||
            analysis.name?.replace(/\.[^/.]+$/, "") ||
            analysis.fileName?.replace(/\.[^/.]+$/, "") ||
            "Unknown Candidate",
          fileName: analysis.fileName,
          position:
            analysis.fullAnalysis?.analysis?.target_position ||
            "General Application",
          date: analysis.date
            ? analysis.date.split("T")[0]
            : new Date().toISOString().split("T")[0],
          overallScore: (() => {
            // Try multiple score extraction paths
            const possibleScores = [
              analysis.fullAnalysis?.analysis?.overall_score,
              analysis.fullAnalysis?.overall_score,
              analysis.score,
              analysis.overallScore,
              analysis.fullAnalysis?.data?.overall_score,
              analysis.fullAnalysis?.score,
            ];

            for (const score of possibleScores) {
              if (typeof score === "number" && score > 0) {
                return Math.round(score);
              }
            }
            return 0;
          })(),
          technicalSkills:
            analysis.fullAnalysis?.analysis?.technical_skills_score ||
            analysis.score ||
            0,
          experience:
            analysis.fullAnalysis?.analysis?.experience_score ||
            analysis.score ||
            0,
          education:
            analysis.fullAnalysis?.analysis?.education_score ||
            analysis.score ||
            0,
          skills: analysis.priorities || [],
          department: determineDepartment(analysis),
          status: analysis.status || "completed",
          uploadedAt: analysis.uploadedAt,
          jobId: analysis.jobId,
          fullAnalysis: analysis.fullAnalysis,
        }));
        setHistoryData(transformedData);
      };

      loadHistoryData();
      alert(`Analysis for ${item.candidateName} has been deleted.`);
    }
  };

  // Bulk action handlers
  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedItems([]);
      setSelectAll(false);
    } else {
      // Select ALL filtered data, not just current page
      setSelectedItems(filteredData.map((item) => item.id));
      setSelectAll(true);
    }
  };

  const handleSelectItem = (itemId) => {
    setSelectedItems(prev => {
      const newSelection = prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId];

      // Update selectAll status based on whether all filtered items are selected
      setSelectAll(newSelection.length === filteredData.length && filteredData.length > 0);

      return newSelection;
    });
  };

  const handleBulkDelete = () => {
    if (selectedItems.length === 0) {
      alert("Please select items to delete.");
      return;
    }

    const selectedCount = selectedItems.length;
    if (
      window.confirm(
        `Are you sure you want to delete ${selectedCount} selected analyses? This action cannot be undone.`
      )
    ) {
      const updatedAnalyses =
        JSON.parse(localStorage.getItem("recentAnalyses")) || [];
      const filteredAnalyses = updatedAnalyses.filter(
        (analysis) => !selectedItems.includes(analysis.id)
      );
      localStorage.setItem("recentAnalyses", JSON.stringify(filteredAnalyses));

      // Reload the data
      const loadHistoryData = () => {
        const storedAnalyses =
          JSON.parse(localStorage.getItem("recentAnalyses")) || [];
        const transformedData = storedAnalyses.map((analysis) => ({
          id: analysis.id,
          candidateName:
            analysis.candidateName ||
            analysis.fullAnalysis?.analysis?.basic_info?.content?.name ||
            analysis.fullAnalysis?.analysis?.candidate_name ||
            analysis.name?.replace(/\.[^/.]+$/, "") ||
            analysis.fileName?.replace(/\.[^/.]+$/, "") ||
            "Unknown Candidate",
          fileName: analysis.fileName,
          position:
            analysis.fullAnalysis?.analysis?.target_position ||
            "General Application",
          date: analysis.date
            ? analysis.date.split("T")[0]
            : new Date().toISOString().split("T")[0],
          overallScore: (() => {
            // Try multiple score extraction paths
            const possibleScores = [
              analysis.fullAnalysis?.analysis?.overall_score,
              analysis.fullAnalysis?.overall_score,
              analysis.score,
              analysis.overallScore,
              analysis.fullAnalysis?.data?.overall_score,
              analysis.fullAnalysis?.score,
            ];

            for (const score of possibleScores) {
              if (typeof score === "number" && score > 0) {
                return Math.round(score);
              }
            }
            return 0;
          })(),
          technicalSkills:
            analysis.fullAnalysis?.analysis?.technical_skills_score ||
            analysis.score ||
            0,
          experience:
            analysis.fullAnalysis?.analysis?.experience_score ||
            analysis.score ||
            0,
          education:
            analysis.fullAnalysis?.analysis?.education_score ||
            analysis.score ||
            0,
          skills: analysis.priorities || [],
          department: determineDepartment(analysis),
          status: analysis.status || "completed",
          uploadedAt: analysis.uploadedAt,
          jobId: analysis.jobId,
          fullAnalysis: analysis.fullAnalysis,
        }));
        setHistoryData(transformedData);
      };

      loadHistoryData();
      setSelectedItems([]);
      setSelectAll(false);
      alert(`${selectedCount} analyses have been deleted successfully.`);
    }
  };


  return (
    <div className="history-analytics-container">
      <div className="history-analytics-content">
        <div className="history-page-header">
          <h1 className="history-title">History & Analytics</h1>
          <div className="history-actions"></div>
        </div>

        {/* Analytics Dashboard - FIRST */}
        {analytics && (
          <div className="analytics-section">
            <h2>Analytics Dashboard</h2>

            <div className="analytics-grid">
              {/* Score Distribution - Big Chart at Top */}
              <div className="analytics-top-row">
                <div className="analytics-card">
                  <h3>Score Distribution</h3>
                  <div className="score-distribution-big">
                    <div className="score-distribution-chart">
                      <div className="chart-y-axis">
                        <span>
                          {Math.max(...Object.values(analytics.scoreRanges))}
                        </span>
                        <span>
                          {Math.floor(
                            Math.max(...Object.values(analytics.scoreRanges)) /
                              2
                          )}
                        </span>
                        <span>0</span>
                      </div>
                      {Object.entries(analytics.scoreRanges).map(
                        ([range, count]) => (
                          <div key={range} className="score-bar-big">
                            <div
                              className="score-bar-fill-big"
                              style={{
                                height: `${
                                  (count /
                                    Math.max(
                                      ...Object.values(analytics.scoreRanges)
                                    )) *
                                  100
                                }%`,
                                backgroundColor: getScoreColor(
                                  parseInt(range.split("-")[0]) || 50
                                ),
                              }}
                            ></div>
                            <div className="score-range-label-big">{range}</div>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Other Cards - Bottom Row */}
              <div className="analytics-bottom-row">
                <div className="analytics-card">
                  <h3>Overview</h3>
                  <div className="overview-stats">
                    <div className="stat-item">
                      <span className="stat-number">
                        {analytics.totalCandidates}
                      </span>
                      <span className="stat-label">Total Candidates</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-number">{analytics.avgScore}</span>
                      <span className="stat-label">Average Score</span>
                    </div>
                  </div>
                </div>

                <div className="analytics-card">
                  <h3>Top Skills/Priorities</h3>
                  <div className="skills-list">
                    {analytics.topSkills.map(([skill, count]) => (
                      <div key={skill} className="skill-item">
                        <span className="skill-name">{skill}</span>
                        <span className="skill-count">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="analytics-card">
                  <h3>Department Distribution</h3>
                  <div className="department-distribution">
                    {Object.entries(analytics.departmentCounts).map(
                      ([dept, count]) => (
                        <div key={dept} className="department-item">
                          <span className="department-name">{dept}</span>
                          <div className="department-bar-container">
                            <div
                              className="department-bar-fill"
                              style={{
                                width: `${
                                  (count / analytics.totalCandidates) * 100
                                }%`,
                              }}
                            ></div>
                            <span className="department-count">{count}</span>
                          </div>
                        </div>
                      )
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filter Controls - SECOND */}
        <div className="filter-section">
          <div className="filter-header">
            <h2>Filter Controls</h2>
            <button className="clear-filters-btn" onClick={handleClearFilters}>
              Clear All Filters
            </button>
          </div>

          <div className="filter-grid">
            <div className="filter-group">
              <label>Date Range</label>
              <div className="date-range">
                <input
                  type="date"
                  value={filters.dateRange.start}
                  onChange={(e) =>
                    handleFilterChange("dateRange", {
                      ...filters.dateRange,
                      start: e.target.value,
                    })
                  }
                  className="date-input"
                />
                <span>to</span>
                <input
                  type="date"
                  value={filters.dateRange.end}
                  onChange={(e) =>
                    handleFilterChange("dateRange", {
                      ...filters.dateRange,
                      end: e.target.value,
                    })
                  }
                  className="date-input"
                />
              </div>
            </div>

            <div className="filter-group">
              <label>Department</label>
              <select
                value={filters.department}
                onChange={(e) =>
                  handleFilterChange("department", e.target.value)
                }
                className="filter-select"
              >
                <option value="">All Departments</option>
                {/* Dynamic department options based on actual data */}
                {Object.keys(analytics?.departmentCounts || {})
                  .sort()
                  .map((dept) => (
                    <option key={dept} value={dept}>
                      {dept} ({analytics.departmentCounts[dept]})
                    </option>
                  ))}
                {/* Static fallback options for departments that might not have data yet */}
                {!analytics && (
                  <>
                    <option value="General">General</option>
                    <option value="Engineering">Engineering</option>
                    <option value="Data Science">Data Science</option>
                    <option value="Product">Product</option>
                    <option value="Design">Design</option>
                    <option value="Marketing">Marketing</option>
                    <option value="Sales">Sales</option>
                    <option value="Finance">Finance</option>
                    <option value="HR">HR</option>
                    <option value="Operations">Operations</option>
                  </>
                )}
              </select>
            </div>

            <div className="filter-group">
              <label>Score Range</label>
              <div className="score-range">
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={filters.scoreRange.min}
                  onChange={(e) =>
                    handleFilterChange("scoreRange", {
                      ...filters.scoreRange,
                      min: parseInt(e.target.value) || 0,
                    })
                  }
                  className="score-input"
                />
                <span>to</span>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={filters.scoreRange.max}
                  onChange={(e) =>
                    handleFilterChange("scoreRange", {
                      ...filters.scoreRange,
                      max: parseInt(e.target.value) || 100,
                    })
                  }
                  className="score-input"
                />
              </div>
            </div>

            <div className="filter-group">
              <label>Search Candidate</label>
              <input
                type="text"
                placeholder="Enter candidate name..."
                value={filters.searchName}
                onChange={(e) =>
                  handleFilterChange("searchName", e.target.value)
                }
                className="search-input"
              />
            </div>

            <div className="filter-group">
              <label>File Name</label>
              <input
                type="text"
                placeholder="Enter file name..."
                value={filters.position}
                onChange={(e) => handleFilterChange("position", e.target.value)}
                className="search-input"
              />
            </div>
          </div>
        </div>

        {/* Analysis History Table - THIRD */}
        <div className="history-section">
          <div className="history-header-section">
            <h2>Analysis History</h2>
            <div className="history-controls">
              <span className="results-count">
                Showing {paginatedData.length} of {filteredData.length} results
                {selectedItems.length > 0 && (
                  <span className="selected-count">
                    {" "}
                    • {selectedItems.length} selected
                  </span>
                )}
              </span>
              <select
                value={itemsPerPage}
                onChange={(e) => setItemsPerPage(parseInt(e.target.value))}
                className="items-per-page-select"
              >
                <option value={5}>5 per page</option>
                <option value={10}>10 per page</option>
                <option value={25}>25 per page</option>
                <option value={50}>50 per page</option>
              </select>
            </div>
          </div>

          {/* Bulk Actions Controls */}
          {filteredData.length > 0 && (
            <div className="bulk-actions-section">
              <div className="bulk-actions-left">
                <label className="select-all-checkbox">
                  <input
                    type="checkbox"
                    checked={selectAll}
                    onChange={handleSelectAll}
                  />
                  <span className="checkbox-label">
                    {selectAll
                      ? `Deselect All (${filteredData.length} selected)`
                      : `Select All (${filteredData.length} items)`}
                  </span>
                </label>
              </div>
              <div className="bulk-actions-right">
                <button
                  className="bulk-action-btn bulk-delete-selected"
                  onClick={handleBulkDelete}
                  disabled={selectedItems.length === 0}
                >
                  <i className="bi bi-trash"></i>
                  {selectedItems.length > 0
                    ? `Delete Selected (${selectedItems.length})`
                    : 'Delete Selected'}
                </button>
                <button
                  className="bulk-action-btn bulk-export"
                  onClick={() => {
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

                    // Build dynamic headers based on selected priorities
                    const headers = [
                      "Name",
                      "Date",
                      "Overall Score",
                      "Selected Priority Configuration",
                      ...selectedPriorities.map(priority => `${priority} Score`),
                      ...selectedPriorities.map(priority => `${priority} Weight (%)`),
                      "Analysis Link"
                    ];

                    const csvData = filteredData.map((item) => {
                      // Extract priority scores from fullAnalysis
                      const priorityScores = {};

                      // Map priority names to their scores in the analysis
                      const scoreMapping = {
                        "Technical Skills": item.fullAnalysis?.analysis?.technical_skills_score ||
                                         item.fullAnalysis?.analysis?.skills_score ||
                                         item.technicalSkills || 0,
                        "Work Experience": item.fullAnalysis?.analysis?.experience_score ||
                                         item.fullAnalysis?.analysis?.work_experience_score ||
                                         item.experience || 0,
                        "Academic Performance": item.fullAnalysis?.analysis?.academic_performance_score ||
                                              item.fullAnalysis?.analysis?.education_score ||
                                              item.education || 0,
                        "Project Experience": item.fullAnalysis?.analysis?.project_experience_score ||
                                            item.fullAnalysis?.analysis?.projects_score || 0,
                        "Certifications": item.fullAnalysis?.analysis?.certifications_score ||
                                        item.fullAnalysis?.analysis?.certification_score || 0,
                        "Resume Formatting": item.fullAnalysis?.analysis?.resume_formatting_score ||
                                           item.fullAnalysis?.analysis?.formatting_score || 0,
                        "Skill Diversity": item.fullAnalysis?.analysis?.skill_diversity_score ||
                                         item.fullAnalysis?.analysis?.diversity_score || 0,
                        "Extracurricular Activities": item.fullAnalysis?.analysis?.extracurricular_score ||
                                                    item.fullAnalysis?.analysis?.extracurriculars_score || 0,
                        "CGPA Scores": item.fullAnalysis?.analysis?.cgpa_score ||
                                     item.fullAnalysis?.analysis?.gpa_score || 0
                      };

                      // Create analysis link
                      const analysisLink = `${window.location.origin}/analysis/${item.id}`;

                      // Build the row data
                      const rowData = [
                        `"${item.candidateName}"`,
                        `"${new Date(item.date).toLocaleDateString()}"`,
                        item.overallScore,
                        `"${selectedPriorities.join(', ')}"`,
                        ...selectedPriorities.map(priority => scoreMapping[priority] || 0),
                        ...selectedPriorities.map(priority => priorityWeights[priority] || 0),
                        `"${analysisLink}"`
                      ];

                      return rowData;
                    });

                    const csvContent = [
                      headers.join(","),
                      ...csvData.map((row) => row.join(",")),
                    ].join("\n");
                    const dataBlob = new Blob([csvContent], {
                      type: "text/csv",
                    });
                    const url = URL.createObjectURL(dataBlob);
                    const link = document.createElement("a");
                    link.href = url;
                    link.download = `resume-analysis-with-priorities-${
                      new Date().toISOString().split("T")[0]
                    }.csv`;
                    link.click();
                    URL.revokeObjectURL(url);
                  }}
                  disabled={filteredData.length === 0}
                >
                  <i className="bi bi-file-earmark-spreadsheet"></i>
                  Export CSV
                </button>
              </div>
            </div>
          )}

          {filteredData.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">
                <i className="bi bi-graph-up"></i>
              </div>
              <h3>No Analysis Data Found</h3>
              <p>
                Upload and analyze some resumes to see your history and
                analytics here.
              </p>
              <button className="empty-cta" onClick={onBackToDashboard}>
                Go to Dashboard
              </button>
            </div>
          ) : (
            <>
              <div className="history-table-container">
                <table className="history-table">
                  <thead>
                    <tr>
                      <th className="checkbox-header">Select</th>
                      <th>Candidate Name</th>
                      <th>Date</th>
                      <th>Overall Score</th>
                      <th>Status</th>
                      <th>Priorities</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedData.map((item) => (
                      <tr key={item.id}>
                        <td className="checkbox-cell">
                          <input
                            type="checkbox"
                            checked={selectedItems.includes(item.id)}
                            onChange={() => handleSelectItem(item.id)}
                          />
                        </td>
                        <td className="candidate-cell">
                          <div className="candidate-info">
                            <span className="candidate-name">
                              {item.candidateName}
                            </span>
                          </div>
                        </td>
                        <td>{new Date(item.date).toLocaleDateString()}</td>
                        <td>
                          <div className="score-cell">
                            <span
                              className="score-value"
                              style={{
                                color: getScoreColor(item.overallScore),
                              }}
                            >
                              {item.overallScore}%
                            </span>
                          </div>
                        </td>
                        <td>
                          <span className={`status-badge ${item.status}`}>
                            {item.status === "processing" ? (
                              <>
                                <i className="bi bi-clock"></i>Processing
                              </>
                            ) : (
                              <>
                                <i className="bi bi-check-circle"></i>Completed
                              </>
                            )}
                          </span>
                        </td>
                        <td>
                          <div className="priorities-cell">
                            {item.skills.slice(0, 2).map((skill, index) => (
                              <span key={index} className="priority-tag">
                                {skill}
                              </span>
                            ))}
                            {item.skills.length > 2 && (
                              <span className="priority-more">
                                +{item.skills.length - 2}
                              </span>
                            )}
                          </div>
                        </td>
                        <td>
                          <div className="action-buttons">
                            <button
                              className="action-btn view-btn"
                              title="View Details"
                              onClick={() => handleViewDetails(item)}
                            >
                              <i className="bi bi-eye"></i>
                            </button>
                            <div className="dropdown-wrapper">
                              <button
                                className="action-btn download-btn dropdown-toggle"
                                title="Download Report"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  const dropdown = e.target.nextElementSibling;
                                  if (dropdown) {
                                    dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
                                  }
                                }}
                              >
                                📥
                              </button>
                              <div className="dropdown-menu" style={{display: 'none'}}>
                                <button
                                  className="dropdown-item"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleDownloadReportCSV(item);
                                    e.target.closest('.dropdown-menu').style.display = 'none';
                                  }}
                                >
                                  📊 Export as CSV
                                </button>
                                <button
                                  className="dropdown-item"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleDownloadReportPDF(item);
                                    e.target.closest('.dropdown-menu').style.display = 'none';
                                  }}
                                >
                                  📄 Export as PDF
                                </button>
                              </div>
                            </div>
                            <button
                              className="action-btn delete-btn"
                              title="Delete"
                              onClick={() => handleDeleteAnalysis(item)}
                            >
                              <i className="bi bi-trash"></i>
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="pagination">
                  <button
                    className="pagination-btn"
                    disabled={currentPage === 1}
                    onClick={() => setCurrentPage(currentPage - 1)}
                  >
                    Previous
                  </button>

                  <div className="pagination-numbers">
                    {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                      (pageNum) => (
                        <button
                          key={pageNum}
                          className={`pagination-number ${
                            currentPage === pageNum ? "active" : ""
                          }`}
                          onClick={() => setCurrentPage(pageNum)}
                        >
                          {pageNum}
                        </button>
                      )
                    )}
                  </div>

                  <button
                    className="pagination-btn"
                    disabled={currentPage === totalPages}
                    onClick={() => setCurrentPage(currentPage + 1)}
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default HistoryAnalytics;
