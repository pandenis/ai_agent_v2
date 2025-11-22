'use client'

import React from 'react'
import { type Message as MessageType } from '@/types'

interface MessageProps {
  message: MessageType
  isUser: boolean
}

const Message: React.FC<MessageProps> = ({ message, isUser }) => {
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[70%] ${isUser ? 'order-2' : 'order-1'}`}>
        {/* Message bubble */}
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white'
              : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700'
          }`}
        >
          {/* Agent badge for assistant messages */}
          {!isUser && message.agent_used && (
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-medium text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 px-2 py-1 rounded-full">
                {message.agent_used}
              </span>
            </div>
          )}
          
          {/* Message content */}
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.content}
          </p>

          {/* Sources if available */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Sources: {message.sources.join(', ')}
              </p>
            </div>
          )}
        </div>

        {/* Timestamp */}
        <div className={`mt-1 px-2 ${isUser ? 'text-right' : 'text-left'}`}>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {formatTime(message.timestamp)}
          </span>
        </div>
      </div>

      {/* Avatar */}
      <div className={`flex-shrink-0 ${isUser ? 'order-1 mr-3' : 'order-2 ml-3'}`}>
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
            isUser
              ? 'bg-gradient-to-r from-indigo-600 to-cyan-600 text-white'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
          }`}
        >
          {isUser ? 'U' : 'AI'}
        </div>
      </div>
    </div>
  )
}

export default Message
