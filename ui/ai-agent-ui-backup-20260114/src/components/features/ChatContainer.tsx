'use client'

import React, { useState, useEffect } from 'react'
import MessageList from './MessageList'
import ChatInput from './ChatInput'
import AgentSelector from './AgentSelector'
import { type Message } from '@/types'
import { apiClient } from '@/lib/api/client'
import { v4 as uuidv4 } from 'uuid'

const ChatContainer: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [selectedAgent, setSelectedAgent] = useState('groq')
  const [loading, setLoading] = useState(false)
  const [sessionId] = useState(() => `session-${uuidv4()}`)

  const handleSendMessage = async (content: string) => {
    // Add user message immediately
    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMessage])
    setLoading(true)

    try {
      // Call API
      const response = await apiClient.sendMessage({
        message: content,
        session_id: sessionId,
        agent_name: selectedAgent,
        include_memory: true,
      })

      // Add assistant response
      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: response.response,
        timestamp: response.timestamp,
        agent_used: response.agent_used,
        sources: response.sources_used,
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error: any) {
      console.error('Failed to send message:', error)
      
      // Add error message
      const errorMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: `Sorry, I couldn't process your request. Error: ${error.message || 'Unknown error'}`,
        timestamp: new Date().toISOString(),
        agent_used: 'error',
      }

      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-black">
      {/* Header */}
      <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-cyan-600 bg-clip-text text-transparent mb-2">
            AI Agent Chat
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Session: {sessionId.slice(0, 20)}...
          </p>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col max-w-6xl w-full mx-auto">
        {/* Agent selector */}
        <div className="px-6 pt-4">
          <AgentSelector
            selectedAgent={selectedAgent}
            onSelect={setSelectedAgent}
            disabled={loading}
          />
        </div>

        {/* Messages */}
        <MessageList messages={messages} loading={loading} />

        {/* Input */}
        <ChatInput
          onSend={handleSendMessage}
          disabled={loading}
          placeholder={loading ? 'AI is thinking...' : 'Type your message...'}
        />
      </div>
    </div>
  )
}

export default ChatContainer
