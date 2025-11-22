'use client'

import React from 'react'
import { type BaseProps } from '@/types'

interface CardProps extends BaseProps {
  title?: string
  subtitle?: string
  hover?: boolean
}

const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  hover = false,
  children,
  className = '',
}) => {
  const baseStyles = 'bg-white dark:bg-gray-900 rounded-2xl shadow-xl p-6 transition-all duration-300'
  
  const hoverStyles = hover ? 'hover:shadow-2xl hover:-translate-y-1 cursor-pointer' : ''
  
  const classes = `${baseStyles} ${hoverStyles} ${className}`
  
  return (
    <div className={classes}>
      {(title || subtitle) && (
        <div className="mb-4">
          {title && (
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              {title}
            </h3>
          )}
          {subtitle && (
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {subtitle}
            </p>
          )}
        </div>
      )}
      {children}
    </div>
  )
}

export default Card
