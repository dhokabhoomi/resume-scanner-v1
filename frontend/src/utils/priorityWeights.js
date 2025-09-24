// Utility functions for calculating scoring weights based on priority order

/**
 * Calculate scoring weights based on priority order
 * Higher priority (lower index) gets higher weight
 * @param {Array} priorities - Array of priority labels in order of importance
 * @returns {Object} - Object mapping priority labels to weight percentages
 */
export function calculatePriorityWeights(priorities) {
  if (!priorities || priorities.length === 0) {
    return {};
  }

  const totalPriorities = priorities.length;
  const weights = {};
  let totalWeight = 0;

  // Calculate weights using a descending scale
  // First priority gets highest weight, subsequent priorities get progressively less
  for (let i = 0; i < totalPriorities; i++) {
    const priority = priorities[i];
    // Weight formula: (totalPriorities - index) / sum of (1 to totalPriorities) * 100
    // This ensures weights add up to 100% and decrease in order
    const weight = Math.round(((totalPriorities - i) / sumOfIntegers(totalPriorities)) * 100);
    weights[priority] = weight;
    totalWeight += weight;
  }

  // Adjust for rounding errors to ensure total is exactly 100
  if (totalWeight !== 100 && priorities.length > 0) {
    const difference = 100 - totalWeight;
    weights[priorities[0]] += difference; // Add/subtract difference to first priority
  }

  return weights;
}

/**
 * Helper function to calculate sum of integers from 1 to n
 * @param {number} n - The upper limit
 * @returns {number} - Sum of 1 + 2 + ... + n
 */
function sumOfIntegers(n) {
  return (n * (n + 1)) / 2;
}

/**
 * Map priority labels to backend scoring categories
 * @param {Object} priorityWeights - Weights mapped by priority labels
 * @returns {Object} - Weights mapped by backend category names
 */
export function mapPriorityWeightsToScoringCategories(priorityWeights) {
  const categoryMapping = {
    "Technical Skills": "skills",
    "Work Experience": "experience",
    "Academic Performance": "education",
    "Project Experience": "projects",
    "Resume Formatting": "formatting",
    "Certifications": "certifications",
    "Skill Diversity": "diversity",
    "Extracurricular Activities": "extracurriculars",
    "CGPA Scores": "cgpa"
  };

  const scoringWeights = {
    skills: 0,
    experience: 0,
    education: 0,
    projects: 0,
    formatting: 0,
    certifications: 0,
    diversity: 0,
    extracurriculars: 0,
    cgpa: 0
  };

  // Map priority weights to scoring categories
  Object.entries(priorityWeights).forEach(([priority, weight]) => {
    const category = categoryMapping[priority];
    if (category && Object.prototype.hasOwnProperty.call(scoringWeights, category)) {
      // Add weights if multiple priorities map to the same category (instead of overwriting)
      scoringWeights[category] += weight;
    }
  });

  // If no priorities mapped to a category, distribute remaining weight evenly
  const totalMapped = Object.values(scoringWeights).reduce((sum, weight) => sum + weight, 0);
  if (totalMapped < 100) {
    const remaining = 100 - totalMapped;
    const unmappedCategories = Object.keys(scoringWeights).filter(cat => scoringWeights[cat] === 0);

    if (unmappedCategories.length > 0) {
      const weightPerCategory = Math.floor(remaining / unmappedCategories.length);
      unmappedCategories.forEach((category, index) => {
        scoringWeights[category] = weightPerCategory;
        // Add any remaining due to rounding to the last category
        if (index === unmappedCategories.length - 1) {
          scoringWeights[category] += remaining - (weightPerCategory * unmappedCategories.length);
        }
      });
    }
  }

  return scoringWeights;
}

/**
 * Get scoring weights for the current settings
 * @returns {Object} - Current scoring weights based on saved priorities
 */
export function getCurrentScoringWeights() {
  try {
    const savedSettings = localStorage.getItem("resumeAnalyzerSettings");
    if (savedSettings) {
      const settings = JSON.parse(savedSettings);
      const priorities = settings.defaultPriorities || [];
      const priorityWeights = calculatePriorityWeights(priorities);
      return mapPriorityWeightsToScoringCategories(priorityWeights);
    }
  } catch (error) {
    console.error("Error getting current scoring weights:", error);
  }

  // Fallback to equal weights if no settings found
  return {
    skills: 15,
    experience: 15,
    education: 15,
    projects: 15,
    formatting: 10,
    certifications: 10,
    diversity: 10,
    extracurriculars: 10,
    cgpa: 0
  };
}