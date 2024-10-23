// src/components/DependencyAnalyzer.jsx
import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const DependencyAnalyzer = () => {
  const [analysis, setAnalysis] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const analyzeFileContent = (content) => {
    // Core feature detection
    const features = {
      hooks: {
        useState: content.includes('useState'),
        useEffect: content.includes('useEffect'),
        useContext: content.includes('useContext'),
        useRef: content.includes('useRef'),
        useMemo: content.includes('useMemo'),
        useCallback: content.includes('useCallback'),
        useTransition: content.includes('useTransition'),
        useDeferredValue: content.includes('useDeferredValue')
      },
      components: new Set(),
      imports: new Set(),
      reactFeatures: new Set()
    };

    // Analyze imports
    const importRegex = /import\s+{([^}]+)}\s+from\s+['"]([^'"]+)['"]/g;
    let match;

    while ((match = importRegex.exec(content))) {
      const [, imports, path] = match;

      // Clean and split imports
      const importList = imports.split(',').map(i => i.trim());

      if (path.startsWith('@/components/ui/')) {
        importList.forEach(i => features.components.add(i));
      } else if (!path.startsWith('./') && !path.startsWith('../')) {
        importList.forEach(i => features.imports.add(path));
      }

      // Detect React features
      if (path === 'react') {
        importList.forEach(i => features.reactFeatures.add(i));
      }
    }

    // Determine React version requirements
    let requiredReactVersion = '16.8.0'; // Base for hooks
    if (features.hooks.useTransition || features.hooks.useDeferredValue) {
      requiredReactVersion = '18.0.0';
    }

    return {
      components: Array.from(features.components),
      externalDependencies: Array.from(features.imports),
      reactFeatures: Array.from(features.reactFeatures),
      requiredReactVersion,
      hooks: Object.entries(features.hooks)
        .filter(([, used]) => used)
        .map(([hook]) => hook)
    };
  };

  const analyzeArtifacts = async () => {
    setIsAnalyzing(true);
    try {
      const artifactFiles = import.meta.glob('../claude_artifacts/*.jsx', { as: 'raw' });

      const results = {
        artifactsChecked: [],
        requiredComponents: new Set(),
        externalDependencies: new Set(),
        reactRequirements: new Map(),
        report: []
      };

      for (const [path, loadContent] of Object.entries(artifactFiles)) {
        try {
          const content = await loadContent();
          const fileName = path.split('/').pop();
          results.artifactsChecked.push(fileName);

          const analysis = analyzeFileContent(content);

          // Track all requirements
          analysis.components.forEach(c => results.requiredComponents.add(c));
          analysis.externalDependencies.forEach(d => results.externalDependencies.add(d));
          results.reactRequirements.set(fileName, {
            version: analysis.requiredReactVersion,
            features: analysis.reactFeatures,
            hooks: analysis.hooks
          });

          // Add to detailed report
          results.report.push({
            file: fileName,
            components: analysis.components,
            dependencies: analysis.externalDependencies,
            react: {
              version: analysis.requiredReactVersion,
              features: analysis.reactFeatures,
              hooks: analysis.hooks
            }
          });
        } catch (err) {
          console.warn(`Error analyzing ${path}:`, err);
          results.report.push({
            file: path.split('/').pop(),
            error: err.message
          });
        }
      }

      // Determine highest React version needed
      const maxReactVersion = Array.from(results.reactRequirements.values())
        .reduce((max, curr) => {
          const [maxMajor] = max.version.split('.');
          const [currMajor] = curr.version.split('.');
          return parseInt(currMajor) > parseInt(maxMajor) ? curr : max;
        });

      setAnalysis({
        ...results,
        maxReactVersion,
        requiredComponents: Array.from(results.requiredComponents),
        externalDependencies: Array.from(results.externalDependencies)
      });
    } catch (error) {
      console.error('Analysis failed:', error);
      setAnalysis({
        error: 'Analysis encountered some issues',
        details: error.message
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <Card className="mb-6">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Dependency Analyzer</CardTitle>
        <Button
          onClick={analyzeArtifacts}
          disabled={isAnalyzing}
        >
          {isAnalyzing ? 'Analyzing...' : 'Analyze Artifacts'}
        </Button>
      </CardHeader>
      <CardContent>
        {analysis && !analysis.error && (
          <div className="space-y-6">
            {/* Artifacts Checked */}
            <div>
              <h3 className="font-semibold mb-2">Artifacts Checked:</h3>
              <ul className="list-disc pl-5">
                {analysis.artifactsChecked.map(file => (
                  <li key={file}>{file}</li>
                ))}
              </ul>
            </div>

            {/* Required UI Components */}
            {analysis.requiredComponents.length > 0 && (
              <div>
                <h3 className="font-semibold mb-2">Required UI Components:</h3>
                <ul className="list-disc pl-5">
                  {analysis.requiredComponents.map(comp => (
                    <li key={comp}>{comp}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* External Dependencies */}
            {analysis.externalDependencies.length > 0 && (
              <div>
                <h3 className="font-semibold mb-2 text-amber-600">Required External Packages:</h3>
                <div className="bg-amber-50 border border-amber-200 rounded p-4">
                  <code className="block bg-black text-white p-2 rounded">
                    npm install {analysis.externalDependencies.join(' ')}
                  </code>
                </div>
              </div>
            )}

            {/* React Requirements */}
            <div>
              <h3 className="font-semibold mb-2">React Requirements:</h3>
              <div className="space-y-2">
                <p><span className="font-medium">Minimum React Version: </span>
                  {analysis.maxReactVersion.version}
                </p>
              </div>
            </div>

            {/* Detailed Report */}
            <div>
              <h3 className="font-semibold mb-2">Detailed Report:</h3>
              {analysis.report.map((item) => (
                <div key={item.file} className="mb-4">
                  <h4 className="font-medium">{item.file}:</h4>
                  {item.error ? (
                    <p className="text-red-500 pl-5">{item.error}</p>
                  ) : (
                    <div className="pl-5 space-y-2">
                      {item.react && (
                        <>
                          <p>React Version: {item.react.version}</p>
                          {item.react.hooks.length > 0 && (
                            <p>Hooks: {item.react.hooks.join(', ')}</p>
                          )}
                        </>
                      )}
                      {item.components.length > 0 && (
                        <p>UI Components: {item.components.join(', ')}</p>
                      )}
                      {item.dependencies.length > 0 && (
                        <p>External Dependencies: {item.dependencies.join(', ')}</p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {analysis?.error && (
          <div className="text-amber-600">
            <p>{analysis.error}</p>
            {analysis.details && (
              <p className="text-sm mt-1">{analysis.details}</p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default DependencyAnalyzer;