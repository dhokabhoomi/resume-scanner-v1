import React, { useState } from "react";
import { useNavigation } from "../contexts/NavigationContext";
import AnalysisResultsPage from "./AnalysisResultsPage";
import SettingsPage from "./SettingsPage";
import { API_ENDPOINTS, testBackendConnection } from "../config/api";
import {
  DEFAULT_PRIORITIES,
  AVAILABLE_PRIORITIES,
  PRIORITY_MAPPINGS,
} from "../constants/priorities";
import { getCurrentScoringWeights } from "../utils/priorityWeights";
import "./DashboardLayout.css";
import "./AnalysisResultsPage.css";

function EnhancedDashboard({
  onViewDetails,
}) {
  const { goToHistory, goToSettings } = useNavigation();
  const [selectedPriorities, setSelectedPriorities] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [defaultPriorities, setDefaultPriorities] =
    useState(DEFAULT_PRIORITIES);

  const priorities = AVAILABLE_PRIORITIES;

  const handlePriorityToggle = (priorityId) => {
    setSelectedPriorities((prev) => {
      if (prev.includes(priorityId)) {
        // Remove if already selected
        return prev.filter((id) => id !== priorityId);
      } else if (prev.length < 3) {
        // Add in the order selected (maintains order)
        return [...prev, priorityId];
      }
      // Don't add if already 3 selected
      return prev;
    });
  };

  const getPriorityOrder = (priorityId) => {
    const index = selectedPriorities.indexOf(priorityId);
    return index !== -1 ? index + 1 : null;
  };

  const handleViewAnalysis = (analysis) => {
    // If onViewDetails prop is provided, use routing (proper navigation)
    if (onViewDetails) {
      onViewDetails(analysis);
    } else {
      // Fallback: set local state for inline display
      setCurrentAnalysis({
        candidate_name: analysis.candidateName || analysis.name,
        overall_score: analysis.score,
        priorities: analysis.priorities,
        fileName: analysis.fileName,
        uploadedAt: analysis.uploadedAt,
        fullAnalysis: analysis.fullAnalysis,
        jobId: analysis.jobId,
        status: analysis.status,
      });
      setShowAnalysisResults(true);
    }
    setShowDropdownId(null); // Close any open dropdowns
  };

  const handleRemoveAnalysis = (analysisId) => {
    const existingAnalyses =
      JSON.parse(localStorage.getItem("recentAnalyses")) || [];
    const updatedAnalyses = existingAnalyses.filter(
      (analysis) => analysis.id !== analysisId
    );
    localStorage.setItem("recentAnalyses", JSON.stringify(updatedAnalyses));
    setRecentAnalyses(updatedAnalyses.slice(0, 3));
    setShowDropdownId(null); // Close dropdown after removal
  };

  const toggleDropdown = (analysisId) => {
    setShowDropdownId(showDropdownId === analysisId ? null : analysisId);
  };

  const handleBackToDashboard = () => {
    setShowAnalysisResults(false);
    setCurrentAnalysis(null);
    setShowSettings(false);

    // Refresh default priorities when returning from settings
    const savedSettings = localStorage.getItem("resumeAnalyzerSettings");
    if (savedSettings) {
      const settings = JSON.parse(savedSettings);
      setDefaultPriorities(
        settings.defaultPriorities || [
          "Technical Skills",
          "Work Experience",
          "Academic Performance",
        ]
      );
    }
  };

  const handleShowSettings = () => {
    setShowSettings(true);
    setShowAnalysisResults(false);
    setCurrentAnalysis(null);
  };

  const handleDownloadReport = () => {
    alert(
      "Download Report functionality will be implemented with backend integration!"
    );
  };

  const handleShareReport = () => {
    alert(
      "📤 Share Report functionality will be implemented with backend integration!"
    );
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    if (e.currentTarget.contains(e.relatedTarget)) return;
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    const validFiles = droppedFiles.filter(
      (file) => file.type === "application/pdf" || file.name.endsWith(".pdf")
    );
    setFiles(validFiles);
  };

  const handleFileInput = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const validFiles = selectedFiles.filter(
      (file) => file.type === "application/pdf" || file.name.endsWith(".pdf")
    );
    setFiles(validFiles);
  };

  const saveToLocalStorage = (analysisData) => {
    const existingAnalyses =
      JSON.parse(localStorage.getItem("recentAnalyses")) || [];

    // Helper function to extract candidate name from various sources
    const extractCandidateName = (analysisData) => {
      // Try multiple sources in order of preference
      const sources = [
        // 1. From API analysis basic_info
        analysisData.fullAnalysis?.analysis?.basic_info?.content?.name,
        // 2. From bulk analysis candidate_name
        analysisData.candidateName,
        // 3. Try to extract from filename (common patterns)
        extractNameFromFilename(analysisData.fileName),
        // 4. Clean filename fallback
        analysisData.fileName?.replace(/\.[^/.]+$/, "") || "Unknown",
      ];

      for (const name of sources) {
        if (name && typeof name === "string" && name.trim().length > 0) {
          return name.trim();
        }
      }
      return "Unknown Candidate";
    };

    const candidateName = extractCandidateName(analysisData);

    const newAnalysis = {
      id: Date.now(),
      name: candidateName,
      candidateName: candidateName, // Store extracted candidate name
      fileName: analysisData.fileName,
      score: analysisData.score,
      date: new Date().toISOString(),
      priorities: analysisData.priorities,
      uploadedAt: new Date().toLocaleDateString(),
      fullAnalysis: analysisData.fullAnalysis, // Store complete backend analysis
      jobId: analysisData.jobId,
      status: analysisData.status || "completed",
    };

    // Add to beginning of array and keep only last 10
    const updatedAnalyses = [newAnalysis, ...existingAnalyses].slice(0, 10);
    localStorage.setItem("recentAnalyses", JSON.stringify(updatedAnalyses));

    return newAnalysis;
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      alert(
        'Please select files first!\n\nDrag & drop files or click "Browse Files" to get started.'
      );
      return;
    }

    setIsAnalyzing(true);

    try {
      // Use selected priorities if available, otherwise use default priorities from settings
      let prioritiesToUse;
      if (selectedPriorities.length > 0) {
        // Convert priority IDs to labels that the backend expects
        prioritiesToUse = selectedPriorities.map((id) => {
          return PRIORITY_MAPPINGS[id] || id;
        });
      } else {
        // Use default priorities from settings
        prioritiesToUse = defaultPriorities;
      }

      if (files.length === 1) {
        // Single file analysis

        const formData = new FormData();
        formData.append("file", files[0]);

        if (prioritiesToUse.length > 0) {
          formData.append("priorities", prioritiesToUse.join(","));
        }

        // Add dynamic scoring weights based on current priorities
        const scoringWeights = getCurrentScoringWeights();
        formData.append("scoring_weights", JSON.stringify(scoringWeights));

        const response = await fetch(API_ENDPOINTS.ANALYZE_RESUME, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          let errorData;
          try {
            errorData = await response.json();
          } catch {
            errorData = await response.text();
          }

          // Extract error message from various possible formats
          let errorMessage;
          if (errorData.detail) {
            errorMessage = errorData.detail;
          } else if (errorData.message) {
            errorMessage = errorData.message;
          } else if (typeof errorData === "string") {
            errorMessage = errorData;
          } else if (errorData && typeof errorData === "object") {
            // If it's an object with no clear message, stringify it properly
            errorMessage = JSON.stringify(errorData);
          } else {
            errorMessage = `HTTP ${response.status} error`;
          }
          const error = new Error(`HTTP ${response.status}: ${errorMessage}`);
          error.response = errorData;
          throw error;
        }

        const analysisResult = await response.json();
        console.log("Analysis result received:", analysisResult); // Debug log

        if (analysisResult.status === "success") {
          // Extract score from multiple possible locations
          const extractScore = (result) => {
            const possibleScores = [
              result.analysis?.overall_score,
              result.overall_score,
              result.score,
              result.analysis?.score,
              result.data?.overall_score,
              result.data?.score
            ];

            for (const score of possibleScores) {
              if (typeof score === 'number' && score > 0) {
                return Math.round(score);
              }
            }
            return 0;
          };

          const extractedScore = extractScore(analysisResult);
          console.log("Extracted score:", extractedScore); // Debug log

          // Extract real data from the analysis
          const analysisData = {
            fileName: files[0].name,
            score: extractedScore,
            priorities:
              prioritiesToUse.length > 0
                ? prioritiesToUse
                : ["General Analysis"],
            fullAnalysis: analysisResult, // Store the complete analysis
          };

          saveToLocalStorage(analysisData);

          // Update recent analyses immediately
          const stored =
            JSON.parse(localStorage.getItem("recentAnalyses")) || [];
          setRecentAnalyses(stored.slice(0, 3));

          const priorityText =
            prioritiesToUse.length > 0
              ? prioritiesToUse.join(", ")
              : "General Analysis";
          const sourceText =
            selectedPriorities.length > 0
              ? "Manual Selection"
              : "Default Settings";
          alert(
            `Analysis Complete!\n\nFile: ${files[0].name}\nFocus: ${priorityText}\nSource: ${sourceText}\nScore: ${analysisData.score}%\n\nResults saved to Recent Analyses`
          );
        } else {
          throw new Error(analysisResult.error || "Analysis failed");
        }
      } else {
        // Bulk file analysis

        const formData = new FormData();
        files.forEach((file) => {
          formData.append("files", file);
        });

        if (prioritiesToUse.length > 0) {
          formData.append("priorities", prioritiesToUse.join(","));
        }

        // Add dynamic scoring weights based on current priorities
        const scoringWeights = getCurrentScoringWeights();
        formData.append("scoring_weights", JSON.stringify(scoringWeights));

        // Create a job name with only allowed characters
        const now = new Date();
        const timestamp = now.toISOString().slice(0, 19).replace(/[T:]/g, "-");
        formData.append("job_name", `Bulk_Analysis_${timestamp}`);

        const response = await fetch(API_ENDPOINTS.BULK_ANALYZE, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          let errorData;
          try {
            errorData = await response.json();
          } catch {
            errorData = await response.text();
          }

          // Extract error message from various possible formats
          let errorMessage;
          if (errorData.detail) {
            errorMessage = errorData.detail;
          } else if (errorData.message) {
            errorMessage = errorData.message;
          } else if (typeof errorData === "string") {
            errorMessage = errorData;
          } else if (errorData && typeof errorData === "object") {
            // If it's an object with no clear message, stringify it properly
            errorMessage = JSON.stringify(errorData);
          } else {
            errorMessage = `HTTP ${response.status} error`;
          }
          const error = new Error(`HTTP ${response.status}: ${errorMessage}`);
          error.response = errorData;
          throw error;
        }

        const bulkResult = await response.json();

        if (bulkResult.job_id) {
          const priorityText =
            prioritiesToUse.length > 0
              ? prioritiesToUse.join(", ")
              : "General Analysis";
          const sourceText =
            selectedPriorities.length > 0
              ? "Manual Selection"
              : "Default Settings";

          // Create placeholder entries immediately to show in UI
          const placeholders = files.map((file, index) => {
            const extractedName =
              extractNameFromFilename(file.name) ||
              file.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ") ||
              "Unknown Candidate";
            return {
              id: `${bulkResult.job_id}-${index}`,
              fileName: file.name,
              name: extractedName, // UI expects 'name' field
              candidateName: extractedName, // Keep both for compatibility
              score: 0,
              priorities:
                prioritiesToUse.length > 0
                  ? prioritiesToUse
                  : ["General Analysis"],
              jobId: bulkResult.job_id,
              status: "processing",
              timestamp: new Date().toISOString(),
            };
          });

          // Add placeholders to localStorage and UI
          const existingAnalyses =
            JSON.parse(localStorage.getItem("recentAnalyses")) || [];
          const updatedAnalyses = [...placeholders, ...existingAnalyses].slice(
            0,
            10
          );
          localStorage.setItem(
            "recentAnalyses",
            JSON.stringify(updatedAnalyses)
          );
          setRecentAnalyses(updatedAnalyses.slice(0, 3));

          alert(
            `Bulk Analysis Started!\n\nFiles: ${files.length}\nFocus: ${priorityText}\nSource: ${sourceText}\nJob ID: ${bulkResult.job_id}\n\nProcessing... You'll see placeholders in Recent Analyses that will update when complete.`
          );

          // Start polling for job completion
          pollBulkJobStatus(bulkResult.job_id);
        } else {
          throw new Error("Failed to start bulk analysis");
        }
      }

      // Reset form after successful upload
      setFiles([]);
      setSelectedPriorities([]);
      setIsAnalyzing(false);
    } catch (error) {
      console.error("Upload error:", error);
      let errorMessage = "Upload failed. Please try again.";

      if (error.message.includes("Failed to fetch")) {
        errorMessage =
          "Cannot connect to server. Please check if the backend is running.";
      } else if (error.message.includes("HTTP 429") || error.message.includes("rate limit") || error.message.includes("temporarily blocked")) {
        errorMessage =
          "Rate limit exceeded. Please wait a moment before trying again. The server is temporarily blocking requests to prevent overload.";
      } else if (error.message.includes("HTTP 400")) {
        // Try to extract the actual error message from the backend
        if (error.response && error.response.detail) {
          errorMessage = error.response.detail;
        } else if (error.message.includes("File validation failed")) {
          errorMessage = "Invalid file format. Please upload PDF files only.";
        } else {
          errorMessage = error.message; // Show the actual error
        }
      } else if (error.message.includes("HTTP 500")) {
        errorMessage = "Server error during analysis. Please check if the backend is running and try again.";
        console.error("500 Server Error Details:", {
          message: error.message,
          response: error.response,
          timestamp: new Date().toISOString()
        });
      } else if (error.message) {
        errorMessage = error.message;
      }

      console.error("Full error details:", error);
      alert(`Error: ${errorMessage}\n\nCheck the browser console for more details.`);
    } finally {
      setIsAnalyzing(false);
    }
  };


  // Load recent analyses from localStorage
  const [recentAnalyses, setRecentAnalyses] = useState([]);
  const [showAnalysisResults, setShowAnalysisResults] = useState(false);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [showDropdownId, setShowDropdownId] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [backendStatus, setBackendStatus] = useState(null);

  // Test backend connection
  const handleTestConnection = async () => {
    console.log("Testing backend connection...");
    const result = await testBackendConnection();
    setBackendStatus(result);

    if (result.success) {
      alert(`✅ Backend Connected!\n\nStatus: ${JSON.stringify(result.data, null, 2)}`);
    } else {
      alert(`❌ Backend Connection Failed!\n\nError: ${result.error}\n\nCheck the console for more details.`);
    }
  };

  // Manual refresh for stuck processing jobs
  const handleRefreshResults = () => {
    console.log("Manually refreshing analysis results...");
    const stored = JSON.parse(localStorage.getItem("recentAnalyses")) || [];
    const processingJobs = stored.filter(a => a.status === "processing" && a.jobId);

    if (processingJobs.length > 0) {
      console.log(`Found ${processingJobs.length} processing jobs, checking status...`);
      processingJobs.forEach(job => {
        console.log(`Checking job ${job.jobId}...`);
        pollBulkJobStatus(job.jobId);
      });
      alert(`Checking status of ${processingJobs.length} processing job(s). Results will update automatically if completed.`);
    } else {
      // Just refresh the display
      const updatedStored = JSON.parse(localStorage.getItem("recentAnalyses")) || [];
      setRecentAnalyses(updatedStored.slice(0, 3));
      alert("Results refreshed! No processing jobs found.");
    }
  };

  // Helper function to extract name from filename using common patterns
  const extractNameFromFilename = (fileName) => {
    if (!fileName) return null;

    // Remove file extension
    const nameWithoutExt = fileName.replace(/\.[^/.]+$/, "");

    // Common patterns in resume filenames (made more flexible)
    const patterns = [
      // Pattern: "FirstName LastName - Something" or "FirstName LastName_Something"
      /^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:\s*[-_]\s*.+)?$/,
      // Pattern: "FirstNameLastName_Something - FirstName LastName"
      /.*[-_]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)$/,
      // Pattern: Just "FirstName LastName"
      /^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)$/,
      // Pattern: "firstname lastname" (lowercase)
      /^([a-z]+(?:\s+[a-z]+)+)(?:\s*[-_]\s*.+)?$/i,
      // Pattern: "First Last" (mixed case)
      /^([A-Za-z]+(?:\s+[A-Za-z]+)+)(?:\s*[-_]\s*.+)?$/,
    ];

    for (const pattern of patterns) {
      const match = nameWithoutExt.match(pattern);
      if (match && match[1]) {
        const extractedName = match[1].trim();
        // Convert to proper case
        const properCaseName = extractedName
          .toLowerCase()
          .split(" ")
          .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
          .join(" ");
        return properCaseName;
      }
    }

    // If no pattern matches, try to clean up the filename
    const cleaned = nameWithoutExt
      .replace(/[-_]/g, " ")
      .replace(/\s+/g, " ")
      .trim();

    // If it looks like a name (2+ words, reasonable length)
    if (cleaned.includes(" ") && cleaned.length > 2 && cleaned.length < 50) {
      const properCaseName = cleaned
        .toLowerCase()
        .split(" ")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
      return properCaseName;
    }

    return null;
  };

  // Poll for bulk job status and update localStorage incrementally
  const pollBulkJobStatus = async (jobId) => {
    const maxAttempts = 80; // Poll for up to 20 minutes (80 * 15s)
    const pollInterval = 15000; // 15 seconds to avoid rate limiting
    let attempts = 0;
    let consecutiveRateLimitErrors = 0;

    const poll = async () => {
      try {
        attempts++;

        const response = await fetch(
          `${API_ENDPOINTS.BULK_JOB_STATUS}/${jobId}`
        );

        if (!response.ok) {
          throw new Error(`Failed to get job status: HTTP ${response.status}`);
        }

        const jobStatus = await response.json();
        console.log(`Job ${jobId} status:`, jobStatus.status, `Results: ${jobStatus.results?.length || 0}`);
        console.log('Full job status:', JSON.stringify(jobStatus, null, 2));

        // Update individual resume statuses incrementally
        let updatedAnalyses =
          JSON.parse(localStorage.getItem("recentAnalyses")) || [];

        // Check if we have any results to process (partial or complete)
        if (jobStatus.results && jobStatus.results.length > 0) {
          console.log('Processing', jobStatus.results.length, 'results from job', jobId);
          // Update placeholders with actual results as they become available
          updatedAnalyses = updatedAnalyses.map(analysis => {
            // Find matching result for this placeholder
            if (analysis.jobId === jobId && analysis.status === "processing") {
              const matchingResult = jobStatus.results.find(result => {
                // Primary matching: jobId and filename
                return result.filename === analysis.fileName;
              });

              if (matchingResult) {
                console.log(`Found match for ${analysis.fileName}:`, matchingResult.filename);
                // Create updated analysis with actual data
                const extractedName =
                  matchingResult.candidate_name ||
                  extractNameFromFilename(matchingResult.filename) ||
                  matchingResult.filename.replace(/\.[^/.]+$/, "");

                // Create a mock detailed analysis structure from the summary data
                const mockFullAnalysis = {
                  analysis: {
                    overall_score: matchingResult.overall_score,
                    basic_info: {
                      content: {
                        name: matchingResult.candidate_name,
                        email: "N/A",
                        phone: "N/A",
                        location: "N/A",
                      },
                      quality_score: Math.max(matchingResult.overall_score - 10, 0),
                    },
                    skills: {
                      content: {
                        technical_skills: matchingResult.key_skills || [],
                        skill_categories: matchingResult.key_skills
                          ? matchingResult.key_skills.map((skill) => ({
                              name: skill,
                              level: "Intermediate",
                            }))
                          : [],
                      },
                      quality_score:
                        matchingResult.priority_scores?.["Technical Skills"] ||
                        matchingResult.overall_score,
                      suggestions:
                        "Detailed skills analysis not available for bulk processed resumes.",
                    },
                    work_experience: {
                      content: {
                        experience_level: matchingResult.experience_level,
                        total_experience: "Not specified",
                      },
                      quality_score:
                        matchingResult.priority_scores?.["Work Experience"] ||
                        Math.max(matchingResult.overall_score - 5, 0),
                      suggestions:
                        "Detailed experience analysis not available for bulk processed resumes.",
                    },
                    education: {
                      content: {
                        education_level: matchingResult.education_level,
                        cgpa_present: matchingResult.cgpa_found,
                        cgpa_value: matchingResult.cgpa_value,
                      },
                      quality_score:
                        matchingResult.priority_scores?.["Academic Performance"] ||
                        Math.max(matchingResult.overall_score - 5, 0),
                      suggestions:
                        "Detailed education analysis not available for bulk processed resumes.",
                    },
                    projects: {
                      content: {
                        project_count: "Not analyzed in bulk mode",
                      },
                      quality_score:
                        matchingResult.priority_scores?.["Project Experience"] ||
                        Math.max(matchingResult.overall_score - 15, 0),
                      suggestions:
                        "Detailed project analysis not available for bulk processed resumes.",
                    },
                    formatting_issues: {
                      content: {
                        formatting_score: matchingResult.formatting_score,
                        major_issues: [],
                      },
                      quality_score: matchingResult.formatting_score,
                      suggestions:
                        "Detailed formatting analysis not available for bulk processed resumes.",
                    },
                  },
                };

                // Extract email from the backend analysis data
                const extractedEmail = matchingResult.full_analysis?.basic_info?.content?.email;

                return {
                  ...analysis,
                  id: `${jobId}-completed-${analysis.fileName}`,
                  name: extractedName,
                  candidateName: extractedName,
                  score: matchingResult.overall_score,
                  status: "completed", // Explicitly set status to completed
                  fullAnalysis: mockFullAnalysis,
                  // Include enhanced data fields from backend
                  full_analysis: matchingResult.full_analysis,
                  rule_based_findings: matchingResult.rule_based_findings,
                  fact_sheet: matchingResult.fact_sheet,
                  priority_analysis: matchingResult.priority_analysis,
                  // Store email at root level for easy access
                  email: extractedEmail,
                  timestamp: new Date().toISOString(),
                  uploadedAt: new Date().toLocaleDateString(),
                };
              }
            }
            return analysis;
          });

          // Save updated analyses
          localStorage.setItem("recentAnalyses", JSON.stringify(updatedAnalyses));
          setRecentAnalyses(updatedAnalyses.slice(0, 3));

          // Show progress to user
          const completedCount = updatedAnalyses.filter(a => a.jobId === jobId && a.status === "completed").length;
          const totalCount = updatedAnalyses.filter(a => a.jobId === jobId).length;
          console.log(`Bulk job progress: ${completedCount}/${totalCount} completed`);

          // Show progress notification (could be improved with a proper progress bar later)
          if (completedCount > 0 && completedCount < totalCount) {
            console.log(`✅ ${completedCount} resumes completed! Check Recent Analyses or History to view results.`);
          }
        }

        if (jobStatus.status === "completed") {
          // Force match any remaining unmatched results
          const unmatchedResults = jobStatus.results.filter(result =>
            !updatedAnalyses.some(analysis =>
              analysis.jobId === jobId &&
              analysis.status === "completed" &&
              (analysis.fileName === result.filename ||
               analysis.fileName?.toLowerCase() === result.filename?.toLowerCase())
            )
          );

          // Force match remaining results to any processing entries
          unmatchedResults.forEach((result) => {
            const processingEntry = updatedAnalyses.find(analysis =>
              analysis.jobId === jobId && analysis.status === "processing"
            );

            if (processingEntry) {
              const extractedName =
                result.candidate_name ||
                extractNameFromFilename(result.filename) ||
                result.filename?.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ") ||
                "Unknown Candidate";

              Object.assign(processingEntry, {
                status: "completed", // Explicitly set status to completed
                score: result.overall_score || 0,
                overallScore: result.overall_score || 0,
                fullAnalysis: result,
                // Include enhanced data fields from backend
                full_analysis: result.full_analysis,
                rule_based_findings: result.rule_based_findings,
                fact_sheet: result.fact_sheet,
                priority_analysis: result.priority_analysis,
                fileName: result.filename || processingEntry.fileName,
                name: extractedName,
                candidateName: extractedName,
                uploadedAt: new Date().toLocaleDateString(),
                timestamp: new Date().toISOString()
              });
            }
          });

          // Update localStorage with final results
          localStorage.setItem("recentAnalyses", JSON.stringify(updatedAnalyses));
          setRecentAnalyses(updatedAnalyses.slice(0, 3));

          const completedCount = updatedAnalyses.filter(a => a.jobId === jobId && a.status === "completed").length;
          console.log(`Updated ${completedCount} completed analyses out of ${jobStatus.results.length} results`);

          // Check if job is truly finished or still processing
          if (jobStatus.status === "completed" || jobStatus.status === "finished") {
            console.log(`Bulk Analysis Complete! ${completedCount}/${jobStatus.results.length} resumes processed successfully.`);
            return; // Stop polling
          } else if (jobStatus.status === "processing" && attempts < maxAttempts) {
            console.log(`Job still processing, continuing to poll (attempt ${attempts}/${maxAttempts})`);
            setTimeout(poll, pollInterval);
          }
        } else if (jobStatus.status === "processing" && attempts < maxAttempts) {
          // Still processing, continue polling
          setTimeout(poll, pollInterval);
        } else if (jobStatus.status === "failed") {
          console.error("Bulk job failed:", jobStatus.error_message);
          alert(
            `Bulk Analysis Failed!\n\nError: ${
              jobStatus.error_message || "Unknown error"
            }`
          );
        } else if (attempts >= maxAttempts) {
          console.warn("Bulk job polling timed out");
          alert(
            "Bulk Analysis Status: Processing is taking longer than expected. Please check back later or contact support."
          );
        }
      } catch (error) {
        console.error("Error polling job status:", error);

        // Check for 404 errors (job not found/expired)
        if (error.message && error.message.includes("HTTP 404")) {
          console.warn(`Job ${jobId} not found - likely expired after server restart`);
          // Stop polling for this job and clean up
          const updatedAnalyses = JSON.parse(localStorage.getItem("recentAnalyses")) || [];
          const filteredAnalyses = updatedAnalyses.filter(analysis => analysis.jobId !== jobId);
          localStorage.setItem("recentAnalyses", JSON.stringify(filteredAnalyses));
          setRecentAnalyses(filteredAnalyses.slice(0, 3));
          return; // Stop polling
        }

        // Check for rate limiting errors
        if (error.message && (error.message.includes("429") || error.message.includes("rate limit") || error.message.includes("temporarily blocked"))) {
          consecutiveRateLimitErrors++;
          console.warn(`Rate limit hit during polling (${consecutiveRateLimitErrors} consecutive times)`);

          if (attempts < maxAttempts) {
            // Progressive backoff: 30s, 60s, 120s, 240s, max 5 minutes
            const backoffDelay = Math.min(30000 * Math.pow(2, consecutiveRateLimitErrors - 1), 300000);
            console.log(`Rate limited. Retrying in ${backoffDelay / 1000} seconds... (attempt ${attempts}/${maxAttempts})`);

            // Show user notification for persistent rate limiting
            if (consecutiveRateLimitErrors >= 3) {
              console.log("⏰ Polling slowed due to rate limiting. Results will appear when ready.");
            }

            setTimeout(poll, backoffDelay);
          } else {
            alert(
              "Bulk analysis polling was rate-limited. Your analyses may have completed. Please refresh the page to check results in Recent Analyses."
            );
          }
        } else if (attempts < maxAttempts) {
          // Reset rate limit counter on successful request
          consecutiveRateLimitErrors = 0;
          // Regular error retry with longer interval
          setTimeout(poll, pollInterval * 2);
        } else {
          alert(
            "Unable to check bulk analysis status. Please refresh the page and check Recent Analyses."
          );
        }
      }
    };

    // Start polling with delay to let backend start processing
    setTimeout(poll, 20000); // Wait 20 seconds before first poll to reduce rate limiting
  };

  React.useEffect(() => {
    const loadRecentAnalyses = () => {
      const stored = JSON.parse(localStorage.getItem("recentAnalyses")) || [];

      // Auto-check any stuck processing jobs on page load
      const processingJobs = stored.filter(a => a.status === "processing" && a.jobId);
      console.log(`Found ${processingJobs.length} processing jobs on page load`);

      // Check each stuck job
      processingJobs.forEach(async (analysis) => {
        try {
          console.log(`Checking stuck job ${analysis.jobId}`);
          const response = await fetch(`${API_ENDPOINTS.BULK_JOB_STATUS}/${analysis.jobId}`);
          if (response.ok) {
            const jobStatus = await response.json();
            if (jobStatus.results && jobStatus.results.length > 0) {
              console.log(`Found completed results for stuck job ${analysis.jobId}, restarting polling`);
              pollBulkJobStatus(analysis.jobId);
            }
          }
        } catch (error) {
          console.error(`Error checking stuck job ${analysis.jobId}:`, error);
        }
      });

      setRecentAnalyses(stored.slice(0, 3)); // Show up to 3 recent analyses
    };

    const loadDefaultPriorities = () => {
      const savedSettings = localStorage.getItem("resumeAnalyzerSettings");
      if (savedSettings) {
        const settings = JSON.parse(savedSettings);
        setDefaultPriorities(settings.defaultPriorities || DEFAULT_PRIORITIES);
      } else {
        setDefaultPriorities(DEFAULT_PRIORITIES);
      }
    };

    loadRecentAnalyses();
    loadDefaultPriorities();

    // Test backend connection on component mount
    testBackendConnection().then(result => {
      setBackendStatus(result);
      if (!result.success) {
        console.warn("Backend connection failed on startup:", result.error);
      }
    });

    // Listen for storage changes (in case user opens multiple tabs or changes settings)
    const handleStorageChange = (event) => {
      if (event.key === "recentAnalyses") {
        loadRecentAnalyses();
      } else if (event.key === "resumeAnalyzerSettings") {
        loadDefaultPriorities();
      }
    };
    window.addEventListener("storage", handleStorageChange);

    // Click outside handler to close dropdowns
    const handleClickOutside = (event) => {
      if (showDropdownId && !event.target.closest(".card-menu")) {
        setShowDropdownId(null);
      }
    };

    document.addEventListener("click", handleClickOutside);

    return () => {
      window.removeEventListener("storage", handleStorageChange);
      document.removeEventListener("click", handleClickOutside);
    };
  }, [showDropdownId]);

  // Show settings page if requested
  if (showSettings) {
    return <SettingsPage onBackToDashboard={handleBackToDashboard} />;
  }

  // Show analysis results page if requested
  if (showAnalysisResults && currentAnalysis) {
    return (
      <AnalysisResultsPage
        analysisData={currentAnalysis}
        onBackToDashboard={handleBackToDashboard}
        onDownloadReport={handleDownloadReport}
        onShareReport={handleShareReport}
      />
    );
  }

  return (
    <div className="dashboard-container">
      {/* Main Content */}
      <main className="dashboard-main">
        {/* Hero Section */}
        <section className="hero-section">
          <h2 className="hero-title">AI-Powered Resume Analysis</h2>
          <p className="hero-subtitle">
            Get detailed insights based on your priorities
          </p>

          {/* Upload Zone */}
          <div
            className={`upload-zone ${isDragging ? "dragging" : ""} ${
              files.length > 0 ? "has-files" : ""
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="upload-content">
              <div className="upload-icon">
                <i
                  className={
                    files.length > 0
                      ? "bi bi-file-earmark-text"
                      : "bi bi-folder2-open"
                  }
                ></i>
              </div>
              <h3 className="upload-title">
                {files.length > 0
                  ? `${files.length} file${
                      files.length !== 1 ? "s" : ""
                    } selected`
                  : "Drag & drop area with upload icon"}
              </h3>
              <p className="upload-formats">Supported formats: PDF</p>
              <label className="browse-button">
                Browse files
                <input
                  type="file"
                  multiple
                  accept=".pdf"
                  onChange={handleFileInput}
                  style={{ display: "none" }}
                />
              </label>
            </div>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="files-preview">
              <h4>Selected Files:</h4>
              <ul className="files-list">
                {files.map((file, index) => (
                  <li key={index} className="file-item">
                    <span className="file-name">
                      <i className="bi bi-file-earmark-pdf"></i>
                      {file.name}
                    </span>
                    <span className="file-size">
                      {(file.size / 1024).toFixed(1)} KB
                    </span>
                    <button
                      className="remove-file"
                      onClick={() =>
                        setFiles((prev) => prev.filter((_, i) => i !== index))
                      }
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Priority Selection */}
          <div className="priority-section-new">
            <h3 className="priority-section-title">Select Top 3 Priorities</h3>

            <div className="priority-intro">
              <span>
                Choose what matters most for this analysis (optional):
              </span>
              <span className="priority-counter">
                Selected: ({selectedPriorities.length}/3)
              </span>
            </div>

            <div className="priority-grid-new">
              {priorities.map((priority) => (
                <label
                  key={priority.id}
                  className={`priority-checkbox ${
                    selectedPriorities.includes(priority.id) ? "selected" : ""
                  } ${
                    selectedPriorities.length >= 3 &&
                    !selectedPriorities.includes(priority.id)
                      ? "disabled"
                      : ""
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedPriorities.includes(priority.id)}
                    onChange={() => handlePriorityToggle(priority.id)}
                    disabled={
                      selectedPriorities.length >= 3 &&
                      !selectedPriorities.includes(priority.id)
                    }
                  />
                  <span className="checkbox-label">{priority.label}</span>
                  {getPriorityOrder(priority.id) && (
                    <span className="priority-order-number">
                      {getPriorityOrder(priority.id)}
                    </span>
                  )}
                </label>
              ))}
            </div>

            {/* Default Priorities Display */}
            {selectedPriorities.length === 0 &&
              defaultPriorities.length > 0 && (
                <div className="default-priorities-info">
                  <span className="default-icon">
                    <i className="bi bi-gear"></i>
                  </span>
                  <span className="default-text">
                    Default priorities will be used:{" "}
                    {defaultPriorities.join(", ")}
                  </span>
                  <button
                    className="settings-link"
                    onClick={goToSettings}
                    title="Adjust default priorities in settings"
                  >
                    Edit
                  </button>
                </div>
              )}

            {/* Analyze Button - Always visible */}
            <div className="analyze-button-container">
              <button
                className={`analyze-resume-btn ${isAnalyzing ? "loading" : ""}`}
                onClick={handleUpload}
                disabled={isAnalyzing || (backendStatus && !backendStatus.success)}
                title={
                  backendStatus?.isRateLimit
                    ? "Server is rate-limited. Please wait a moment before trying again."
                    : backendStatus && !backendStatus.success
                    ? "Backend server is not available. Click 'Test Backend' to check connection."
                    : "Start analysis"
                }
              >
                {isAnalyzing ? "Analyzing..." :
                 backendStatus?.isRateLimit ? "Rate Limited - Wait" :
                 (backendStatus && !backendStatus.success) ? "Backend Unavailable" :
                 "Analyze Resume"}
              </button>

              {/* Backend Connection Test Button */}
              <button
                className="test-connection-btn"
                onClick={handleTestConnection}
                title="Test backend server connection"
                style={{
                  marginLeft: '10px',
                  padding: '8px 16px',
                  backgroundColor:
                    backendStatus?.isRateLimit ? '#ff9800' :
                    backendStatus?.success ? '#28a745' : '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                {backendStatus === null ? 'Test Backend' :
                 backendStatus.isRateLimit ? '⏰ Rate Limited' :
                 backendStatus.success ? '✅ Connected' : '❌ Failed'}
              </button>

              {/* Refresh Results Button */}
              <button
                className="refresh-results-btn"
                onClick={handleRefreshResults}
                title="Manually check for completed bulk analyses"
                style={{
                  marginLeft: '10px',
                  padding: '8px 16px',
                  backgroundColor: '#17a2b8',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                🔄 Refresh Results
              </button>
            </div>
          </div>

          {/* Recent Analyses */}
          <div className="recent-analyses-new">
            <div className="recent-analyses-header">
              <h3 className="recent-analyses-title">Recent Analysis</h3>
              {JSON.parse(localStorage.getItem("recentAnalyses") || "[]")
                .length > 0 && (
                <button
                  className="view-all-button"
                  onClick={goToHistory}
                  title="View all analyses in History page"
                >
                  View All
                </button>
              )}
            </div>
            {recentAnalyses.length > 0 ? (
              <div className="recent-analyses-grid">
                {recentAnalyses.map((analysis) => {
                  return (
                    <div key={analysis.id} className="recent-analysis-card">
                      {/* Top row: Name, Date, Delete button */}
                      <div className="card-header-row">
                        <div className="card-name-text">{analysis.name}</div>
                        <div className="card-right-section">
                          <div className="card-date-text">
                            {(() => {
                              try {
                                const date = new Date(analysis.uploadedAt || analysis.timestamp || Date.now());
                                return isNaN(date.getTime())
                                  ? new Date().toLocaleDateString()
                                  : date.toLocaleDateString();
                              } catch (e) {
                                return new Date().toLocaleDateString();
                              }
                            })()}
                          </div>
                          <button
                            className="card-delete-btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRemoveAnalysis(analysis.id);
                            }}
                            title="Delete analysis"
                          >
                            <i className="bi bi-trash"></i>
                          </button>
                        </div>
                      </div>

                      {/* Center: Score */}
                      <div className="card-score-center">
                        {analysis.status === "processing" ? (
                          <span className="processing-indicator">
                            Processing...
                          </span>
                        ) : (
                          <span className="score-percentage">
                            {analysis.score || analysis.overall_score || 0}%
                          </span>
                        )}
                      </div>

                      {/* Tags */}
                      <div className="card-tags">
                        {analysis.priorities
                          .slice(0, 2)
                          .map((priority, index) => (
                            <span key={index} className="tag">
                              {priority}
                            </span>
                          ))}
                        {analysis.priorities.length > 2 && (
                          <span className="tag-more">
                            +{analysis.priorities.length - 2}
                          </span>
                        )}
                      </div>

                      {/* Bottom: View Analysis button */}
                      <button
                        className="view-analysis-btn"
                        disabled={analysis.status === "processing"}
                        onClick={() => handleViewAnalysis(analysis)}
                        title={analysis.status === "processing" ? "Analysis is still processing" : "View analysis details"}
                      >
                        {analysis.status === "processing" ? "Processing..." : "View Analysis"}
                      </button>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="empty-analyses-new">
                <div className="empty-icon">
                  <i className="bi bi-file-earmark-text"></i>
                </div>
                <p>No recent analyses</p>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default EnhancedDashboard;
