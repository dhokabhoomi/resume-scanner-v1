import React from 'react';
import SettingsPage from '../components/SettingsPage';
import { useNavigation } from '../contexts/NavigationContext';

const SettingsPageWrapper = () => {
  const { goToDashboard } = useNavigation();

  const handleBackToDashboard = () => {
    goToDashboard();
  };

  return (
    <div className="settings-page-wrapper">
      <SettingsPage onBackToDashboard={handleBackToDashboard} />
    </div>
  );
};

export default SettingsPageWrapper;