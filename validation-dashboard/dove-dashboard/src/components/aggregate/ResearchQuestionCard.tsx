import { motion } from 'framer-motion';

interface Props {
  question: string;
}

export function ResearchQuestionCard({ question }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-darpan-surface border border-darpan-border rounded-xl px-5 py-4"
    >
      <p className="text-xs font-medium text-white/30 uppercase tracking-wider mb-1.5">
        Research Question
      </p>
      <p className="text-sm text-white/60 leading-relaxed">{question}</p>
    </motion.div>
  );
}
