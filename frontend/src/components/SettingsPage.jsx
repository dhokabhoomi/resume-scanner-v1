import React, { useState, useEffect } from "react";
import { DEFAULT_PRIORITIES, SETTINGS_PRIORITIES } from "../constants/priorities";
import "./SettingsPage.css";

function SettingsPage() {
  // State for all settings
  const [settings, setSettings] = useState({
    defaultPriorities: DEFAULT_PRIORITIES,
  });

  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Available priorities for drag-and-drop
  const availablePriorities = SETTINGS_PRIORITIES;

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem("resumeAnalyzerSettings");
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }
  }, []);

  // Mark as having unsaved changes when settings change
  const updateSettings = (newSettings) => {
    setSettings(newSettings);
    setHasUnsavedChanges(true);
  };

  const handleSaveSettings = () => {
    localStorage.setItem("resumeAnalyzerSettings", JSON.stringify(settings));
    setHasUnsavedChanges(false);
    alert("Settings saved successfully!");
  };

  const handleResetToDefaults = () => {
    const defaultSettings = {
      defaultPriorities: DEFAULT_PRIORITIES,
    };
    setSettings(defaultSettings);
    setHasUnsavedChanges(true);
  };

  return (
    <div className="settings-page">
      <div className="settings-page-header">
        <h1 className="settings-title">Settings</h1>
        <div className="settings-actions">
          <button
            className="reset-btn"
            onClick={handleResetToDefaults}
            title="Reset to default settings"
          >
            Reset Defaults
          </button>
          <button
            className={`save-btn ${hasUnsavedChanges ? "has-changes" : ""}`}
            onClick={handleSaveSettings}
          >
            {hasUnsavedChanges ? <><i className="bi bi-floppy"></i> Save Changes</> : <><i className="bi bi-check-circle"></i> Saved</>}
          </button>
        </div>
      </div>

      <div className="settings-content">
        {/* Default Priorities Section */}
        <section className="settings-section">
          <div className="section-header">
            <h2>
              <i className="bi bi-bullseye"></i>
              Default Priorities
            </h2>
            <p>
              Set default analysis priorities for all new analyses with
              drag-and-drop ordering
            </p>
          </div>
          <div className="section-content">
            <DefaultPrioritiesManager
              priorities={settings.defaultPriorities}
              availablePriorities={availablePriorities}
              onUpdate={(newPriorities) =>
                updateSettings({
                  ...settings,
                  defaultPriorities: newPriorities,
                })
              }
            />
          </div>
        </section>


      </div>
    </div>
  );
}

// Default Priorities Manager Component
function DefaultPrioritiesManager({
  priorities,
  availablePriorities,
  onUpdate,
}) {
  const [draggedItem, setDraggedItem] = useState(null);

  const handleDragStart = (e, priority) => {
    setDraggedItem(priority);
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  };

  const handleDrop = (e, targetIndex) => {
    e.preventDefault();

    if (!draggedItem) return;

    const currentIndex = priorities.indexOf(draggedItem);
    if (currentIndex === -1) return;

    const newPriorities = [...priorities];
    newPriorities.splice(currentIndex, 1);
    newPriorities.splice(targetIndex, 0, draggedItem);

    onUpdate(newPriorities);
    setDraggedItem(null);
  };

  const addPriority = (priorityLabel) => {
    if (!priorities.includes(priorityLabel)) {
      onUpdate([...priorities, priorityLabel]);
    }
  };

  const removePriority = (priority) => {
    onUpdate(priorities.filter((p) => p !== priority));
  };

  return (
    <div className="priorities-manager">
      <div className="current-priorities">
        <h3>Current Default Priorities (Drag to reorder)</h3>
        <div className="priorities-list">
          {priorities.map((priority, index) => {
            const priorityData = availablePriorities.find(
              (p) => p.label === priority
            );
            return (
              <div
                key={priority}
                className="priority-item"
                draggable
                onDragStart={(e) => handleDragStart(e, priority)}
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, index)}
              >
                <span className="priority-icon">
                  <i className={priorityData?.icon || "bi bi-list-check"}></i>
                </span>
                <span className="priority-label">{priority}</span>
                <span className="priority-order">#{index + 1}</span>
                <button
                  className="remove-priority-btn"
                  onClick={() => removePriority(priority)}
                >
                  ×
                </button>
              </div>
            );
          })}
        </div>
      </div>

      <div className="available-priorities">
        <h3>Available Priorities</h3>
        <div className="available-list">
          {availablePriorities
            .filter((p) => !priorities.includes(p.label))
            .map((priority) => (
              <button
                key={priority.id}
                className="add-priority-btn"
                onClick={() => addPriority(priority.label)}
              >
                {priority.icon} {priority.label}
              </button>
            ))}
        </div>
      </div>
    </div>
  );
}




export default SettingsPage;
