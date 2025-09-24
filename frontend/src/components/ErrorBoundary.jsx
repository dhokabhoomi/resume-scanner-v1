import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Uncaught error:", error, errorInfo);
    console.error("Error stack:", error.stack);
    console.error("Component stack:", errorInfo.componentStack);
    console.error("Error details:", {
      message: error.message,
      name: error.name,
      fileName: error.fileName,
      lineNumber: error.lineNumber,
      columnNumber: error.columnNumber
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <h1>Something went wrong.</h1>
          <p>Check the browser console for details.</p>
          <div style={{ marginTop: '1rem' }}>
            <button onClick={() => window.location.reload()} style={{
              padding: '0.5rem 1rem',
              marginRight: '0.5rem',
              cursor: 'pointer'
            }}>
              Reload Page
            </button>
            <button onClick={() => window.location.href = '/'} style={{
              padding: '0.5rem 1rem',
              cursor: 'pointer'
            }}>
              Go to Dashboard
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
