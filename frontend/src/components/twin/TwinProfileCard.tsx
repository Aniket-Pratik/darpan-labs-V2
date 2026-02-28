'use client';

import { Bot, Shield, Layers } from 'lucide-react';
import { QUALITY_LABELS } from '@/types/twin';
import type { TwinProfile } from '@/types/twin';

interface TwinProfileCardProps {
  twin: TwinProfile;
  compact?: boolean;
  label?: string;
}

export default function TwinProfileCard({ twin, compact = false, label = 'Your Digital Twin' }: TwinProfileCardProps) {
  const qualityInfo = QUALITY_LABELS[twin.quality_label] || QUALITY_LABELS.base;

  if (compact) {
    return (
      <div className="flex items-center gap-3 px-4 py-3 bg-darpan-surface border-b border-darpan-border">
        <div className="w-8 h-8 rounded-full bg-darpan-cyan/20 flex items-center justify-center">
          <Bot className="w-4 h-4 text-darpan-cyan" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white">{label}</p>
          <p className="text-xs text-white/40">v{twin.version} &middot; {qualityInfo.name}</p>
        </div>
        <div
          className="px-2 py-0.5 rounded-full text-xs font-mono"
          style={{ backgroundColor: `${qualityInfo.color}20`, color: qualityInfo.color }}
        >
          {Math.round(twin.quality_score * 100)}%
        </div>
      </div>
    );
  }

  return (
    <div className="bg-darpan-surface rounded-lg border border-darpan-border p-4">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-darpan-lime/20 to-darpan-cyan/20 flex items-center justify-center">
          <Bot className="w-6 h-6 text-darpan-cyan" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">{label}</h3>
          <div className="flex items-center gap-2 mt-0.5">
            <span
              className="px-2 py-0.5 rounded-full text-xs font-mono"
              style={{ backgroundColor: `${qualityInfo.color}20`, color: qualityInfo.color }}
            >
              {qualityInfo.name}
            </span>
            <span className="text-xs text-white/40">v{twin.version}</span>
          </div>
        </div>
      </div>

      {/* Quality Score */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-white/50">Quality Score</span>
          <span className="text-xs font-mono text-white/70">
            {Math.round(twin.quality_score * 100)}%
          </span>
        </div>
        <div className="w-full bg-darpan-bg rounded-full h-1.5">
          <div
            className="h-1.5 rounded-full transition-all duration-500"
            style={{
              width: `${twin.quality_score * 100}%`,
              backgroundColor: qualityInfo.color,
            }}
          />
        </div>
      </div>

      {/* Module Coverage */}
      <div className="space-y-2">
        <div className="flex items-center gap-1.5 text-xs text-white/50">
          <Layers className="w-3 h-3" />
          <span>Modules ({twin.modules_included.length})</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {twin.modules_included.map((mid) => (
            <span
              key={mid}
              className="px-2 py-0.5 bg-darpan-lime/10 text-darpan-lime text-xs rounded-full"
            >
              {mid}
            </span>
          ))}
        </div>
      </div>

      {/* Coverage bars */}
      {twin.coverage_confidence.length > 0 && (
        <div className="mt-4 space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs text-white/50">
            <Shield className="w-3 h-3" />
            <span>Coverage</span>
          </div>
          {twin.coverage_confidence.map((cc) => (
            <div key={cc.domain} className="flex items-center gap-2">
              <span className="text-[10px] text-white/40 w-6 font-mono">{cc.domain}</span>
              <div className="flex-1 bg-darpan-bg rounded-full h-1">
                <div
                  className="h-1 rounded-full bg-darpan-lime/60"
                  style={{ width: `${cc.coverage_score * 100}%` }}
                />
              </div>
              <span className="text-[10px] text-white/30 font-mono">
                {Math.round(cc.coverage_score * 100)}%
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
