import { qualityColor, formatMetricValue } from '../../lib/validation-utils';
import type { IndividualValidationData, ValidationMetricType } from '../../types/individual';

interface Props {
  data: IndividualValidationData;
}

const METRICS: { key: ValidationMetricType; label: string; description: string }[] = [
  { key: 'mae', label: 'Overall MAE', description: 'Mean absolute error' },
  { key: 'accuracy', label: 'Overall ±1 Accuracy', description: 'Within 1 point' },
  { key: 'exact', label: 'Overall Exact Match', description: 'Exactly correct' },
];

export function AggregateSummaryCards({ data }: Props) {
  const { aggregate } = data;

  const getValue = (key: ValidationMetricType): number | null => {
    if (key === 'mae') return aggregate.overall_mae;
    if (key === 'accuracy') return aggregate.overall_accuracy;
    return aggregate.overall_exact;
  };

  return (
    <div className="grid grid-cols-3 gap-3">
      {METRICS.map(({ key, label, description }) => {
        const value = getValue(key);
        const color = qualityColor(value, key);
        const quality = aggregate.overall_quality[key];
        return (
          <div
            key={key}
            className="bg-darpan-surface border border-darpan-border rounded-xl px-4 py-3"
          >
            <div className="text-xs text-white/40 uppercase tracking-wider mb-1">{label}</div>
            <div className="text-lg font-mono font-bold tabular-nums mb-1" style={{ color }}>
              {formatMetricValue(value, key)}
            </div>
            <div className="flex items-center gap-2">
              <span
                className="text-[10px] font-mono px-1.5 py-0.5 rounded"
                style={{ color, backgroundColor: `${color}15` }}
              >
                {quality}
              </span>
              <span className="text-[10px] text-white/30">{description}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
