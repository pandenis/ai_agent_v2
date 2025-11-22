'use client'

import React, { useState, useRef, useEffect } from 'react'

interface Agent {
  name: string
  displayName: string
  description: string
  icon: string
}

interface AgentSelectorProps {
  selectedAgent: string
  onSelect: (agent: string) => void
  disabled?: boolean
}

const availableAgents: Agent[] = [
  {
    name: 'groq',
    displayName: 'Groq (Llama)',
    description: 'Fast & efficient for general tasks',
    icon: '⚡',
  },
  {
    name: 'mistral',
    displayName: 'Mistral 7B',
    description: 'Balanced performance & accuracy',
    icon: '🎯',
  },
  {
    name: 'gpt-oss',
    displayName: 'GPT-OSS 20B',
    description: 'Advanced reasoning & memory',
    icon: '🧠',
  },
  {
    name: 'llama3',
    displayName: 'Llama 3 8B',
    description: 'General purpose assistant',
    icon: '🦙',
  },
  {
    name: 'deepseek',
    displayName: 'DeepSeek Coder',
    description: 'Specialized for coding tasks',
    icon: '💻',
  },
]

const AgentSelector: React.FC<AgentSelectorProps> = ({
  selectedAgent,
  onSelect,
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const selectedAgentData = availableAgents.find(a => a.name === selectedAgent) || availableAgents[0]

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (agent: Agent) => {
    onSelect(agent.name)
    setIsOpen(false)
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Selected agent button */}
      <button
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className="w-full flex items-center justify-between gap-3 px-4 py-3 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:border-indigo-500 dark:hover:border-indigo-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{selectedAgentData.icon}</span>
          <div className="text-left">
            <div className="text-sm font-medium text-gray-900 dark:text-white">
              {selectedAgentData.displayName}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              {selectedAgentData.description}
            </div>
          </div>
        </div>
        <svg
          className={`w-5 h-5 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown menu */}
      {isOpen && (
        <div className="absolute z-10 w-full mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl overflow-hidden">
          {availableAgents.map((agent) => (
            <button
              key={agent.name}
              onClick={() => handleSelect(agent)}
              className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                agent.name === selectedAgent
                  ? 'bg-indigo-50 dark:bg-indigo-900/30'
                  : ''
              }`}
            >
              <span className="text-2xl">{agent.icon}</span>
              <div className="text-left flex-1">
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  {agent.displayName}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {agent.description}
                </div>
              </div>
              {agent.name === selectedAgent && (
                <svg className="w-5 h-5 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default AgentSelector
