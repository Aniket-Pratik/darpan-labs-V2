import { useState } from 'react';
import { ConceptPill } from '../shared/ConceptPill';
import { useDashboardStore } from '../../store/useDashboardStore';
import type { DashboardData } from '../../types';

interface Props {
  data: DashboardData;
}

export function QualitativeInsightsCard({ data }: Props) {
  const [tab, setTab] = useState<'likes' | 'concerns' | 'barriers'>('likes');
  const dataSource = useDashboardStore((s) => s.dataSource);
  const block = dataSource === 'twin' ? data.twin : data.real;
  const [showScreening, setShowScreening] = useState(false);

  const concepts = data.metadata.concept_short_names;

  return (
    <div className="bg-darpan-surface border border-darpan-border rounded-xl p-5">
      <div className="text-xs font-medium uppercase tracking-wider text-white/30 mb-3">
        Qualitative Insights
      </div>

      <div className="flex gap-1 mb-3">
        {(
          [
            { key: 'likes' as const, label: 'Likes', color: '#00FF88' },
            { key: 'concerns' as const, label: 'Concerns', color: '#FF4444' },
            { key: 'barriers' as const, label: 'Barriers', color: '#FFB800' },
          ]
        ).map(({ key, label, color }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`px-2.5 py-1 text-[10px] font-medium rounded-md transition-colors cursor-pointer border ${
              tab === key
                ? 'border-transparent'
                : 'text-white/40 border-darpan-border hover:text-white/70'
            }`}
            style={
              tab === key
                ? { backgroundColor: `${color}15`, color, borderColor: `${color}30` }
                : {}
            }
          >
            {label}
          </button>
        ))}
      </div>

      <div className="space-y-3 max-h-[280px] overflow-y-auto pr-1">
        {tab === 'likes' &&
          concepts.map((name) => {
            const themes = block.themes?.[name]?.appealing ?? [];
            if (themes.length === 0)
              return (
                <div key={name}>
                  <ConceptPill name={name} />
                  <div className="mt-1 text-[10px] text-white/40 pl-3">No themes extracted</div>
                </div>
              );
            return (
              <div key={name}>
                <ConceptPill name={name} />
                <div className="mt-1.5 space-y-1">
                  {themes.slice(0, 3).map((t, i) => (
                    <div
                      key={i}
                      className="text-[10px] text-white/60 pl-3 border-l-2"
                      style={{ borderColor: '#00FF88' }}
                    >
                      <span className="text-white/80 font-medium">{t.theme_name}</span>
                      <span className="text-white/40 ml-1">({t.frequency}x)</span>
                      {t.representative_quote && (
                        <p className="text-white/40 mt-0.5 italic">
                          "{t.representative_quote.slice(0, 100)}..."
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}

        {tab === 'concerns' &&
          concepts.map((name) => {
            const themes = block.themes?.[name]?.change ?? [];
            if (themes.length === 0)
              return (
                <div key={name}>
                  <ConceptPill name={name} />
                  <div className="mt-1 text-[10px] text-white/40 pl-3">No themes extracted</div>
                </div>
              );
            return (
              <div key={name}>
                <ConceptPill name={name} />
                <div className="mt-1.5 space-y-1">
                  {themes.slice(0, 3).map((t, i) => (
                    <div
                      key={i}
                      className="text-[10px] text-white/60 pl-3 border-l-2 border-darpan-error"
                    >
                      <span className="text-white/80 font-medium">{t.theme_name}</span>
                      <span className="text-white/40 ml-1">({t.frequency}x)</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}

        {tab === 'barriers' &&
          concepts.map((name) => {
            const barriers = block.barriers[name]?.barriers ?? [];
            return (
              <div key={name}>
                <ConceptPill name={name} />
                {barriers.length === 0 ? (
                  <div className="mt-1 text-[10px] text-white/40 pl-3">No barriers reported</div>
                ) : (
                  <div className="mt-1.5 space-y-1">
                    {barriers.slice(0, 3).map((b, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between text-[10px] pl-3 border-l-2 border-darpan-warning"
                      >
                        <span className="text-white/60 capitalize">
                          {b.name.replace(/_/g, ' ')}
                        </span>
                        <span className="font-mono text-darpan-warning tabular-nums">
                          {b.pct.toFixed(0)}%
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
      </div>

      <div className="mt-3 pt-3 border-t border-darpan-border">
        <button
          type="button"
          onClick={() => setShowScreening(!showScreening)}
          className="text-[10px] text-white/40 hover:text-white/60 transition-colors cursor-pointer"
        >
          {showScreening ? '\u25BC' : '\u25B6'} Screening Context
        </button>
        {showScreening && (
          <div className="mt-2 space-y-2 text-[10px] text-white/40">
            <div>
              <span className="text-white/60 font-medium">Top Brands: </span>
              {Object.entries(block.screeningContext.top_brands)
                .slice(0, 5)
                .map(([b, c]) => `${b} (${c})`)
                .join(', ')}
            </div>
            <div>
              <span className="text-white/60 font-medium">Usage: </span>
              {Object.entries(block.screeningContext.frequencies)
                .map(([f, c]) => `${f} (${c})`)
                .join(', ')}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
