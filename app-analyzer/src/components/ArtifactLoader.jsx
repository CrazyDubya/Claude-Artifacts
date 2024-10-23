// src/components/ArtifactLoader.jsx
import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import DependencyAnalyzer from './DependencyAnalyzer';

const ArtifactLoader = () => {
  const [artifacts, setArtifacts] = useState([]);
  const [selectedArtifact, setSelectedArtifact] = useState(null);
  const [errors, setErrors] = useState({});  // Track errors per artifact

  const loadArtifacts = async () => {
    try {
      const artifactFiles = import.meta.glob('../claude_artifacts/*.jsx');
      const artifactList = [];
      const newErrors = {};

      // Process each artifact file
      for (const path in artifactFiles) {
        const name = path
          .split('/')
          .pop()
          .replace('.jsx', '')
          .split('-')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ');

        const id = path.split('/').pop().replace('.jsx', '');

        artifactList.push({
          id,
          name,
          path,
          loader: artifactFiles[path]
        });
      }

      setArtifacts(artifactList);
      setErrors(newErrors);
    } catch (err) {
      console.error('Failed to scan artifacts:', err);
      setErrors(prev => ({
        ...prev,
        global: 'Failed to scan artifacts directory'
      }));
    }
  };

  useEffect(() => {
    loadArtifacts();
  }, []);

  const handleRefresh = () => {
    loadArtifacts();
  };

  const handleSelectArtifact = async (artifactId) => {
    try {
      const artifact = artifacts.find(a => a.id === artifactId);
      if (!artifact) throw new Error(`Artifact ${artifactId} not found`);

      // Just load the artifact - no environment determination yet
      const module = await artifact.loader();

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
  };

  return (
    <div className="container mx-auto p-4">
      <DependencyAnalyzer />

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
          <Button variant="outline" onClick={handleRefresh}>
            Refresh List
          </Button>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {artifacts.map((artifact) => (
              <div key={artifact.id} className="flex flex-col items-start">
                <Button
                  variant={selectedArtifact?.id === artifact.id ? "default" : "outline"}
                  onClick={() => handleSelectArtifact(artifact.id)}
                >
                  {artifact.name}
                </Button>
                {errors[artifact.id] && (
                  <p className="text-sm text-destructive mt-1">
                    {errors[artifact.id]}
                  </p>
                )}
              </div>
            ))}
            {artifacts.length === 0 && (
              <p className="text-muted-foreground">
                No artifacts found. Place .jsx files in the claude_artifacts directory.
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Selected Artifact */}
      {selectedArtifact?.Component && (
        <Card>
          <CardContent className="p-4">
            <selectedArtifact.Component />
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ArtifactLoader;