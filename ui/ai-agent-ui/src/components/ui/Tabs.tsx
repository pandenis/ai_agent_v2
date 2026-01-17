'use client';

import { useState, createContext, useContext, ReactNode } from 'react';

// Types
interface TabsContextType {
  activeTab: string;
  setActiveTab: (id: string) => void;
}

interface TabsProps {
  defaultTab: string;
  children: ReactNode;
  className?: string;
}

interface TabListProps {
  children: ReactNode;
  className?: string;
}

interface TabProps {
  id: string;
  label: string;
  icon?: ReactNode;
  className?: string;
}

interface TabPanelProps {
  id: string;
  children: ReactNode;
  className?: string;
}

// Context
const TabsContext = createContext<TabsContextType | null>(null);

function useTabsContext() {
  const context = useContext(TabsContext);
  if (!context) {
    throw new Error('Tab components must be used within a Tabs component');
  }
  return context;
}

// Components
export function Tabs({ defaultTab, children, className = '' }: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultTab);

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className={`flex flex-col h-full ${className}`}>
        {children}
      </div>
    </TabsContext.Provider>
  );
}

export function TabList({ children, className = '' }: TabListProps) {
  return (
    <div
      className={`flex border-b border-border ${className}`}
      role="tablist"
    >
      {children}
    </div>
  );
}

export function Tab({ id, label, icon, className = '' }: TabProps) {
  const { activeTab, setActiveTab } = useTabsContext();
  const isActive = activeTab === id;

  return (
    <button
      role="tab"
      aria-selected={isActive}
      aria-controls={`panel-${id}`}
      id={`tab-${id}`}
      onClick={() => setActiveTab(id)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          setActiveTab(id);
        }
      }}
      className={`
        flex items-center gap-1.5 px-3 py-2 text-sm font-medium
        transition-colors duration-200
        border-b-2 -mb-[1px]
        ${isActive
          ? 'border-primary text-primary'
          : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground/50'
        }
        ${className}
      `}
    >
      {icon && <span className="w-4 h-4">{icon}</span>}
      {label}
    </button>
  );
}

export function TabPanel({ id, children, className = '' }: TabPanelProps) {
  const { activeTab } = useTabsContext();
  const isActive = activeTab === id;

  if (!isActive) return null;

  return (
    <div
      role="tabpanel"
      id={`panel-${id}`}
      aria-labelledby={`tab-${id}`}
      className={`flex-1 overflow-y-auto ${className}`}
    >
      {children}
    </div>
  );
}