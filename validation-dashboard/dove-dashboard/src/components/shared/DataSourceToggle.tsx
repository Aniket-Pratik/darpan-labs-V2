import { useDashboardStore } from '../../store/useDashboardStore';
import type { DataSource } from '../../types';

const OPTIONS: { value: DataSource; label: string }[] = [
  { value: 'real', label: 'Real' },
  { value: 'twin', label: 'Twin' },
  { value: 'both', label: 'Both' },
];

export function DataSourceToggle() {
  const dataSource = useDashboardStore((s) => s.dataSource);
  const setDataSource = useDashboardStore((s) => s.setDataSource);

  return (
    <div className="flex bg-darpan-surface rounded-lg p-0.5 border border-darpan-border">
      {OPTIONS.map(({ value, label }) => (
        <button
          key={value}
          type="button"
          onClick={() => setDataSource(value)}
          className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-colors cursor-pointer border ${
            dataSource === value
              ? 'bg-darpan-lime/10 text-darpan-lime border-darpan-lime/20'
              : 'text-white/40 border-transparent hover:text-white/70'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
