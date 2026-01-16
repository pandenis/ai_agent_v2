'use client'

import React, { useState, KeyboardEvent } from 'react'
import TextareaAutosize from 'react-textarea-autosize'
import Button from '@/components/ui/Button'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  disabled = false,
  placeholder = 'Type your message...',
}) => {
  const [message, setMessage] = useState('')

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim())
      setMessage('')
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
      <div className="flex gap-3 items-end">
        {/* Text input */}
        <div className="flex-1">
          <TextareaAutosize
		  value={message}
		  onChange={(e) => setMessage(e.target.value)}
		  onKeyDown={handleKeyPress}
		  placeholder={placeholder}
		  disabled={disabled}
		  minRows={1}
		  maxRows={10}
		  className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none disabled:opacity-50 disabled:cursor-not-allowed"
		/>
          {/* Character count */}
          <div className="mt-1 text-xs text-gray-500 dark:text-gray-400 text-right">
            {message.length} characters
          </div>
        </div>

        {/* Send button */}
        <Button
          onClick={handleSend}
          disabled={disabled || !message.trim()}
          variant="primary"
          size="lg"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </Button>
      </div>
    </div>
  )
}

export default ChatInput
