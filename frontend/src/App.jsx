// App.js - Clean ATS-Style Interface with Proper Routing
import React from "react";
import { BrowserRouter as Router } from "react-router-dom";
import { ThemeProvider } from "./contexts/ThemeContext";
import { NavigationProvider } from "./contexts/NavigationContext";
import ErrorBoundary from "./components/ErrorBoundary";
import StickyNavigation from "./components/StickyNavigation";
import AppRoutes from "./routes/AppRoutes";
import "./App.css";

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <ThemeProvider>
          <NavigationProvider>
            <div className="app">
              <StickyNavigation />
              <AppRoutes />
            </div>
          </NavigationProvider>
        </ThemeProvider>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
