import React, { createContext, useContext } from "react";
import { useNavigate } from "react-router-dom";

const NavigationContext = createContext();

const useNavigation = () => {
  const context = useContext(NavigationContext);
  if (!context) {
    throw new Error("useNavigation must be used within a NavigationProvider");
  }
  return context;
};

const NavigationProvider = ({ children }) => {
  const navigate = useNavigate();

  // Navigation helper functions
  const goToDashboard = () => {
    navigate('/');
  };

  const goToHistory = () => {
    navigate('/history');
  };

  const goToAnalysis = (id) => {
    navigate(`/analysis/${id}`);
  };

  const goToSettings = () => {
    navigate('/settings');
  };

  const contextValue = {
    // Navigation functions
    goToDashboard,
    goToHistory,
    goToAnalysis,
    goToSettings,
  };

  return (
    <NavigationContext.Provider value={contextValue}>
      {children}
    </NavigationContext.Provider>
  );
};

export { useNavigation, NavigationProvider };