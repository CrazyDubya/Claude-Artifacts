// src/components/ArtifactLoader.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import DependencyAnalyzer from './DependencyAnalyzer';
import ErrorBoundary from './ErrorBoundary';
import { ArtifactValidator } from '../services/artifactValidator';

const ArtifactLoader = () => {
  const [artifacts, setArtifacts] = useState([]);
  const [selectedArtifact, setSelectedArtifact] = useState(null);
  const [errors, setErrors] = useState({});  // Track errors per artifact
  const [isLoading, setIsLoading] = useState(false);
  const [validationResults, setValidationResults] = useState({});

  const loadArtifacts = useCallback(async () => {
    setIsLoading(true);
    try {
      const artifactFiles = import.meta.glob('../claude_artifacts/*.jsx');
      const artifactRawFiles = import.meta.glob('../claude_artifacts/*.jsx', { as: 'raw' });
      const artifactList = [];
      const newErrors = {};
      const newValidationResults = {};

      // Process each artifact file
      for (const path in artifactFiles) {
        const id = path.split('/').pop().replace('.jsx', '');
        const name = id
          .split('-')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ');

        try {
          // Load raw content for validation
          const rawContent = await artifactRawFiles[path]();
          
          // Validate artifact security and structure
          const validation = ArtifactValidator.validate(rawContent, id);
          newValidationResults[id] = validation;

          if (!validation.isValid) {
            newErrors[id] = `Security validation failed: ${validation.securityIssues[0]?.message || validation.errors[0]?.message}`;
          }

          artifactList.push({
            id,
            name,
            path,
            loader: artifactFiles[path],
            validation
          });
        } catch (err) {
          console.error(`Error processing artifact ${id}:`, err);
          newErrors[id] = `Failed to process: ${err.message}`;
        }
      }

      setArtifacts(artifactList);
      setErrors(newErrors);
      setValidationResults(newValidationResults);
    } catch (err) {
      console.error('Failed to scan artifacts:', err);
      setErrors(prev => ({
        ...prev,
        global: 'Failed to scan artifacts directory'
      }));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadArtifacts();
  }, [loadArtifacts]);

  const handleSelectArtifact = useCallback(async (artifactId) => {
    try {
      const artifact = artifacts.find(a => a.id === artifactId);
      if (!artifact) throw new Error(`Artifact ${artifactId} not found`);

      // Check validation results before loading
      const validation = validationResults[artifactId];
      if (validation && !validation.isValid) {
        throw new Error(`Security validation failed: ${validation.securityIssues[0]?.message || 'Invalid artifact'}`);
      }

      // Validate component before loading
      const module = await artifact.loader();
      
      if (!module.default) {
        throw new Error('Artifact must export a default React component');
      }

      if (typeof module.default !== 'function') {
        throw new Error('Default export must be a React component function');
      }

      setSelectedArtifact({
        ...artifact,
        Component: module.default
      });

      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[artifactId];
        return newErrors;
      });

    } catch (err) {
      console.error(`Error loading artifact ${artifactId}:`, err);
      setErrors(prev => ({
        ...prev,
        [artifactId]: `Failed to load: ${err.message}`
      }));
    }
  }, [artifacts, validationResults]);

  // Memoize error reporting function
  const handleErrorReport = useCallback((error, errorInfo) => {
    console.error('Artifact error reported:', { error, errorInfo });
    // Here you could send to an error reporting service
  }, []);

  return (
    <div className="container mx-auto p-4">
      <ErrorBoundary title="Dependency Analyzer Error" onReport={handleErrorReport}>
        <DependencyAnalyzer />
      </ErrorBoundary>

      {/* Global Errors */}
      {errors.global && (
        <Card className="mb-6 bg-destructive/10">
          <CardContent className="p-4">
            <p className="text-destructive">{errors.global}</p>
          </CardContent>
        </Card>
      )}

      {/* Artifact Selection */}
      <Card className="mb-6">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Available Artifacts</CardTitle>
          <Button 
            variant="outline" 
            onClick={loadArtifacts}
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : 'Refresh List'}
          </Button>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {artifacts.map((artifact) => {
              const validation = validationResults[artifact.id];
              const hasSecurityIssues = validation?.securityIssues?.length > 0;
              const hasWarnings = validation?.warnings?.length > 0;
              
              return (
                <div key={artifact.id} className="flex flex-col items-start">
                  <div className="flex items-center gap-2">
                    <Button
                      variant={selectedArtifact?.id === artifact.id ? "default" : "outline"}
                      onClick={() => handleSelectArtifact(artifact.id)}
                      disabled={isLoading || !validation?.isValid}
                      className={hasSecurityIssues ? "border-destructive" : hasWarnings ? "border-amber-500" : ""}
                    >
                      {artifact.name}
                    </Button>
                    {validation && (
                      <div className="flex gap-1">
                        {validation.isValid ? (
                          <span className="text-green-500 text-sm">✅</span>
                        ) : (
                          <span className="text-red-500 text-sm">❌</span>
                        )}
                        {hasWarnings && (
                          <span className="text-amber-500 text-sm">⚠️</span>
                        )}
                      </div>
                    )}
                  </div>
                  
                  {errors[artifact.id] && (
                    <p className="text-sm text-destructive mt-1">
                      {errors[artifact.id]}
                    </p>
                  )}
                  
                  {validation && !validation.isValid && (
                    <div className="text-xs text-muted-foreground mt-1 max-w-xs">
                      {validation.securityIssues.slice(0, 2).map((issue, idx) => (
                        <div key={idx} className="text-red-600">
                          Security: {issue.message}
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {validation && validation.warnings.length > 0 && (
                    <div className="text-xs text-amber-600 mt-1">
                      {validation.warnings.length} warning(s)
                    </div>
                  )}
                </div>
              );
            })}
            {artifacts.length === 0 && !isLoading && (
              <p className="text-muted-foreground">
                No artifacts found. Place .jsx files in the claude_artifacts directory.
              </p>
            )}
            {isLoading && (
              <p className="text-muted-foreground">
                Loading artifacts...
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Selected Artifact */}
      {selectedArtifact?.Component && (
        <Card>
          <CardContent className="p-4">
            <ErrorBoundary 
              title={`Error in ${selectedArtifact.name}`}
              message="This artifact encountered an error while rendering."
              onReport={handleErrorReport}
            >
              <selectedArtifact.Component />
            </ErrorBoundary>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ArtifactLoader;