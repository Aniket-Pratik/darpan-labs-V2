import { qualityColor, formatMetricValue } from '../../lib/validation-utils';
import type { ValidationMetricType } from '../../types/individual';
import { VALIDATION_METRIC_LABELS } from '../../constants/theme';

interface AccuracyCardProps {
  metricType: ValidationMetricType;
  value: number | null;
  quality: string;
}

export function AccuracyCard({ metricType, value, quality }: AccuracyCardProps) {
  const color = qualityColor(value, metricType);
  const qualityColors: Record<string, string> = {
    Good: '#00FF88',
    Acceptable: '#FFB800',
    Poor: '#FF4444',
  };
  const badgeColor = qualityColors[quality] || '#666666';

  return (
    <div className="bg-darpan-surface border border-darpan-border rounded-xl p-4 flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <span className="text-xs text-white/40 uppercase tracking-wider">
          {VALIDATION_METRIC_LABELS[metricType]}
        </span>
        <span
          className="text-[10px] font-mono px-1.5 py-0.5 rounded"
          style={{
            color: badgeColor,
            backgroundColor: `${badgeColor}15`,
          }}
        >
          {quality}
        </span>
      </div>
      <span className="text-lg font-mono font-bold tabular-nums" style={{ color }}>
        {formatMetricValue(value, metricType)}
      </span>
      <span className="text-[10px] text-white/25 font-mono">
        {metricType === 'mae' && '<1.0 Good · 1.0–1.5 OK · >1.5 Poor'}
        {metricType === 'accuracy' && '≥85% Good · 70–85% OK · <70% Poor'}
        {metricType === 'exact' && '≥45% Good · 25–45% OK · <25% Poor'}
      </span>
    </div>
  );
}
