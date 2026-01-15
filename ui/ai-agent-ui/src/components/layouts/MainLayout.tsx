'use client';

import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { ThemeToggle } from '@/components/features/ThemeToggle';

interface MainLayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  contextPanel?: React.ReactNode;
}

export function MainLayout({ children, sidebar, contextPanel }: MainLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [contextOpen, setContextOpen] = useState(false);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if typing in input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      if (e.key === 'F1') {
        e.preventDefault();
        setSidebarOpen(prev => !prev);
      } else if (e.key === 'F2') {
        e.preventDefault();
        setContextOpen(prev => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="flex h-screen bg-background">
      {/* Dialog Panel (Left Sidebar) - 250px */}
      {sidebar && (
        <aside
          className={cn(
            'w-[250px] border-r border-border bg-card transition-all duration-300 flex-shrink-0',
            !sidebarOpen && 'w-0 overflow-hidden'
          )}
        >
          <div className="w-[250px] h-full">{sidebar}</div>
        </aside>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Bar */}
        <header className="h-14 border-b border-border flex items-center px-4 gap-2 flex-shrink-0">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-accent rounded-md transition-colors"
            aria-label="Toggle sidebar"
            title="Toggle sidebar (F1)"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          
          <span className="font-semibold text-lg">AI Agent</span>
          
          {/* Keyboard hints */}
          <div className="hidden md:flex items-center gap-2 text-xs text-muted-foreground ml-4">
            <kbd className="px-1.5 py-0.5 bg-muted rounded text-[10px]">F1</kbd>
            <span>Sidebar</span>
            <kbd className="px-1.5 py-0.5 bg-muted rounded text-[10px] ml-2">F2</kbd>
            <span>Context</span>
          </div>
          
          <div className="flex-1" />

          <ThemeToggle />
          
          <button
            onClick={() => setContextOpen(!contextOpen)}
            className={cn(
              'p-2 hover:bg-accent rounded-md transition-colors',
              contextOpen && 'bg-accent'
            )}
            aria-label="Toggle context panel"
            title="Toggle context (F2)"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
        </header>

        {/* Main Chat Area */}
        <main className="flex-1 overflow-hidden">
          {children}
        </main>

        {/* Status Bar */}
        <footer className="h-8 border-t border-border flex items-center px-4 text-xs text-muted-foreground flex-shrink-0">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            Connected
          </span>
          <span className="mx-2 text-border">|</span>
          <span>Model: Orchestrator</span>
          <div className="flex-1" />
          <span>v1.0.0</span>
        </footer>
      </div>

      {/* Context Panel (Right Sidebar) - 300px */}
      {contextPanel && (
        <aside
          className={cn(
            'w-[300px] border-l border-border bg-card transition-all duration-300 flex-shrink-0',
            !contextOpen && 'w-0 overflow-hidden'
          )}
        >
          <div className="w-[300px] h-full">{contextPanel}</div>
        </aside>
      )}
    </div>
  );
}
