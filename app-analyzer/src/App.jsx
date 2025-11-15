
import React, { useState, useEffect, lazy, Suspense } from 'react';
import { Card } from './components/ui/card';
import { ArtifactValidator } from './services/artifactValidator.js';

const ArtifactViewer = ({ artifact, onSelect }) => {
  const [validation, setValidation] = useState({ isValidating: true, result: null });

  useEffect(() => {
    if (!artifact) return;

    const validateArtifact = async () => {
      setValidation({ isValidating: true, result: null });
      try {
        // Fetch the source code
        const response = await fetch(`/api/artifact-source?path=${artifact.path}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch source: ${response.statusText}`);
        }
        const sourceCode = await response.text();

        // Validate the source code
        const validationResult = ArtifactValidator.validate(sourceCode, artifact.path);
        setValidation({ isValidating: false, result: validationResult });

      } catch (error) {
        console.error("Validation failed:", error);
        setValidation({
          isValidating: false,
          result: { isValid: false, issues: ["Failed to fetch or validate artifact source."] },
        });
      }
    };

    validateArtifact();
  }, [artifact]);

  if (!artifact) return null;

  const path = `../${artifact.path}`;
  const ArtifactComponent = lazy(() => import(/* @vite-ignore */ path));

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white p-4 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto">
        <h2 className="text-2xl font-bold mb-4">{artifact.name}</h2>

        {validation.isValidating ? (
          <div>Validating artifact...</div>
        ) : validation.result?.isValid ? (
          <Suspense fallback={<div>Loading artifact...</div>}>
            <ArtifactComponent />
          </Suspense>
        ) : (
          <div>
            <h3 className="text-lg font-bold text-red-600">Security Issues Found:</h3>
            <ul className="list-disc list-inside text-red-500">
              {validation.result?.issues.map((issue, index) => (
                <li key={index}>{issue}</li>
              ))}
            </ul>
          </div>
        )}

        <button
          className="mt-4 px-4 py-2 bg-gray-200 rounded"
          onClick={() => onSelect(null)}
        >
          Close
        </button>
      </div>
    </div>
  );
};

function App() {
  const [artifacts, setArtifacts] = useState([]);
  const [selectedArtifact, setSelectedArtifact] = useState(null);

  useEffect(() => {
    const loadArtifacts = async () => {
      try {
        const response = await fetch('/api/artifacts');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setArtifacts(data);
      } catch (error) {
        console.error("Failed to load artifacts:", error);
      }
    };
    loadArtifacts();
  }, []);

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Claude Artifacts</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {artifacts.map((artifact) => (
          <Card
            key={artifact.id}
            className="p-4 cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => setSelectedArtifact(artifact)}
          >
            <h2 className="text-xl font-semibold">{artifact.name}</h2>
            <p className="text-gray-600">{artifact.description || 'No description available.'}</p>
          </Card>
        ))}
      </div>
      <ArtifactViewer artifact={selectedArtifact} onSelect={setSelectedArtifact} />
    </div>
  );
}

export default App;
