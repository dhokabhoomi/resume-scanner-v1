// Centralized priority constants to avoid duplication

export const DEFAULT_PRIORITIES = [
  "Technical Skills",
  "Work Experience",
  "Academic Performance",
];

export const PRIORITY_MAPPINGS = {
  technical: "Technical Skills",
  education: "Academic Performance",
  experience: "Work Experience",
  projects: "Project Experience",
  certifications: "Certifications",
  formatting: "Resume Formatting",
  cgpa: "CGPA Scores",
  diversity: "Skill Diversity",
  extracurriculars: "Extracurricular Activities",
};

export const AVAILABLE_PRIORITIES = [
  { id: "technical", label: "Technical Skills", icon: "bi bi-cpu" },
  { id: "education", label: "Academic Performance", icon: "bi bi-mortarboard" },
  { id: "experience", label: "Work Experience", icon: "bi bi-briefcase" },
  { id: "projects", label: "Project Experience", icon: "bi bi-rocket-takeoff" },
  { id: "certifications", label: "Certifications", icon: "bi bi-award" },
  { id: "formatting", label: "Resume Formatting", icon: "bi bi-file-earmark-text" },
  { id: "cgpa", label: "CGPA Scores", icon: "bi bi-graph-up" },
  { id: "diversity", label: "Skill Diversity", icon: "bi bi-stars" },
  { id: "extracurriculars", label: "Extracurricular Activities", icon: "bi bi-trophy" },
];

// For settings page
export const SETTINGS_PRIORITIES = [
  { id: "technical", label: "Technical Skills", icon: "bi bi-tools" },
  { id: "experience", label: "Work Experience", icon: "bi bi-briefcase" },
  { id: "education", label: "Academic Performance", icon: "bi bi-mortarboard" },
  { id: "projects", label: "Project Experience", icon: "bi bi-rocket-takeoff" },
  { id: "certifications", label: "Certifications", icon: "bi bi-award" },
  { id: "formatting", label: "Resume Formatting", icon: "bi bi-file-earmark-text" },
  { id: "diversity", label: "Skill Diversity", icon: "bi bi-stars" },
  { id: "extracurriculars", label: "Extracurricular Activities", icon: "bi bi-trophy" },
];