import React, { useState } from 'react';

function DashboardLayout() {
  const [selectedPriorities, setSelectedPriorities] = useState([]);
  const [isDragging, setIsDragging] = useState(false);

  const priorities = [
    { id: 'technical', label: 'Technical Skills', icon: 'bi bi-cpu' },
    { id: 'education', label: 'Education', icon: 'bi bi-mortarboard' },
    { id: 'experience', label: 'Experience', icon: 'bi bi-briefcase' },
    { id: 'projects', label: 'Projects', icon: 'bi bi-rocket-takeoff' },
    { id: 'certifications', label: 'Certifications', icon: 'bi bi-award' }
  ];

  const recentAnalyses = [
    { id: 1, name: 'Sarah Johnson', score: 92, date: '2024-01-15', position: 'Software Engineer' },
    { id: 2, name: 'Mike Chen', score: 88, date: '2024-01-14', position: 'Data Scientist' },
    { id: 3, name: 'Lisa Rodriguez', score: 85, date: '2024-01-13', position: 'Frontend Developer' }
  ];

  const handlePriorityToggle = (priorityId) => {
    setSelectedPriorities(prev => 
      prev.includes(priorityId) 
        ? prev.filter(id => id !== priorityId)
        : [...prev, priorityId]
    );
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const getScoreColor = (score) => {
    if (score >= 90) return '#059669'; // green - excellent
    if (score >= 80) return '#2563eb'; // blue - good
    if (score >= 70) return '#d97706'; // amber - average
    return '#dc2626'; // red - poor
  };

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <div className="logo-section">
            <div className="logo-icon">
              <i className="bi bi-graph-up"></i>
            </div>
            <h1 className="site-title">Resume Analyzer</h1>
          </div>
          <nav className="header-nav">
            <button className="nav-item active">Dashboard</button>
            <button className="nav-item">Settings</button>
            <button className="nav-item">Help</button>
          </nav>
        </div>
        <div className="header-right">
          <div className="user-profile">
            <div className="user-avatar">👤</div>
            <span className="user-name">User Profile</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="dashboard-main">
        {/* Hero Section */}
        <section className="hero-section">
          <h2 className="hero-title">Analyze Resumes with AI Precision</h2>
          <p className="hero-subtitle">
            Upload resumes and get detailed analysis with actionable insights to improve candidate evaluation
          </p>

          {/* Upload Zone */}
          <div 
            className={`upload-zone ${isDragging ? 'dragging' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="upload-content">
              <div className="upload-icon">
                <i className="bi bi-folder2-open"></i>
              </div>
              <h3 className="upload-title">Drag & drop area with upload icon</h3>
              <p className="upload-formats">Supported formats: PDF, DOCX, TXT</p>
              <button className="browse-button">Browse files</button>
              <input 
                type="file" 
                multiple 
                accept=".pdf,.docx,.txt"
                style={{ display: 'none' }}
              />
            </div>
          </div>

          {/* Priority Selection */}
          <div className="priority-section">
            <h3 className="priority-title">Select Analysis Priorities</h3>
            <p className="priority-subtitle">Drag to reorder priorities (1, 2, 3)</p>
            <div className="priority-grid">
              {priorities.map((priority) => (
                <label key={priority.id} className="priority-item">
                  <input
                    type="checkbox"
                    checked={selectedPriorities.includes(priority.id)}
                    onChange={() => handlePriorityToggle(priority.id)}
                  />
                  <div className="priority-content">
                    <span className="priority-icon">{priority.icon}</span>
                    <span className="priority-label">{priority.label}</span>
                    {selectedPriorities.includes(priority.id) && (
                      <span className="priority-order">
                        {selectedPriorities.indexOf(priority.id) + 1}
                      </span>
                    )}
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Recent Analyses */}
          <div className="recent-analyses">
            <h3 className="recent-title">Recent Analyses</h3>
            <div className="analyses-grid">
              {recentAnalyses.map((analysis) => (
                <div key={analysis.id} className="analysis-card">
                  <div className="card-header">
                    <div className="candidate-info">
                      <h4 className="candidate-name">{analysis.name}</h4>
                      <p className="candidate-position">{analysis.position}</p>
                    </div>
                    <div className="score-badge" style={{ color: getScoreColor(analysis.score) }}>
                      {analysis.score}
                    </div>
                  </div>
                  <div className="card-footer">
                    <span className="analysis-date">{analysis.date}</span>
                    <button className="view-btn">View Details</button>
                  </div>
                </div>
              ))}
            </div>
            <button className="view-all-btn">View All Analyses</button>
          </div>
        </section>
      </main>
    </div>
  );
}

export default DashboardLayout;