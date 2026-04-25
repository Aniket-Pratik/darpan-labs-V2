import { useValidationStore } from '../../store/useValidationStore';
import type { IndividualValidationData } from '../../types/individual';

const CONCEPT_NAMES = ['Body Spray', 'Skip', 'Night Wash', 'Yours & Mine', 'Skin ID'];

interface Props {
  data: IndividualValidationData;
}

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`px-2.5 py-1 rounded-md text-[11px] font-medium border transition-colors cursor-pointer ${
        active
          ? 'bg-darpan-lime/10 text-darpan-lime border-darpan-lime/20'
          : 'bg-white/[0.02] text-white/40 border-darpan-border hover:text-white/70 hover:border-darpan-border-active'
      }`}
    >
      {children}
    </button>
  );
}

export function ParticipantConceptSelector({ data }: Props) {
  const { selectedParticipant, selectedConcept, setSelectedParticipant, setSelectedConcept } =
    useValidationStore();
  const participants = data.pairs.map((p) => p.participant_id);

  return (
    <div className="bg-darpan-surface border border-darpan-border rounded-xl px-5 py-4 space-y-3">
      <div>
        <p className="text-xs font-medium text-white/30 uppercase tracking-wider mb-2">
          Participant
        </p>
        <div className="flex flex-wrap gap-1.5">
          {participants.map((pid) => (
            <Chip
              key={pid}
              active={selectedParticipant === pid}
              onClick={() => setSelectedParticipant(pid)}
            >
              {pid}
            </Chip>
          ))}
        </div>
      </div>

      <div>
        <p className="text-xs font-medium text-white/30 uppercase tracking-wider mb-2">Concept</p>
        <div className="flex flex-wrap gap-1.5">
          <Chip active={selectedConcept === -1} onClick={() => setSelectedConcept(-1)}>
            All Concepts
          </Chip>
          {CONCEPT_NAMES.map((name, idx) => (
            <Chip
              key={name}
              active={selectedConcept === idx}
              onClick={() => setSelectedConcept(idx)}
            >
              {name}
            </Chip>
          ))}
        </div>
      </div>
    </div>
  );
}
