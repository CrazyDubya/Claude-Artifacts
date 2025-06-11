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
    this.containerRef.current.innerHTML = '';
    this.containerRef.current.appendChild(container);

    try {
      // Dynamically load required React version
      const ReactModule = await import(
        `https://cdn.jsdelivr.net/npm/react@${reactVersion}/umd/react.production.min.js`
      );
      const ReactDOMModule = await import(
        `https://cdn.jsdelivr.net/npm/react-dom@${reactVersion}/umd/react-dom.production.min.js`
      );

      // Create new root with specific React version
      this.root = ReactDOMModule.createRoot(container);
      this.root.render(
        <Suspense fallback={<div>Loading environment...</div>}>
          <Component />
        </Suspense>
      );
    } catch (error) {
      console.error(`Failed to setup React ${reactVersion} environment:`, error);
      container.innerHTML = `
        <div class="text-red-500">
          Failed to load React ${reactVersion} environment.
          Error: ${error.message}
        </div>
      `;
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
