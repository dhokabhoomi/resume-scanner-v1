import React, { useState, useEffect } from "react";
import styled, { css } from "styled-components";
import { DEFAULT_PRIORITIES } from "../constants/priorities";

// Styled Components for Header Section
const StyledHeader = styled.header`
  background: var(--bg-header);
  border-bottom: 1px solid var(--border-primary);
  padding: 1rem 2rem;
  box-shadow: var(--shadow-sm);
`;

const HeaderContent = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;

  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1rem;
  }
`;

const HeaderLeft = styled.div`
  display: flex;
  align-items: center;
  gap: 1.5rem;

  @media (max-width: 768px) {
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }
`;

const CandidateNameHeader = styled.h1`
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;

  @media (max-width: 480px) {
    font-size: 1.2rem;
  }
`;

const HeaderActions = styled.div`
  display: flex;
  gap: 1rem;
  align-items: center;

  @media (max-width: 768px) {
    flex-wrap: wrap;
    justify-content: center;
  }
`;

const ActionButton = styled.button`
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
  border: 1px solid;

  ${(props) =>
    props.$variant === "back" &&
    css`
      background: transparent;
      color: var(--accent-primary);
      border-color: var(--accent-primary);

      &:hover {
        background: var(--accent-primary);
        color: white;
      }
    `}

  ${(props) =>
    props.$variant === "download" &&
    css`
      background: var(--accent-success);
      color: white;
      border-color: var(--accent-success);

      &:hover {
        background: var(--accent-success);
        opacity: 0.9;
      }
    `}

  ${(props) =>
    props.$variant === "share" &&
    css`
      background: var(--accent-secondary);
      color: white;
      border-color: var(--accent-secondary);

      &:hover {
        background: var(--accent-primary-hover);
      }
    `}
`;

// Main Content Layout
const AnalysisMain = styled.main`
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;

  @media (max-width: 1024px) {
    padding: 1rem;
  }

  @media (max-width: 480px) {
    padding: 0.5rem;
  }
`;

// Card Components
const SectionCard = styled.section`
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: var(--shadow-md);

  @media (max-width: 480px) {
    padding: 1rem;
  }
`;

const CardHeader = styled.h3`
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 1.5rem;
`;

// Candidate Summary
const CandidateSummary = styled(SectionCard)`
  display: flex;
  justify-content: space-between;
  align-items: center;

  @media (max-width: 1024px) {
    flex-direction: column;
    text-align: center;
    gap: 2rem;
  }
`;

const SummaryInfo = styled.div`
  h2 {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
  }

  p.position {
    font-size: 1.2rem;
    color: var(--accent-primary);
    font-weight: 600;
    margin-bottom: 1rem;
  }
`;

const ContactInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;

  span {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  @media (max-width: 768px) {
    align-items: center;
  }
`;

const AnalysisTimestamp = styled.div`
  color: var(--text-tertiary);
  font-size: 0.85rem;
  font-style: italic;
`;

const OverallScoreDisplay = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
`;

const ScoreCircleLarge = styled.div`
  position: relative;
  width: 120px;
  height: 120px;
`;

const ScoreContent = styled.div`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
`;

const ScoreNumber = styled.span`
  display: block;
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
`;

const ScoreGrade = styled.span`
  font-size: 1rem;
  color: var(--text-tertiary);
  font-weight: 600;
`;

// Score Breakdown
const ScoreBreakdown = styled(SectionCard)`
  position: relative;
  overflow: visible;
  z-index: 1;
`;

const BreakdownBars = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  position: relative;
  width: 100%;
`;

const ScoreBarContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 8px 0;
  position: relative;
  width: 100%;
  contain: layout;
`;

const ScoreBarHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  min-height: 24px;
  position: relative;
  width: 100%;
`;

const CategoryName = styled.span`
  font-weight: 600;
  color: var(--text-primary);
  text-transform: capitalize;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  position: relative;
`;

const ScoreValue = styled.span`
  font-weight: 700;
  color: var(--accent-primary);
  font-size: 0.9rem;
  white-space: nowrap;
  min-width: fit-content;
  background: rgba(59, 130, 246, 0.1);
  padding: 4px 8px;
  border-radius: 12px;
  border: 1px solid var(--accent-primary);
  flex-shrink: 0;
  display: inline-block;
`;

const ProgressBar = styled.div`
  width: 100%;
  height: 12px;
  background: var(--bg-tertiary);
  border-radius: 6px;
  overflow: hidden;
`;

const ProgressFill = styled.div`
  height: 100%;
  border-radius: 6px;
  transition: width 0.6s ease;
`;

// Priority Analysis
const PriorityAnalysis = styled(SectionCard)`
  /* Add any specific styles for PriorityAnalysis if needed */
`;

const PriorityIndicators = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const PriorityIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: 12px;
  border-left: 4px solid var(--accent-primary);
`;

const PriorityRank = styled.div`
  background: var(--accent-primary);
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.1rem;
`;

const PriorityInfo = styled.div`
  flex: 1;

  h4 {
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
  }

  p {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin: 0;
  }
`;

const PriorityScore = styled.div`
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--accent-primary);
`;

// Detailed Analysis Tabs
const AnalysisTabs = styled.div`
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  border-bottom: 1px solid var(--border-primary);

  @media (max-width: 768px) {
    flex-wrap: wrap;
  }
`;

const TabButton = styled.button`
  padding: 0.75rem 1.5rem;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
  border-bottom: 2px solid transparent;

  &:hover {
    color: var(--text-primary);
    background: var(--bg-secondary);
  }

  &.active {
    color: var(--accent-primary);
    border-bottom-color: var(--accent-primary);
  }

  @media (max-width: 768px) {
    flex: 1;
    min-width: 120px;
  }
`;

const TabContent = styled.div`
  min-height: 300px;

  h4 {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 1rem;
  }
`;

// Tab Content Sections
const SectionContent = styled.div`
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: 12px;
  margin-bottom: 20px;
`;

const SectionHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--border-primary);

  h4 {
    margin: 0;
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--text-primary);
  }
`;

const SectionScore = styled.div`
  background: var(--accent-primary);
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.9rem;
`;

const ContentDisplay = styled.div`
  margin: 16px 0;
  min-height: 60px;
`;

const NoContent = styled.div`
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
  padding: 20px;
  background: var(--bg-primary);
  border-radius: 8px;
  border: 1px dashed var(--border-primary);
`;

const SuggestionsBox = styled.div`
  background: linear-gradient(
    135deg,
    rgba(59, 130, 246, 0.1),
    rgba(139, 92, 246, 0.05)
  );
  border: 1px solid var(--accent-primary);
  border-radius: 8px;
  padding: 12px;
  margin-top: 12px;

  h5 {
    margin: 0 0 8px 0;
    color: var(--accent-primary);
    font-size: 0.95rem;
  }

  p {
    margin: 0;
    color: var(--text-primary);
    line-height: 1.5;
  }
`;

// Summary Content
const SummaryDetails = styled.div`
  background: var(--bg-primary);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid var(--border-primary);
`;

const SummaryTextContent = styled.div`
  strong {
    color: var(--accent-primary);
    font-size: 1rem;
    margin-bottom: 8px;
    display: block;
  }
`;

const SummaryQuote = styled.div`
  font-size: 1.1rem;
  line-height: 1.6;
  color: var(--text-primary);
  font-style: italic;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: 8px;
  border-left: 4px solid var(--accent-primary);
  margin-top: 12px;
  position: relative;
`;

// Skills Content
const SkillsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
`;

const SkillTag = styled.div`
  background: var(--accent-primary);
  color: white;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 0.85rem;
  font-weight: 500;

  &.soft {
    background: var(--accent-secondary);
  }
`;

// Experience Content
const ExperienceList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`;

const ExperienceItem = styled.div`
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s ease;
`;

const ExperienceHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;

  h5 {
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
`;

const CompanyName = styled.h5`
  color: var(--accent-primary);
  font-weight: 500;
  margin-bottom: 0.75rem;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--accent-primary);
`;

const ExperienceDetailsItem = styled.div`
  .detail-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 8px 0;

    strong {
      color: var(--text-primary);
      min-width: 100px;
      font-size: 0.9rem;
    }

    span {
      color: var(--text-primary);
      flex: 1;
    }

    @media (max-width: 768px) {
      flex-direction: column;
      gap: 0.25rem;

      strong {
        min-width: auto;
      }
    }
  }
`;

const AchievementsContent = styled.div`
  margin-top: 0.25rem;
`;

const AchievementsList = styled.ul`
  margin: 0.25rem 0;
  padding-left: 1rem;
  list-style: disc;

  li {
    margin: 0.25rem 0;
    color: var(--text-primary);
    line-height: 1.4;
  }
`;

// Education Content
const EducationList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const EducationItem = styled.div`
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--accent-primary);
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
  }
`;

const EducationHeader = styled.div`
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--accent-primary);
`;

const InstitutionName = styled.h5`
  color: var(--accent-primary);
  font-weight: 500;
  margin-bottom: 0.75rem;
  font-size: 1.1rem;
  margin: 0;
`;

const EducationDetailsItem = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const DetailInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 0.95rem;

  strong {
    color: var(--text-primary);
    min-width: 100px;
    font-size: 0.9rem;
  }
`;

const ValuePresent = styled.span`
  color: var(--text-primary);
  font-weight: 500;
  margin-left: 4px;
`;

const ValueMissing = styled.span`
  color: var(--text-tertiary);
  font-style: italic;
  margin-left: 4px;
  opacity: 0.7;
`;

const EduDetails = styled.div`
  display: flex;
  gap: 2rem;

  span {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  @media (max-width: 768px) {
    flex-direction: column;
    gap: 0.5rem;
  }
`;

// Projects Content
const ProjectsList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`;

const ProjectItem = styled.div`
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s ease;

  h5 {
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.75rem;
  }
`;

const ProjectName = styled.div`
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.75rem;
`;

const TechStack = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
`;

const TechTag = styled.div`
  background: var(--accent-success);
  color: white;
  padding: 0.2rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
`;

const ProjectDescription = styled.p`
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0;
`;

// Certifications & Activities
const CertActivityItem = styled.div`
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: 8px;
  padding: 12px;
  margin: 8px 0;
`;

const CertActivityName = styled.div`
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
`;

const CertActivityDetail = styled.div`
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin: 2px 0;
`;

// Actionable Feedback
const ActionableFeedback = styled(SectionCard)`
  /* Add any specific styles for ActionableFeedback if needed */
`;

const FeedbackGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;

  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
`;

const FeedbackSection = styled.div`
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid var(--border-primary);

  h4 {
    font-weight: 600;
    margin-bottom: 1rem;
  }

  ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  li {
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border-primary);
    color: var(--text-secondary);
    line-height: 1.4;

    &:last-child {
      border-bottom: none;
    }
  }

  ${(props) =>
    props.$variant === "strengths" &&
    css`
      background: rgba(16, 185, 129, 0.05);
      border-color: rgba(16, 185, 129, 0.2);

      h4 {
        color: var(--accent-success);
      }
    `}

  ${(props) =>
    props.$variant === "improvements" &&
    css`
      background: rgba(245, 158, 11, 0.05);
      border-color: rgba(245, 158, 11, 0.2);

      h4 {
        color: var(--accent-warning);
      }
    `}

  ${(props) =>
    props.$variant === "recommendations" &&
    css`
      background: rgba(139, 92, 246, 0.05);
      border-color: rgba(139, 92, 246, 0.2);

      h4 {
        color: var(--accent-secondary);
      }
    `}
`;

const AnalysisResultsPageWrapper = styled.div`
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
`;

function AnalysisResultsPage({
  analysisData,
  onBackToDashboard,
  onDownloadReportCSV,
  onDownloadReportPDF,
  onShareReport,
  showExportDropdown,
  setShowExportDropdown,
}) {
  const [activeTab, setActiveTab] = useState("summary");

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showExportDropdown && setShowExportDropdown) {
        const dropdown = event.target.closest('[data-dropdown-container]');
        if (!dropdown) {
          setShowExportDropdown(false);
        }
      }
    };

    document.addEventListener("click", handleClickOutside);
    return () => {
      document.removeEventListener("click", handleClickOutside);
    };
  }, [showExportDropdown, setShowExportDropdown]);

  // Extract real data - ALWAYS expect complete detailed analysis
  // For single analysis: MUST have analysisData.analysis with complete AIAnalysisResult data
  // For bulk analysis: MUST have analysisData.fullAnalysis.analysis with complete data
  // Final fallback: analysisData.fullAnalysis directly
  const realAnalysis = analysisData?.analysis || analysisData?.fullAnalysis?.full_analysis || analysisData?.fullAnalysis?.analysis || analysisData?.fullAnalysis || {};

  // Validate that we have complete analysis data
  if (!realAnalysis.basic_info || !realAnalysis.professional_summary) {
    console.error("INCOMPLETE ANALYSIS DATA:", {
      hasAnalysis: !!analysisData?.analysis,
      hasFullAnalysisFullAnalysis: !!analysisData?.fullAnalysis?.full_analysis,
      hasFullAnalysisAnalysis: !!analysisData?.fullAnalysis?.analysis,
      hasFullAnalysisDirect: !!analysisData?.fullAnalysis,
      realAnalysisKeys: realAnalysis ? Object.keys(realAnalysis) : null,
      realAnalysis: realAnalysis
    });

    // Log the full structure to understand what we actually have
    console.log("Full analysisData structure:", JSON.stringify(analysisData, null, 2));
  }

  // Extract enhanced data - MUST have complete data
  const ruleBasedFindings = analysisData?.rule_based_findings || analysisData?.fullAnalysis?.rule_based_findings;
  const priorityAnalysis = analysisData?.priority_analysis || analysisData?.fullAnalysis?.priority_analysis;
  const basicInfo = realAnalysis.basic_info?.content || {};

  // Debug logging to understand data structure
  console.log("AnalysisResultsPage - analysisData:", analysisData);
  console.log("AnalysisResultsPage - analysisData.analysis:", analysisData?.analysis);
  console.log("AnalysisResultsPage - analysisData.fullAnalysis?.full_analysis:", analysisData?.fullAnalysis?.full_analysis);
  console.log("AnalysisResultsPage - analysisData.fullAnalysis?.analysis:", analysisData?.fullAnalysis?.analysis);
  console.log("AnalysisResultsPage - realAnalysis:", realAnalysis);
  console.log("AnalysisResultsPage - realAnalysis.skills:", realAnalysis?.skills);
  console.log("AnalysisResultsPage - realAnalysis.skills?.content:", realAnalysis?.skills?.content);

  // If no analysis data is available, show error message
  if (!analysisData) {
    return (
      <AnalysisResultsPageWrapper>
        <div className="analysis-error">
          <h2>Analysis Not Available</h2>
          <p>Sorry, the analysis data could not be loaded. This might happen if:</p>
          <ul>
            <li>The analysis is still processing</li>
            <li>The analysis data was corrupted</li>
            <li>There was an error during analysis</li>
          </ul>
          <ActionButton $variant="back" onClick={onBackToDashboard}>
            Back to Dashboard
          </ActionButton>
        </div>
      </AnalysisResultsPageWrapper>
    );
  }

  const displayData = {
    candidate: {
      name:
        basicInfo.name ||
        analysisData?.candidate_name ||
        analysisData?.candidateName ||
        analysisData?.name ||
        "Unknown Candidate",
      position: "Job Seeker", // Could be extracted from summary if available
      email: basicInfo.email || "N/A",
      phone: basicInfo.phone || "N/A",
      location: basicInfo.location || "N/A",
    },
    overallScore:
      realAnalysis.overall_score || analysisData?.score || 0,
    completenessScore:
      ruleBasedFindings?.completeness_score || 85,
    factSheet: {
      summary:
        (analysisData?.fact_sheet || analysisData?.factSheet)?.summary ||
        "Analysis completed with enhanced data preservation",
      formattingScore:
        (analysisData?.fact_sheet || analysisData?.factSheet)?.formatting_score ||
        ruleBasedFindings?.formatting_analysis?.overall_formatting_score || 88.0,
      promptCustomized:
        (analysisData?.fact_sheet || analysisData?.factSheet)?.prompt_was_customized || true,
    },
    analysisTimestamp:
      analysisData?.uploadedAt || new Date().toLocaleDateString(),
    scoreBreakdown: (() => {
      const baseScore = realAnalysis.overall_score || analysisData?.score || 0;
      const priorityAnalysis = analysisData?.priority_analysis || analysisData?.fullAnalysis?.priority_analysis;


      const scores = {
        skills:
          // First try enhanced priority score for Technical Skills
          (priorityAnalysis?.priority_scores?.["Technical Skills"] > 0 ? priorityAnalysis.priority_scores["Technical Skills"] : null) ??
          (realAnalysis.skills?.quality_score > 0 ? realAnalysis.skills.quality_score : null) ??
          (realAnalysis.skills ? Math.max(baseScore - 10, 30) : Math.max(baseScore - 5, 25)),
        experience:
          // First try enhanced priority score for Work Experience
          (priorityAnalysis?.priority_scores?.["Work Experience"] > 0 ? priorityAnalysis.priority_scores["Work Experience"] : null) ??
          (realAnalysis.work_experience?.quality_score > 0 ? realAnalysis.work_experience.quality_score : null) ??
          (realAnalysis.work_experience ? Math.max(baseScore - 5, 35) : Math.max(baseScore - 5, 30)),
        education:
          // First try enhanced priority score for Academic Performance
          (priorityAnalysis?.priority_scores?.["Academic Performance"] > 0 ? priorityAnalysis.priority_scores["Academic Performance"] : null) ??
          (realAnalysis.education?.quality_score > 0 ? realAnalysis.education.quality_score : null) ??
          (realAnalysis.education ? Math.max(baseScore - 5, 30) : Math.max(baseScore - 10, 25)),
        projects:
          // First try enhanced priority score for Project Experience
          priorityAnalysis?.priority_scores?.["Project Experience"] ??
          (realAnalysis.projects?.quality_score > 0 ? realAnalysis.projects.quality_score : null) ??
          (realAnalysis.projects ? Math.max(baseScore - 15, 20) : Math.max(baseScore - 20, 15)),
        formatting:
          // First try enhanced priority score for Resume Formatting
          priorityAnalysis?.priority_scores?.["Resume Formatting"] ??
          analysisData?.rule_based_findings?.formatting_analysis?.overall_formatting_score ??  // Enhanced bulk analysis
          analysisData?.formatting_score ??                                                      // Legacy bulk analysis
          (realAnalysis.formatting_issues?.quality_score > 0 ? realAnalysis.formatting_issues.quality_score : null) ??  // Single analysis
          realAnalysis.formatting_issues?.content?.formatting_score ??                           // Single analysis fallback
          Math.min(baseScore + 10, 100),
        certifications:
          // First try enhanced priority score for Certifications
          (priorityAnalysis?.priority_scores?.["Certifications"] > 0 ? priorityAnalysis.priority_scores["Certifications"] : null) ??
          (realAnalysis.certifications?.quality_score > 0 ? realAnalysis.certifications.quality_score : null) ??
          (realAnalysis.certifications ? Math.max(baseScore - 20, 15) : Math.max(baseScore - 25, 10)),
        extracurriculars:
          // First try enhanced priority score for Extracurricular Activities
          priorityAnalysis?.priority_scores?.["Extracurricular Activities"] ??
          (realAnalysis.extracurriculars?.quality_score > 0 ? realAnalysis.extracurriculars.quality_score : null) ??
          (realAnalysis.extracurriculars ? Math.max(baseScore - 20, 15) : Math.max(baseScore - 25, 10)),
      };


      return scores;
    })(),
    priorities:
      priorityAnalysis?.selected_priorities || analysisData?.priorities || DEFAULT_PRIORITIES,
    sections: {
      skills: {
        score: (realAnalysis.skills?.quality_score > 0 ? realAnalysis.skills.quality_score : null) || Math.max((analysisData?.score || 0) - 5, 25),
        content: (() => {
          // Handle multiple skills data formats - prioritize original format
          const skillsData = realAnalysis.skills?.content;

          if (!skillsData) {
            return {};
          }

          // If we have original_format, use that as the primary display
          if (skillsData.original_format) {
            return {
              original_format: skillsData.original_format,
              is_properly_categorized: skillsData.is_properly_categorized,
              // Include categorized data only if it exists and is properly categorized
              ...(skillsData.is_properly_categorized && {
                technical_skills: skillsData.technical_skills,
                hard_skills: skillsData.hard_skills,
                soft_skills: skillsData.soft_skills
              })
            };
          }

          // Fallback to existing logic for backward compatibility
          if (skillsData.technical_skills || skillsData.hard_skills || skillsData.soft_skills) {
            return skillsData;
          }
          if (Array.isArray(skillsData)) {
            return { technical_skills: skillsData };
          }
          return skillsData;
        })(),
        suggestions:
          realAnalysis.skills?.suggestions ||
          "Analysis completed. Detailed suggestions available in full analysis mode.",
      },
      experience: {
        score: (realAnalysis.work_experience?.quality_score > 0 ? realAnalysis.work_experience.quality_score : null) || Math.max((analysisData?.score || 0) - 5, 30),
        content: realAnalysis.work_experience?.content || {},
        suggestions:
          realAnalysis.work_experience?.suggestions ||
          "Analysis completed. Detailed suggestions available in full analysis mode.",
      },
      education: {
        score: (realAnalysis.education?.quality_score > 0 ? realAnalysis.education.quality_score : null) || Math.max((analysisData?.score || 0) - 10, 25),
        content: realAnalysis.education?.content || {},
        suggestions:
          realAnalysis.education?.suggestions ||
          "Analysis completed. Detailed suggestions available in full analysis mode.",
      },
      projects: {
        score: (realAnalysis.projects?.quality_score > 0 ? realAnalysis.projects.quality_score : null) || Math.max((analysisData?.score || 0) - 20, 15),
        content: realAnalysis.projects?.content || {},
        suggestions:
          realAnalysis.projects?.suggestions ||
          "Analysis completed. Detailed suggestions available in full analysis mode.",
      },
      certifications: {
        score: (realAnalysis.certifications?.quality_score > 0 ? realAnalysis.certifications.quality_score : null) || Math.max((analysisData?.score || 0) - 25, 10),
        content: realAnalysis.certifications?.content || {},
        suggestions:
          realAnalysis.certifications?.suggestions ||
          "Analysis completed. Detailed suggestions available in full analysis mode.",
      },
      extracurriculars: {
        score: (realAnalysis.extracurriculars?.quality_score > 0 ? realAnalysis.extracurriculars.quality_score : null) || Math.max((analysisData?.score || 0) - 25, 10),
        content: realAnalysis.extracurriculars?.content || {},
        suggestions:
          realAnalysis.extracurriculars?.suggestions ||
          "Analysis completed. Detailed suggestions available in full analysis mode.",
      },
      professional_summary: {
        score: (realAnalysis.professional_summary?.quality_score > 0 ? realAnalysis.professional_summary.quality_score : null) || Math.max((analysisData?.score || 0) - 10, 20),
        content: realAnalysis.professional_summary?.content || {},
        suggestions:
          realAnalysis.professional_summary?.suggestions ||
          "Analysis completed. Detailed suggestions available in full analysis mode.",
      },
    },
    feedback: {
      strengths: [],
      improvements: [],
      recommendations: [],
    },
  };

  // Calculate feedback based on actual scores (after displayData is created)
  const calculateFeedback = () => {
    const sections = [
      { name: 'Technical Skills', score: displayData.scoreBreakdown.skills, suggestions: realAnalysis.skills?.suggestions },
      { name: 'Work Experience', score: displayData.scoreBreakdown.experience, suggestions: realAnalysis.work_experience?.suggestions },
      { name: 'Education', score: displayData.scoreBreakdown.education, suggestions: realAnalysis.education?.suggestions },
      { name: 'Projects', score: displayData.scoreBreakdown.projects, suggestions: realAnalysis.projects?.suggestions },
      { name: 'Professional Summary', score: displayData.sections.professional_summary.score, suggestions: realAnalysis.professional_summary?.suggestions },
    ];

    const strengths = [];
    const improvements = [];
    const recommendations = [];

    // Categorize based on scores (70+ = strength, <70 = improvement)
    sections.forEach(section => {
      if (section.score >= 70 && section.suggestions) {
        strengths.push(`${section.name}: Strong performance with well-structured content.`);
      } else if (section.score < 70 && section.suggestions) {
        improvements.push(`${section.name}: ${section.suggestions}`);
      }
    });

    // Add general strengths if overall score is good
    const baseScore = realAnalysis.overall_score || analysisData?.score || 0;
    if (baseScore >= 70) {
      strengths.unshift("Overall resume structure is well-organized and professional.");
    }

    // Add formatting feedback
    if (displayData.scoreBreakdown.formatting >= 80) {
      strengths.push("Resume formatting: Excellent layout and visual presentation.");
    } else if (displayData.scoreBreakdown.formatting < 70) {
      improvements.push("Resume formatting: Consider improving layout, spacing, and visual consistency.");
    }

    // Add certification and extracurricular recommendations
    if (realAnalysis.certifications?.suggestions) {
      recommendations.push(`Certifications: ${realAnalysis.certifications.suggestions}`);
    }
    if (realAnalysis.extracurriculars?.suggestions) {
      recommendations.push(`Extracurriculars: ${realAnalysis.extracurriculars.suggestions}`);
    }

    // Ensure we have at least one item in each category
    if (strengths.length === 0) {
      strengths.push("Resume contains valuable professional information ready for enhancement.");
    }
    if (improvements.length === 0) {
      improvements.push("Continue refining content to better highlight achievements and quantifiable results.");
    }
    if (recommendations.length === 0) {
      recommendations.push("Consider adding relevant certifications or professional development activities.");
    }

    return { strengths, improvements, recommendations };
  };

  // Update the feedback in displayData
  displayData.feedback = calculateFeedback();

  const getScoreColor = (score) => {
    if (score >= 90) return "#059669"; // Green for excellent
    if (score >= 80) return "#2563eb"; // Blue for good
    if (score >= 70) return "#d97706"; // Amber for average
    return "#dc2626"; // Red for poor
  };

  const getScoreGrade = (score) => {
    if (score >= 90) return "A";
    if (score >= 80) return "B";
    if (score >= 70) return "C";
    return "D";
  };

  const tabs = [
    { id: "summary", label: "Summary", icon: "bi bi-file-earmark-text" },
    { id: "skills", label: "Skills", icon: "bi bi-tools" },
    { id: "experience", label: "Experience", icon: "bi bi-briefcase" },
    { id: "education", label: "Education", icon: "bi bi-mortarboard" },
    { id: "projects", label: "Projects", icon: "bi bi-rocket-takeoff" },
    { id: "certifications", label: "Certifications", icon: "bi bi-award" },
    { id: "extracurriculars", label: "Activities", icon: "bi bi-trophy" },
  ];

  return (
    <AnalysisResultsPageWrapper>
      {/* Header */}
      <StyledHeader>
        <HeaderContent>
          <HeaderLeft>
            <ActionButton $variant="back" onClick={onBackToDashboard}>
              ← Back to Dashboard
            </ActionButton>
            <CandidateNameHeader>
              {displayData.candidate.name}
            </CandidateNameHeader>
          </HeaderLeft>
          <HeaderActions>
            <div style={{ position: 'relative', display: 'inline-block' }} data-dropdown-container>
              <ActionButton
                $variant="download"
                onClick={() => setShowExportDropdown && setShowExportDropdown(!showExportDropdown)}
              >
                <i className="bi bi-download"></i>
              </ActionButton>
              {showExportDropdown && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  right: 0,
                  background: 'var(--bg-primary)',
                  border: '1px solid var(--border-primary)',
                  borderRadius: '6px',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                  zIndex: 1000,
                  minWidth: '150px',
                  overflow: 'hidden'
                }}>
                  <button
                    style={{
                      display: 'block',
                      width: '100%',
                      padding: '8px 12px',
                      border: 'none',
                      background: 'var(--bg-primary)',
                      color: 'var(--text-primary)',
                      textAlign: 'left',
                      cursor: 'pointer',
                      fontSize: '13px',
                      borderBottom: '1px solid var(--border-primary)'
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      onDownloadReportCSV && onDownloadReportCSV();
                      setShowExportDropdown && setShowExportDropdown(false);
                    }}
                    onMouseEnter={(e) => e.target.style.background = 'var(--bg-secondary)'}
                    onMouseLeave={(e) => e.target.style.background = 'var(--bg-primary)'}
                  >
                    📊 Export as CSV
                  </button>
                  <button
                    style={{
                      display: 'block',
                      width: '100%',
                      padding: '8px 12px',
                      border: 'none',
                      background: 'var(--bg-primary)',
                      color: 'var(--text-primary)',
                      textAlign: 'left',
                      cursor: 'pointer',
                      fontSize: '13px'
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      onDownloadReportPDF && onDownloadReportPDF();
                      setShowExportDropdown && setShowExportDropdown(false);
                    }}
                    onMouseEnter={(e) => e.target.style.background = 'var(--bg-secondary)'}
                    onMouseLeave={(e) => e.target.style.background = 'var(--bg-primary)'}
                  >
                    📄 Export as PDF
                  </button>
                </div>
              )}
            </div>
            <ActionButton $variant="share" onClick={onShareReport}>
              <i className="bi bi-share"></i>
            </ActionButton>
          </HeaderActions>
        </HeaderContent>
      </StyledHeader>

      {/* Main Content */}
      <AnalysisMain>
        {/* Candidate Summary */}
        <CandidateSummary>
          <SummaryInfo>
            <h2>{displayData.candidate.name}</h2>
            <p className="position">{displayData.candidate.position}</p>
            <ContactInfo>
              <span>📧 {displayData.candidate.email}</span>
              <span>📱 {displayData.candidate.phone}</span>
              <span>📍 {displayData.candidate.location}</span>
            </ContactInfo>
            <AnalysisTimestamp>
              📅 Analyzed on {displayData.analysisTimestamp}
            </AnalysisTimestamp>
          </SummaryInfo>
          <OverallScoreDisplay>
            <ScoreCircleLarge>
              <svg width="120" height="120">
                <circle
                  cx="60"
                  cy="60"
                  r="50"
                  stroke="#e5e7eb"
                  strokeWidth="8"
                  fill="none"
                />
                <circle
                  cx="60"
                  cy="60"
                  r="50"
                  stroke={getScoreColor(displayData.overallScore)}
                  strokeWidth="8"
                  fill="none"
                  strokeLinecap="round"
                  strokeDasharray={`${
                    (displayData.overallScore / 100) * 314
                  } 314`}
                  style={{
                    transformOrigin: "center",
                    transform: "rotate(-90deg)",
                  }}
                />
              </svg>
              <ScoreContent>
                <ScoreNumber>{displayData.overallScore}</ScoreNumber>
                <ScoreGrade>
                  {getScoreGrade(displayData.overallScore)}
                </ScoreGrade>
              </ScoreContent>
            </ScoreCircleLarge>
          </OverallScoreDisplay>
        </CandidateSummary>

        {/* Score Breakdown */}
        <ScoreBreakdown>
          <CardHeader>Score Breakdown</CardHeader>
          <BreakdownBars>
            {Object.entries(displayData.scoreBreakdown).map(
              ([category, score]) => (
                <ScoreBarContainer key={category}>
                  <ScoreBarHeader>
                    <CategoryName>
                      {category.charAt(0).toUpperCase() + category.slice(1)}
                    </CategoryName>
                    <ScoreValue>
                      {typeof score === "number"
                        ? `${score}%`
                        : score || "No data"}
                    </ScoreValue>
                  </ScoreBarHeader>
                  <ProgressBar>
                    <ProgressFill
                      style={{
                        width: `${Math.max(score, 0)}%`,
                        backgroundColor:
                          score > 0 ? getScoreColor(score) : "#e5e7eb",
                        minHeight: "8px",
                      }}
                    />
                  </ProgressBar>
                </ScoreBarContainer>
              )
            )}
          </BreakdownBars>
        </ScoreBreakdown>

        {/* Priority Analysis */}
        <PriorityAnalysis>
          <CardHeader>Priority Analysis</CardHeader>
          <PriorityIndicators>
            {displayData.priorities.map((priority, index) => (
              <PriorityIndicator key={priority}>
                <PriorityRank>{index + 1}</PriorityRank>
                <PriorityInfo>
                  <h4>{priority}</h4>
                  <p>
                    {(() => {
                      // Try to get detailed feedback from enhanced priority analysis
                      if (priorityAnalysis?.priority_feedback?.[priority]?.feedback) {
                        return priorityAnalysis.priority_feedback[priority].feedback.join(". ");
                      }
                      // Fallback to generic message
                      return "Strong performance in this priority area with room for specific improvements.";
                    })()}
                  </p>
                </PriorityInfo>
                <PriorityScore>
                  {(() => {
                    // First use enhanced priority analysis scores (more accurate with rule-based adjustments)
                    if (priorityAnalysis?.priority_scores?.[priority]) {
                      return `${priorityAnalysis.priority_scores[priority]}%`;
                    }

                    // Fallback to priority_scores field directly
                    if (analysisData?.priority_scores?.[priority]) {
                      return `${analysisData.priority_scores[priority]}%`;
                    }

                    // Final fallback to Score Breakdown values
                    const priorityMapping = {
                      "Technical Skills": displayData.scoreBreakdown.skills,
                      "Work Experience": displayData.scoreBreakdown.experience,
                      "Academic Performance": displayData.scoreBreakdown.education,
                      "Project Experience": displayData.scoreBreakdown.projects,
                      "Resume Formatting": displayData.scoreBreakdown.formatting,
                      Certifications: displayData.sections.certifications.score,
                      "Skill Diversity": displayData.scoreBreakdown.skills,
                    };

                    const score =
                      priorityMapping[priority] ??
                      displayData.scoreBreakdown[priority.toLowerCase().split(" ")[0]] ??
                      0;
                    return score > 0 ? `${score}%` : "No data";
                  })()}
                </PriorityScore>
              </PriorityIndicator>
            ))}
          </PriorityIndicators>
        </PriorityAnalysis>

        {/* Detailed Section Analysis */}
        <SectionCard>
          <CardHeader>Detailed Section Analysis</CardHeader>
          <AnalysisTabs>
            {tabs.map((tab) => (
              <TabButton
                key={tab.id}
                className={activeTab === tab.id ? "active" : ""}
                onClick={() => setActiveTab(tab.id)}
              >
                <i className={tab.icon}></i> {tab.label}
              </TabButton>
            ))}
          </AnalysisTabs>

          <TabContent>
            {activeTab === "summary" && (
              <SectionContent>
                <SectionHeader>
                  <h4>
                    <i className="bi bi-file-earmark-text"></i>
                    Professional Summary
                  </h4>
                  <SectionScore>
                    Score: {displayData.sections.professional_summary.score}/100
                  </SectionScore>
                </SectionHeader>

                <ContentDisplay>
                  {displayData.sections.professional_summary.content
                    .summary_text ? (
                    <SummaryDetails>
                      <SummaryTextContent>
                        <strong>Extracted Summary:</strong>
                        <SummaryQuote>
                          "
                          {
                            displayData.sections.professional_summary.content
                              .summary_text
                          }
                          "
                        </SummaryQuote>
                      </SummaryTextContent>
                    </SummaryDetails>
                  ) : (
                    <NoContent>
                      No professional summary found in resume
                    </NoContent>
                  )}
                </ContentDisplay>

                <SuggestionsBox>
                  <h5>
                    <i className="bi bi-lightbulb"></i> Suggestions:
                  </h5>
                  <p>{displayData.sections.professional_summary.suggestions}</p>
                </SuggestionsBox>
              </SectionContent>
            )}

            {activeTab === "skills" && (
              <SectionContent>
                <SectionHeader>
                  <h4>
                    <i className="bi bi-tools"></i>
                    Technical Skills Assessment
                  </h4>
                  <SectionScore>
                    Score: {displayData.sections.skills.score}/100
                  </SectionScore>
                </SectionHeader>

                <ContentDisplay>
                  {(() => {
                    const skillsContent = displayData.sections.skills.content;
                    console.log("Skills content debug:", skillsContent);
                    console.log("Skills content type:", typeof skillsContent);
                    console.log("Skills content keys:", skillsContent ? Object.keys(skillsContent) : 'null');

                    // Check if skillsContent exists and has data
                    if (!skillsContent) {
                      console.log("No skills content found");
                      return (
                        <NoContent>
                          <p>No skills data available.</p>
                        </NoContent>
                      );
                    }

                    const hasOriginalFormat = skillsContent && skillsContent.original_format;
                    const hasNewFormat = skillsContent && (
                      (skillsContent.technical_skills && typeof skillsContent.technical_skills === 'object' && !Array.isArray(skillsContent.technical_skills) && Object.keys(skillsContent.technical_skills).length > 0) ||
                      (skillsContent.hard_skills && typeof skillsContent.hard_skills === 'object' && !Array.isArray(skillsContent.hard_skills) && Object.keys(skillsContent.hard_skills).length > 0) ||
                      (skillsContent.soft_skills && typeof skillsContent.soft_skills === 'object' && !Array.isArray(skillsContent.soft_skills) && Object.keys(skillsContent.soft_skills).length > 0)
                    );

                    const hasLegacyFormat = skillsContent && (
                      (Array.isArray(skillsContent.technical_skills) && skillsContent.technical_skills.length > 0) ||
                      (Array.isArray(skillsContent.soft_skills) && skillsContent.soft_skills.length > 0) ||
                      (Array.isArray(skillsContent.languages) && skillsContent.languages.length > 0) ||
                      (skillsContent.skill_categories && Array.isArray(skillsContent.skill_categories) && skillsContent.skill_categories.length > 0)
                    );

                    console.log("Has original format:", hasOriginalFormat);
                    console.log("Has new format:", hasNewFormat);
                    console.log("Has legacy format:", hasLegacyFormat);

                    if (hasOriginalFormat) {
                      return (
                        <div className="original-skills-format">
                          <h5><i className="bi bi-star"></i> Skills (As Written in Resume)</h5>
                          <div style={{
                            whiteSpace: 'pre-wrap',
                            lineHeight: '1.6',
                            padding: '12px',
                            backgroundColor: 'var(--bg-tertiary)',
                            borderRadius: '8px',
                            border: '1px solid var(--border-primary)'
                          }}>
                            {skillsContent.original_format}
                          </div>
                          {skillsContent.is_properly_categorized === false && (
                            <div style={{
                              marginTop: '12px',
                              padding: '8px 12px',
                              backgroundColor: 'rgba(245, 158, 11, 0.1)',
                              borderLeft: '3px solid var(--accent-warning)',
                              borderRadius: '4px'
                            }}>
                              <small style={{ color: 'var(--accent-warning)' }}>
                                💡 Consider organizing skills into categories: Technical Skills, Hard Skills, and Soft Skills for better readability.
                              </small>
                            </div>
                          )}
                        </div>
                      );
                    } else if (hasNewFormat) {
                      return (
                        <>
                          {/* Technical Skills Section - New Format */}
                          {skillsContent.technical_skills && typeof skillsContent.technical_skills === 'object' && (
                            <div className="skill-category-section">
                              <h5><i className="bi bi-code-slash"></i> Technical Skills</h5>
                              {Object.entries(skillsContent.technical_skills).map(([category, skills], index) => (
                                skills && Array.isArray(skills) && skills.length > 0 && (
                                  <div key={index} className="skill-subcategory">
                                    <h6>{category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h6>
                                    <SkillsGrid>
                                      {skills.map((skill, skillIndex) => (
                                        <SkillTag key={skillIndex} className="technical">
                                          {skill}
                                        </SkillTag>
                                      ))}
                                    </SkillsGrid>
                                  </div>
                                )
                              ))}
                            </div>
                          )}

                          {/* Hard Skills Section - New Format */}
                          {skillsContent.hard_skills && typeof skillsContent.hard_skills === 'object' && (
                            <div className="skill-category-section">
                              <h5><i className="bi bi-tools"></i> Hard Skills</h5>
                              {Object.entries(skillsContent.hard_skills).map(([category, skills], index) => (
                                skills && Array.isArray(skills) && skills.length > 0 && (
                                  <div key={index} className="skill-subcategory">
                                    <h6>{category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h6>
                                    <SkillsGrid>
                                      {skills.map((skill, skillIndex) => (
                                        <SkillTag key={skillIndex} className="hard">
                                          {skill}
                                        </SkillTag>
                                      ))}
                                    </SkillsGrid>
                                  </div>
                                )
                              ))}
                            </div>
                          )}

                          {/* Soft Skills Section - New Format */}
                          {skillsContent.soft_skills && typeof skillsContent.soft_skills === 'object' && (
                            <div className="skill-category-section">
                              <h5><i className="bi bi-people"></i> Soft Skills</h5>
                              {Object.entries(skillsContent.soft_skills).map(([category, skills], index) => (
                                skills && Array.isArray(skills) && skills.length > 0 && (
                                  <div key={index} className="skill-subcategory">
                                    <h6>{category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h6>
                                    <SkillsGrid>
                                      {skills.map((skill, skillIndex) => (
                                        <SkillTag key={skillIndex} className="soft">
                                          {skill}
                                        </SkillTag>
                                      ))}
                                    </SkillsGrid>
                                  </div>
                                )
                              ))}
                            </div>
                          )}

                          {/* Languages Section */}
                          {skillsContent.languages && Array.isArray(skillsContent.languages) && skillsContent.languages.length > 0 && (
                            <div className="skill-category-section">
                              <h5><i className="bi bi-globe"></i> Languages</h5>
                              <SkillsGrid>
                                {skillsContent.languages.map((language, index) => (
                                  <SkillTag key={index} className="language">
                                    {language}
                                  </SkillTag>
                                ))}
                              </SkillsGrid>
                            </div>
                          )}
                        </>
                      );
                    } else if (hasLegacyFormat) {
                      return (
                        <>
                          {/* Legacy Technical Skills */}
                          {Array.isArray(skillsContent.technical_skills) && skillsContent.technical_skills.length > 0 && (
                            <div className="skill-category-section">
                              <h5><i className="bi bi-code-slash"></i> Technical Skills</h5>
                              <SkillsGrid>
                                {skillsContent.technical_skills.map((skill, index) => (
                                  <SkillTag key={index} className="technical">
                                    {skill}
                                  </SkillTag>
                                ))}
                              </SkillsGrid>
                            </div>
                          )}

                          {/* Legacy Soft Skills */}
                          {Array.isArray(skillsContent.soft_skills) && skillsContent.soft_skills.length > 0 && (
                            <div className="skill-category-section">
                              <h5><i className="bi bi-people"></i> Soft Skills</h5>
                              <SkillsGrid>
                                {skillsContent.soft_skills.map((skill, index) => (
                                  <SkillTag key={index} className="soft">
                                    {skill}
                                  </SkillTag>
                                ))}
                              </SkillsGrid>
                            </div>
                          )}

                          {/* Legacy Languages */}
                          {Array.isArray(skillsContent.languages) && skillsContent.languages.length > 0 && (
                            <div className="skill-category-section">
                              <h5><i className="bi bi-globe"></i> Languages</h5>
                              <SkillsGrid>
                                {skillsContent.languages.map((language, index) => (
                                  <SkillTag key={index} className="language">
                                    {language}
                                  </SkillTag>
                                ))}
                              </SkillsGrid>
                            </div>
                          )}

                          {/* Legacy skill_categories format */}
                          {skillsContent.skill_categories && Array.isArray(skillsContent.skill_categories) && skillsContent.skill_categories.length > 0 && (
                            <div className="skill-category-section">
                              <h5><i className="bi bi-tools"></i> All Skills</h5>
                              <SkillsGrid>
                                {skillsContent.skill_categories.map((skillCat, index) => (
                                  <SkillTag key={index} className="technical">
                                    {typeof skillCat === 'object' ? `${skillCat.name} (${skillCat.level})` : skillCat}
                                  </SkillTag>
                                ))}
                              </SkillsGrid>
                            </div>
                          )}
                        </>
                      );
                    } else {
                      // Fallback: try to display any skills data that exists
                      console.log("Fallback: Attempting to display skills data:", skillsContent);

                      if (skillsContent && typeof skillsContent === 'object' && Object.keys(skillsContent).length > 0) {
                        return (
                          <div className="fallback-skills-display">
                            <h5><i className="bi bi-list-ul"></i> Skills Information</h5>
                            <div style={{
                              padding: '12px',
                              backgroundColor: 'var(--bg-tertiary)',
                              borderRadius: '8px',
                              border: '1px solid var(--border-primary)'
                            }}>
                              {Object.entries(skillsContent).map(([key, value], index) => (
                                <div key={index} style={{ marginBottom: '8px' }}>
                                  <strong>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong>{' '}
                                  {Array.isArray(value) ? value.join(', ') :
                                   typeof value === 'object' ? JSON.stringify(value) :
                                   String(value)}
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      } else {
                        return (
                          <NoContent>
                            <p>Skills analysis not available for this resume.</p>
                          </NoContent>
                        );
                      }
                    }
                  })()}
                </ContentDisplay>

                <SuggestionsBox>
                  <h5>
                    <i className="bi bi-lightbulb"></i> Suggestions:
                  </h5>
                  <p>{displayData.sections.skills.suggestions}</p>
                </SuggestionsBox>
              </SectionContent>
            )}

            {activeTab === "experience" && (
              <SectionContent>
                <SectionHeader>
                  <h4>
                    <i className="bi bi-briefcase"></i>
                    Work Experience
                  </h4>
                  <SectionScore>
                    Score: {displayData.sections.experience.score}/100
                  </SectionScore>
                </SectionHeader>

                <ContentDisplay>
                  {displayData.sections.experience.content.companies &&
                  displayData.sections.experience.content.companies.length >
                    0 ? (
                    <ExperienceList>
                      {displayData.sections.experience.content.companies.map(
                        (company, index) => (
                          <ExperienceItem key={index}>
                            <CompanyName>{company}</CompanyName>

                            <ExperienceDetailsItem>
                              {displayData.sections.experience.content
                                .positions &&
                                displayData.sections.experience.content
                                  .positions[index] && (
                                  <div className="detail-row">
                                    <strong>Position:</strong>
                                    <span>
                                      {
                                        displayData.sections.experience.content
                                          .positions[index]
                                      }
                                    </span>
                                  </div>
                                )}

                              {displayData.sections.experience.content
                                .durations &&
                                displayData.sections.experience.content
                                  .durations[index] && (
                                  <div className="detail-row">
                                    <strong>Duration:</strong>
                                    <span>
                                      {
                                        displayData.sections.experience.content
                                          .durations[index]
                                      }
                                    </span>
                                  </div>
                                )}

                              {displayData.sections.experience.content
                                .descriptions &&
                                displayData.sections.experience.content
                                  .descriptions[index] && (
                                  <div className="detail-row">
                                    <strong>Description:</strong>
                                    <span>
                                      {
                                        displayData.sections.experience.content
                                          .descriptions[index]
                                      }
                                    </span>
                                  </div>
                                )}

                              {/* Key Achievements for this specific job */}
                              {displayData.sections.experience.content
                                .achievements &&
                                displayData.sections.experience.content
                                  .achievements[index] && (
                                  <div className="detail-row">
                                    <strong>Key Achievements:</strong>
                                    <AchievementsContent>
                                      {Array.isArray(
                                        displayData.sections.experience.content
                                          .achievements[index]
                                      ) ? (
                                        <AchievementsList>
                                          {displayData.sections.experience.content.achievements[
                                            index
                                          ].map((achievement, achIndex) => (
                                            <li key={achIndex}>
                                              {achievement}
                                            </li>
                                          ))}
                                        </AchievementsList>
                                      ) : (
                                        <span>
                                          {
                                            displayData.sections.experience
                                              .content.achievements[index]
                                          }
                                        </span>
                                      )}
                                    </AchievementsContent>
                                  </div>
                                )}
                            </ExperienceDetailsItem>
                          </ExperienceItem>
                        )
                      )}
                    </ExperienceList>
                  ) : (
                    <NoContent>
                      <p>Work experience details not available for this resume.</p>
                      <p><small>Experience Level: {displayData.sections.experience.content.experience_level || "Not specified"}</small></p>
                    </NoContent>
                  )}
                </ContentDisplay>

                <SuggestionsBox>
                  <h5>
                    <i className="bi bi-lightbulb"></i> Suggestions:
                  </h5>
                  <p>{displayData.sections.experience.suggestions}</p>
                </SuggestionsBox>
              </SectionContent>
            )}

            {activeTab === "education" && (
              <SectionContent>
                <SectionHeader>
                  <h4>
                    <i className="bi bi-mortarboard"></i>
                    Educational Background
                  </h4>
                  <SectionScore>
                    Score: {displayData.sections.education.score}/100
                  </SectionScore>
                </SectionHeader>

                <ContentDisplay>
                  {displayData.sections.education.content.institutions &&
                  displayData.sections.education.content.institutions.length >
                    0 ? (
                    <EducationList>
                      {displayData.sections.education.content.institutions.map(
                        (institution, index) => (
                          <EducationItem key={index}>
                            <EducationHeader>
                              <InstitutionName>
                                {institution}
                              </InstitutionName>
                            </EducationHeader>

                            <EducationDetailsItem>
                              {displayData.sections.education.content.degrees &&
                                displayData.sections.education.content.degrees[
                                  index
                                ] && (
                                  <DetailInfo>
                                    <strong>Degree:</strong>{" "}
                                    {
                                      displayData.sections.education.content
                                        .degrees[index]
                                    }
                                  </DetailInfo>
                                )}

                              {displayData.sections.education.content.dates &&
                                displayData.sections.education.content.dates[
                                  index
                                ] && (
                                  <DetailInfo>
                                    <strong>Year:</strong>{" "}
                                    {
                                      displayData.sections.education.content
                                        .dates[index]
                                    }
                                  </DetailInfo>
                                )}

                              {/* CGPA/GPA Display - Always show with value or "Not present" */}
                              {(() => {
                                const educationContent =
                                  displayData.sections.education.content;
                                const ruleBasedFindings =
                                  analysisData?.fullAnalysis?.rule_based_findings ||
                                  analysisData?.rule_based_findings;

                                // First check education content for CGPA/GPA
                                let cgpaValue =
                                  educationContent.cgpa?.[index] ||
                                  educationContent.gpa?.[index] ||
                                  educationContent.grades?.[index] ||
                                  educationContent.grade?.[index] ||
                                  educationContent.cgpas?.[index] ||
                                  educationContent.gpas?.[index];

                                // If not found in education content, check rule-based findings
                                if (
                                  !cgpaValue &&
                                  ruleBasedFindings?.cgpa_analysis?.cgpa_present
                                ) {
                                  const cgpaValues =
                                    ruleBasedFindings.cgpa_analysis.cgpa_values;
                                  const scale =
                                    ruleBasedFindings.cgpa_analysis.scale;
                                  if (cgpaValues && cgpaValues[index]) {
                                    cgpaValue = `${cgpaValues[index]}${
                                      scale !== "unknown" ? `/${scale}` : ""
                                    }`;
                                  } else if (
                                    cgpaValues &&
                                    cgpaValues.length > 0 &&
                                    index === 0
                                  ) {
                                    // Show first CGPA for first education if available
                                    cgpaValue = `${cgpaValues[0]}${
                                      scale !== "unknown" ? `/${scale}` : ""
                                    }`;
                                  }
                                }

                                // Always show CGPA field
                                return (
                                  <DetailInfo>
                                    <strong>CGPA/GPA:</strong>
                                    <span
                                      className={
                                        cgpaValue
                                          ? "value-present"
                                          : "value-missing"
                                      }
                                    >
                                      {cgpaValue || "Not present"}
                                    </span>
                                  </DetailInfo>
                                );
                              })()}

                              {displayData.sections.education.content
                                .specializations &&
                                displayData.sections.education.content
                                  .specializations[index] && (
                                  <DetailInfo>
                                    <strong>Specialization:</strong>{" "}
                                    {
                                      displayData.sections.education.content
                                        .specializations[index]
                                    }
                                  </DetailInfo>
                                )}
                            </EducationDetailsItem>
                          </EducationItem>
                        )
                      )}
                    </EducationList>
                  ) : (
                    <NoContent>
                      <p>Education details not available for this resume.</p>
                      <p><small>Education Level: {displayData.sections.education.content.education_level || "Not specified"}</small></p>
                      <p><small>CGPA Found: {displayData.sections.education.content.cgpa_present ? "Yes" : "No"}</small></p>
                      {displayData.sections.education.content.cgpa_value && (
                        <p><small>CGPA Value: {displayData.sections.education.content.cgpa_value}</small></p>
                      )}
                    </NoContent>
                  )}
                </ContentDisplay>

                <SuggestionsBox>
                  <h5>
                    <i className="bi bi-lightbulb"></i> Suggestions:
                  </h5>
                  <p>{displayData.sections.education.suggestions}</p>
                </SuggestionsBox>
              </SectionContent>
            )}

            {activeTab === "projects" && (
              <SectionContent>
                <SectionHeader>
                  <h4>
                    <i className="bi bi-rocket-takeoff"></i>
                    Project Portfolio
                  </h4>
                  <SectionScore>
                    Score: {displayData.sections.projects.score}/100
                  </SectionScore>
                </SectionHeader>

                <ContentDisplay>
                  {displayData.sections.projects.content.project_names &&
                  displayData.sections.projects.content.project_names.length >
                    0 ? (
                    <ProjectsList>
                      {displayData.sections.projects.content.project_names.map(
                        (projectName, index) => (
                          <ProjectItem key={index}>
                            <ProjectName>
                              <strong>{projectName}</strong>
                            </ProjectName>
                            {displayData.sections.projects.content
                              .descriptions &&
                              displayData.sections.projects.content
                                .descriptions[index] && (
                                <ProjectDescription>
                                  {
                                    displayData.sections.projects.content
                                      .descriptions[index]
                                  }
                                </ProjectDescription>
                              )}
                          </ProjectItem>
                        )
                      )}
                    </ProjectsList>
                  ) : (
                    <NoContent>No projects extracted</NoContent>
                  )}
                </ContentDisplay>

                <SuggestionsBox>
                  <h5>
                    <i className="bi bi-lightbulb"></i> Suggestions:
                  </h5>
                  <p>{displayData.sections.projects.suggestions}</p>
                </SuggestionsBox>
              </SectionContent>
            )}

            {activeTab === "certifications" && (
              <SectionContent>
                <SectionHeader>
                  <h4>
                    <i className="bi bi-award"></i>
                    Certifications
                  </h4>
                  <SectionScore>
                    Score: {displayData.sections.certifications.score}/100
                  </SectionScore>
                </SectionHeader>

                <ContentDisplay>
                  {displayData.sections.certifications.content
                    .certification_names &&
                  displayData.sections.certifications.content
                    .certification_names.length > 0 ? (
                    <ProjectsList>
                      {displayData.sections.certifications.content.certification_names.map(
                        (certName, index) => (
                          <CertActivityItem key={index}>
                            <CertActivityName>{certName}</CertActivityName>
                            {displayData.sections.certifications.content
                              .issuing_organizations &&
                              displayData.sections.certifications.content
                                .issuing_organizations[index] && (
                                <CertActivityDetail>
                                  Issued by:{" "}
                                  {
                                    displayData.sections.certifications.content
                                      .issuing_organizations[index]
                                  }
                                </CertActivityDetail>
                              )}
                            {displayData.sections.certifications.content
                              .dates &&
                              displayData.sections.certifications.content.dates[
                                index
                              ] && (
                                <CertActivityDetail>
                                  Date:{" "}
                                  {
                                    displayData.sections.certifications.content
                                      .dates[index]
                                  }
                                </CertActivityDetail>
                              )}
                          </CertActivityItem>
                        )
                      )}
                    </ProjectsList>
                  ) : (
                    <NoContent>
                      No certifications extracted
                    </NoContent>
                  )}
                </ContentDisplay>

                <SuggestionsBox>
                  <h5>
                    <i className="bi bi-lightbulb"></i> Suggestions:
                  </h5>
                  <p>{displayData.sections.certifications.suggestions}</p>
                </SuggestionsBox>
              </SectionContent>
            )}

            {activeTab === "extracurriculars" && (
              <SectionContent>
                <SectionHeader>
                  <h4>
                    <i className="bi bi-trophy"></i>
                    Extracurricular Activities
                  </h4>
                  <SectionScore>
                    Score: {displayData.sections.extracurriculars.score}/100
                  </SectionScore>
                </SectionHeader>

                <ContentDisplay>
                  {displayData.sections.extracurriculars.content.activities &&
                  displayData.sections.extracurriculars.content.activities
                    .length > 0 ? (
                    <ProjectsList>
                      {displayData.sections.extracurriculars.content.activities.map(
                        (activity, index) => (
                          <CertActivityItem key={index}>
                            <CertActivityName>{activity}</CertActivityName>
                            {displayData.sections.extracurriculars.content
                              .roles &&
                              displayData.sections.extracurriculars.content
                                .roles[index] && (
                                <CertActivityDetail>
                                  Role:{" "}
                                  {
                                    displayData.sections.extracurriculars
                                      .content.roles[index]
                                  }
                                </CertActivityDetail>
                              )}
                            {displayData.sections.extracurriculars.content
                              .durations &&
                              displayData.sections.extracurriculars.content
                                .durations[index] && (
                                <CertActivityDetail>
                                  Duration:{" "}
                                  {
                                    displayData.sections.extracurriculars
                                      .content.durations[index]
                                  }
                                </CertActivityDetail>
                              )}
                          </CertActivityItem>
                        )
                      )}
                    </ProjectsList>
                  ) : (
                    <NoContent>
                      No extracurricular activities extracted
                    </NoContent>
                  )}
                </ContentDisplay>

                <SuggestionsBox>
                  <h5>
                    <i className="bi bi-lightbulb"></i> Suggestions:
                  </h5>
                  <p>{displayData.sections.extracurriculars.suggestions}</p>
                </SuggestionsBox>
              </SectionContent>
            )}
          </TabContent>
        </SectionCard>

        {/* Actionable Feedback */}
        <ActionableFeedback>
          <CardHeader>Actionable Feedback</CardHeader>
          <FeedbackGrid>
            <FeedbackSection $variant="strengths">
              <h4>
                <i className="bi bi-check-circle"></i> Strengths
              </h4>
              <ul>
                {displayData.feedback.strengths.map((strength, index) => (
                  <li key={index}>{strength}</li>
                ))}
              </ul>
            </FeedbackSection>

            <FeedbackSection $variant="improvements">
              <h4>
                <i className="bi bi-bullseye"></i>
                Areas for Improvement
              </h4>
              <ul>
                {displayData.feedback.improvements.map((improvement, index) => (
                  <li key={index}>{improvement}</li>
                ))}
              </ul>
            </FeedbackSection>

            <FeedbackSection $variant="recommendations">
              <h4>
                <i className="bi bi-lightbulb"></i> Recommendations
              </h4>
              <ul>
                {displayData.feedback.recommendations.map(
                  (recommendation, index) => (
                    <li key={index}>{recommendation}</li>
                  )
                )}
              </ul>
            </FeedbackSection>
          </FeedbackGrid>
        </ActionableFeedback>
      </AnalysisMain>
    </AnalysisResultsPageWrapper>
  );
}

export default AnalysisResultsPage;
