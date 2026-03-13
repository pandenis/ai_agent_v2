'use client';

import { useState, useEffect } from 'react';

interface Model {
  name: string;
  size?: number;
  modified_at?: string;
}

interface ModelsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ModelsModal({ isOpen, onClose }: ModelsModalProps) {
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    setError(null);
    fetch('/api/v1/models')
      .then((res) => res.json())
      .then((data) => {
        setModels(data.models || []);
        setLoading(false);
      })
      .catch(() => {
        setError('Failed to load models');
        setLoading(false);
      });
  }, [isOpen]);

  if (!isOpen) return null;

  const displayName = (name: string) => name.replace(/:latest$/, '');

  return (
    <div
      className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center"
      onClick={onClose}
    >
      <div
        className="bg-slate-800 rounded-lg flex flex-col"
        style={{ width: '80vw', height: '85vh' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-white">🤖 Model Manager</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-xl leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left panel */}
          <div className="w-1/3 border-r border-slate-700 overflow-y-auto">
            {loading && (
              <div className="p-4 text-slate-400">Loading...</div>
            )}
            {error && (
              <div className="p-4 text-red-400">{error}</div>
            )}
            {!loading && !error && models.length === 0 && (
              <div className="p-4 text-slate-400">No models found</div>
            )}
            {!loading && !error && models.map((model) => (
              <div
                key={model.name}
                onClick={() => setSelectedModel(model.name)}
                className={`px-4 py-3 cursor-pointer hover:bg-slate-700 ${
                  selectedModel === model.name ? 'bg-slate-600' : ''
                }`}
              >
                {displayName(model.name)}
              </div>
            ))}
          </div>

          {/* Right panel */}
          <div className="flex-1 p-4 text-slate-400">
            {!selectedModel ? (
              <p>Select a model to view its Modelfile</p>
            ) : (
              <h3 className="text-white font-semibold">{selectedModel}</h3>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
