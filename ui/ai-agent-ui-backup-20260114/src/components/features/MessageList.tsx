'use client'

import React, { useEffect, useRef } from 'react'
import Message from './Message'
import { type Message as MessageType } from '@/types'

interface MessageListProps {
  messages: MessageType[]
  loading?: boolean
}

const MessageList: React.FC<MessageListProps> = ({ messages, loading = false }) => {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0 && !loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-indigo-600 to-cyan-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Start a conversation
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Choose an AI agent and send your first message
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4">
      {messages.map((message) => (
        <Message
          key={message.id}
          message={message}
          isUser={message.role === 'user'}
        />
      ))}
      
      {/* Loading indicator */}
      {loading && (
        <div className="flex justify-start mb-4">
          <div className="flex items-center gap-2 bg-white dark:bg-gray-800 rounded-2xl px-4 py-3 border border-gray-200 dark:border-gray-700">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
            </div>
            <span className="text-sm text-gray-500">AI is thinking...</span>
          </div>
        </div>
      )}
      
      {/* Scroll anchor */}
      <div ref={bottomRef} />
    </div>
  )
}

export default MessageList
