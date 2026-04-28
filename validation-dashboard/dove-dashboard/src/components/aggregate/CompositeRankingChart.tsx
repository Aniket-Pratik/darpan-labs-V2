import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { CONCEPT_COLORS } from '../../constants/theme';
import { useDashboardStore } from '../../store/useDashboardStore';
import type { DashboardData } from '../../types';

interface Props {
  data: DashboardData;
}

export function CompositeRankingChart({ data }: Props) {
  const dataSource = useDashboardStore((s) => s.dataSource);
  const focusedConcept = useDashboardStore((s) => s.focusedConcept);
  const drilldownMetric = useDashboardStore((s) => s.drilldownMetric);

  // Use composites keys instead of metadata.concept_short_names to avoid
  // name-mismatches in the source JSON (e.g., metadata says "60-Second Body "
  // with a trailing space while composites is keyed "Body Spray").
  const conceptNames = Object.keys(data.real.composites);

  const chartData = conceptNames
    .map((name) => {
      let realVal: number | null = null;
      let twinVal: number | null = null;
      if (drilldownMetric) {
        realVal = data.real.t2b[name]?.[drilldownMetric]?.t2b ?? null;
        twinVal = data.twin.t2b[name]?.[drilldownMetric]?.t2b ?? null;
      } else {
        realVal = data.real.composites[name] ?? null;
        twinVal = data.twin.composites[name] ?? null;
      }
      return { name, real: realVal, twin: twinVal };
    })
    .sort((a, b) => {
      const aVal = dataSource === 'twin' ? (a.twin ?? 0) : (a.real ?? 0);
      const bVal = dataSource === 'twin' ? (b.twin ?? 0) : (b.real ?? 0);
      return bVal - aVal;
    });

  const showBoth = dataSource === 'both';

  return (
    <div className="bg-darpan-surface border border-darpan-border rounded-xl p-4">
      {showBoth && (
        <div className="flex items-center gap-4 mb-3 pl-[100px]">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-2 rounded-sm bg-white/70" />
            <span className="text-[10px] text-white/60 font-mono">Real</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-2 rounded-sm bg-white/25" />
            <span className="text-[10px] text-white/60 font-mono">Twin</span>
          </div>
        </div>
      )}

      <ResponsiveContainer width="100%" height={280}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#2A2A2A" horizontal={false} />
          <XAxis
            type="number"
            domain={[0, 100]}
            tick={{ fill: '#666', fontSize: 10, fontFamily: 'JetBrains Mono' }}
            axisLine={{ stroke: '#2A2A2A' }}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={100}
            tick={{ fill: '#A0A0A0', fontSize: 11 }}
            axisLine={{ stroke: '#2A2A2A' }}
          />
          <Tooltip
            cursor={{ fill: 'rgba(255,255,255,0.03)' }}
            contentStyle={{
              backgroundColor: '#111111',
              border: '1px solid #2A2A2A',
              borderRadius: 8,
              fontSize: 11,
              fontFamily: 'JetBrains Mono',
              color: '#FFFFFF',
            }}
            labelStyle={{ color: '#A0A0A0' }}
            itemStyle={{ color: '#FFFFFF' }}
            formatter={(value, name) => [
              `${Number(value)?.toFixed(1)}%`,
              name === 'real' ? 'Real' : 'Twin',
            ]}
          />
          {(dataSource === 'real' || dataSource === 'both') && (
            <Bar dataKey="real" name="real" radius={[0, 4, 4, 0]} barSize={showBoth ? 14 : 22}>
              {chartData.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={CONCEPT_COLORS[entry.name] || '#A0A0A0'}
                  opacity={!focusedConcept || focusedConcept === entry.name ? 0.85 : 0.2}
                />
              ))}
            </Bar>
          )}
          {(dataSource === 'twin' || dataSource === 'both') && (
            <Bar dataKey="twin" name="twin" radius={[0, 4, 4, 0]} barSize={showBoth ? 14 : 22}>
              {chartData.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={CONCEPT_COLORS[entry.name] || '#A0A0A0'}
                  opacity={
                    !focusedConcept || focusedConcept === entry.name ? (showBoth ? 0.3 : 0.85) : 0.1
                  }
                />
              ))}
            </Bar>
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
