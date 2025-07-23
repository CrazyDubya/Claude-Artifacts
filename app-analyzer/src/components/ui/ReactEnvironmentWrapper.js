// src/components/ReactEnvironmentWrapper.jsx
import React, { Suspense } from 'react';
import { createRoot } from 'react-dom/client';

class ReactEnvironmentWrapper extends React.Component {
  constructor(props) {
    super(props);
    this.containerRef = React.createRef();
    this.root = null;
  }

  componentDidMount() {
    this.setupEnvironment();
  }

  componentDidUpdate(prevProps) {
    if (prevProps.reactVersion !== this.props.reactVersion) {
      this.setupEnvironment();
    }
  }

  componentWillUnmount() {
    if (this.root) {
      this.root.unmount();
    }
  }

  async setupEnvironment() {
    const { reactVersion, component: Component } = this.props;

    // Clean up existing root
    if (this.root) {
      this.root.unmount();
    }

    // Create container for isolated React instance
    const container = document.createElement('div');
    // Security fix: Clear container safely
    while (this.containerRef.current.firstChild) {
      this.containerRef.current.removeChild(this.containerRef.current.firstChild);
    }
    this.containerRef.current.appendChild(container);

    try {
      // Security fix: Use local React instead of CDN
      // This should be handled at build time with proper version management
      console.warn(`React version ${reactVersion} environment requested. Using local React instead for security.`);
      
      // Create new root with local React
      this.root = createRoot(container);
      this.root.render(
        <Suspense fallback={<div>Loading environment...</div>}>
          <Component />
        </Suspense>
      );
    } catch (error) {
      console.error(`Failed to setup React ${reactVersion} environment:`, error);
      // Security fix: Use textContent instead of innerHTML
      const errorDiv = document.createElement('div');
      errorDiv.className = 'text-red-500';
      errorDiv.textContent = `Failed to load React ${reactVersion} environment. Error: ${error.message}`;
      container.appendChild(errorDiv);
    }
  }

  render() {
    return (
      <div
        ref={this.containerRef}
        className="react-environment-container"
      />
    );
  }
}

export default ReactEnvironmentWrapper;