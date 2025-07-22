
import React, { useState, useEffect } from 'react';
import { Card } from './components/ui/card';

function App() {
  const [artifacts, setArtifacts] = useState([]);
  const [selectedArtifact, setSelectedArtifact] = useState(null);

  useEffect(() => {
    // Load artifacts from claude_artifacts directory
    const loadArtifacts = async () => {
      const response = await fetch('/api/artifacts');
      const data = await response.json();
      setArtifacts(data);
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
            <p className="text-gray-600">{artifact.description}</p>
          </Card>
        ))}
      </div>
      {selectedArtifact && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white p-4 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto">
            <h2 className="text-2xl font-bold mb-4">{selectedArtifact.name}</h2>
            <div id="artifact-container"></div>
            <button
              className="mt-4 px-4 py-2 bg-gray-200 rounded"
              onClick={() => setSelectedArtifact(null)}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
