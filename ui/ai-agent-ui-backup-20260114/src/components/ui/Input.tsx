'use client'

import React from 'react'
import { type BaseProps } from '@/types'

interface InputProps extends BaseProps {
  type?: 'text' | 'email' | 'password' | 'number'
  placeholder?: string
  value?: string
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
  disabled?: boolean
  error?: string
}

const Input: React.FC<InputProps> = ({
  type = 'text',
  placeholder,
  value,
  onChange,
  disabled = false,
  error,
  className = '',
}) => {
  const baseStyles = 'w-full px-4 py-2 rounded-lg border transition-all duration-300 focus:outline-none focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed'
  
  const normalStyles = 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500'
  
  const errorStyles = 'bg-white dark:bg-gray-800 border-red-500 text-gray-900 dark:text-white focus:ring-red-500 focus:border-red-500'
  
  const classes = `${baseStyles} ${error ? errorStyles : normalStyles} ${className}`
  
  return (
    <div className="w-full">
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
        className={classes}
      />
      {error && (
        <p className="mt-1 text-sm text-red-500">{error}</p>
      )}
    </div>
  )
}

export default Input
