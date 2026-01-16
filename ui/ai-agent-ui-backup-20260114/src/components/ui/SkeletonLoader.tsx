'use client'

interface SkeletonLoaderProps {
  count?: number
}

export function SkeletonLoader({ count = 3 }: SkeletonLoaderProps) {
  return (
    <div className="p-2 space-y-2">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="p-3 bg-slate-800 rounded-lg border border-slate-700 animate-pulse"
        >
          {/* Session title skeleton */}
          <div className="h-4 bg-slate-700 rounded w-3/4 mb-2"></div>

          {/* Message count skeleton */}
          <div className="h-3 bg-slate-700 rounded w-1/2 mb-2"></div>

          {/* Time ago skeleton */}
          <div className="h-3 bg-slate-700 rounded w-1/3"></div>
        </div>
      ))}
    </div>
  )
}