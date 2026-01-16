'use client'

import { Toaster } from 'react-hot-toast'

export function ToastProvider() {
  return (
    <Toaster
      position="top-right"
      reverseOrder={false}
      toastOptions={{
        // Default options
        duration: 4000,
        style: {
          background: '#1e293b', // slate-800
          color: '#f1f5f9', // slate-100
          border: '1px solid #334155', // slate-700
        },
        // Success
        success: {
          duration: 3000,
          iconTheme: {
            primary: '#10b981', // green-500
            secondary: '#f1f5f9',
          },
        },
        // Error
        error: {
          duration: 5000,
          iconTheme: {
            primary: '#ef4444', // red-500
            secondary: '#f1f5f9',
          },
        },
        // Loading
        loading: {
          iconTheme: {
            primary: '#3b82f6', // blue-500
            secondary: '#f1f5f9',
          },
        },
      }}
    />
  )
}