import { SectionRow } from '../layout/SectionRow';
import { CompositeRankingChart } from './CompositeRankingChart';
import { useDashboardStore } from '../../store/useDashboardStore';
import type { DashboardData } from '../../types';

const METRIC_TABS: { key: string | null; label: string; weight?: string }[] = [
  { key: null, label: 'Composite', weight: '35% PI + 25% Uniq + 20% Rel + 20% Bel' },
  { key: 'pi', label: 'Purchase Intent' },
  { key: 'uniqueness', label: 'Uniqueness' },
  { key: 'relevance', label: 'Relevance' },
  { key: 'believability', label: 'Believability' },
  { key: 'interest', label: 'Interest' },
  { key: 'brand_fit', label: 'Brand Fit' },
];

interface RankingRowProps {
  data: DashboardData;
}

export function RankingRow({ data }: RankingRowProps) {
  const drilldownMetric = useDashboardStore((s) => s.drilldownMetric);
  const setDrilldown = useDashboardStore((s) => s.setDrilldownMetric);

  const activeTab = METRIC_TABS.find((t) => t.key === drilldownMetric) ?? METRIC_TABS[0];

  return (
    <SectionRow
      title="Concept Ranking"
      subtitle={activeTab.weight ?? `T2B% for ${activeTab.label}`}
    >
      <div className="flex items-center gap-1 mb-3 flex-wrap">
        {METRIC_TABS.map((tab) => {
          const isActive = drilldownMetric === tab.key;
          const isComposite = tab.key === null;
          return (
            <button
              key={tab.key ?? 'composite'}
              onClick={() => setDrilldown(tab.key)}
              className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-all cursor-pointer border ${
                isActive
                  ? isComposite
                    ? 'bg-darpan-lime/15 text-darpan-lime border-darpan-lime/30 shadow-[0_0_10px_rgba(200,255,0,0.15)]'
                    : 'bg-darpan-cyan/15 text-darpan-cyan border-darpan-cyan/30 shadow-[0_0_10px_rgba(0,212,255,0.15)]'
                  : 'text-white/40 border-transparent hover:text-white/60 hover:border-darpan-border'
              }`}
            >
              {tab.label}
              {isComposite && !isActive && (
                <span className="ml-1 text-[9px] text-white/40">(weighted)</span>
              )}
            </button>
          );
        })}
      </div>
      <CompositeRankingChart data={data} />
    </SectionRow>
  );
}
