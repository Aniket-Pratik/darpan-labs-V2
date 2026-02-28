'use client';

import { CONFIDENCE_COLORS } from '@/types/twin';

interface ConfidenceBadgeProps {
  label: string;
  score?: number;
  size?: 'sm' | 'md';
}

export default function ConfidenceBadge({ label, score, size = 'sm' }: ConfidenceBadgeProps) {
  const colors = CONFIDENCE_COLORS[label] || CONFIDENCE_COLORS.medium;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border ${colors.bg} ${colors.text} ${colors.border} ${
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm'
      } font-mono`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${
        label === 'high' ? 'bg-green-400' :
        label === 'medium' ? 'bg-yellow-400' :
        'bg-red-400'
      }`} />
      {label.toUpperCase()}
      {score !== undefined && (
        <span className="opacity-60 ml-0.5">{Math.round(score * 100)}%</span>
      )}
    </span>
  );
}
