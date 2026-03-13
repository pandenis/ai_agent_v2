interface ModelsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ModelsModal({ isOpen, onClose }: ModelsModalProps) {
  if (!isOpen) return null;

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
        <div className="flex-1 p-6 text-slate-400">
          Model list coming soon...
        </div>
      </div>
    </div>
  );
}
