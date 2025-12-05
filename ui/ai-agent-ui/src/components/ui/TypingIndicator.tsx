'use client'

export function TypingIndicator() {
  return (
    <div className="flex items-start space-x-3 p-4 animate-fade-in">
      {/* AI Avatar */}
      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
        <span className="text-white text-sm font-semibold">AI</span>
      </div>

      {/* Typing animation */}
      <div className="bg-slate-800 rounded-lg px-4 py-3 max-w-[80%]">
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    </div>
  )
}