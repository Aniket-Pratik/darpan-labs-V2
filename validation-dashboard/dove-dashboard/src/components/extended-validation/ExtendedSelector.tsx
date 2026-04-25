import { useExtendedStore } from '../../store/useExtendedStore';
import type { IndividualValidationData } from '../../types/individual';
import type { ExtendedValidationView } from '../../types/extended';

const CONCEPT_NAMES = ['Body Spray', 'Skip', 'Night Wash', 'Yours & Mine', 'Skin ID'];
const VIEWS: { value: ExtendedValidationView; label: string }[] = [
  { value: 'average', label: 'Average Twin' },
  { value: 'best-match', label: 'Best-Match Twin' },
  { value: 'median', label: 'Median Twin' },
];

interface Props {
  data: IndividualValidationData;
}

export function ExtendedSelector({ data }: Props) {
  const {
    validationView, setValidationView,
    selectedParticipant, setSelectedParticipant,
    selectedConcept, setSelectedConcept,
  } = useExtendedStore();

  const participants = data.pairs.map((p) => p.participant_id);

  return (
    <div className="flex items-center gap-3 flex-wrap">
      <div className="flex bg-darpan-surface rounded-lg p-0.5 border border-darpan-border">
        {VIEWS.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => setValidationView(value)}
            className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-all cursor-pointer border ${
              validationView === value
                ? 'bg-darpan-lime/15 text-darpan-lime border-darpan-lime/30 shadow-[0_0_10px_rgba(200,255,0,0.15)]'
                : 'text-white/40 border-transparent hover:text-white/60 hover:border-darpan-border'
            }`}
          >
            {label}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-2">
        <label className="text-[11px] text-white/40 font-medium">Participant</label>
        <select
          value={selectedParticipant}
          onChange={(e) => setSelectedParticipant(e.target.value)}
          className="bg-darpan-surface border border-darpan-border rounded-lg px-3 py-1.5 text-sm text-white font-mono focus:border-darpan-lime/50 focus:outline-none cursor-pointer"
        >
          {participants.map((id) => (
            <option key={id} value={id}>{id}</option>
          ))}
        </select>
      </div>
      <div className="flex items-center gap-2">
        <label className="text-[11px] text-white/40 font-medium">Concept</label>
        <select
          value={selectedConcept}
          onChange={(e) => setSelectedConcept(Number(e.target.value))}
          className="bg-darpan-surface border border-darpan-border rounded-lg px-3 py-1.5 text-sm text-white font-mono focus:border-darpan-lime/50 focus:outline-none cursor-pointer"
        >
          <option value={-1}>All Concepts</option>
          {CONCEPT_NAMES.map((name, idx) => (
            <option key={idx} value={idx}>{name}</option>
          ))}
        </select>
      </div>
    </div>
  );
}
