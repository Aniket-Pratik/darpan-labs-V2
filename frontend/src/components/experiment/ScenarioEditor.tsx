'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Plus, X, Play, Loader2 } from 'lucide-react';
import type { ExperimentScenario, ScenarioType } from '@/types/experiment';
import { SCENARIO_TYPES } from '@/types/experiment';

interface ScenarioEditorProps {
  onSubmit: (name: string, scenario: ExperimentScenario) => void;
  isSubmitting?: boolean;
}

export function ScenarioEditor({ onSubmit, isSubmitting }: ScenarioEditorProps) {
  const [name, setName] = useState('');
  const [type, setType] = useState<ScenarioType>('forced_choice');
  const [prompt, setPrompt] = useState('');
  const [context, setContext] = useState('');
  const [options, setOptions] = useState<string[]>(['', '']);

  const needsOptions = type === 'forced_choice' || type === 'preference_rank';
  const isLikert = type === 'likert_scale';

  const addOption = () => {
    if (options.length < 10) {
      setOptions([...options, '']);
    }
  };

  const removeOption = (index: number) => {
    if (options.length > 2) {
      setOptions(options.filter((_, i) => i !== index));
    }
  };

  const updateOption = (index: number, value: string) => {
    const updated = [...options];
    updated[index] = value;
    setOptions(updated);
  };

  const handleSubmit = () => {
    if (!name.trim() || !prompt.trim()) return;

    const scenario: ExperimentScenario = {
      type,
      prompt: prompt.trim(),
      context: context.trim() || null,
      options: needsOptions
        ? options.filter((o) => o.trim())
        : isLikert
        ? ['1', '2', '3', '4', '5']
        : null,
    };

    if (needsOptions && (scenario.options?.length || 0) < 2) return;

    onSubmit(name.trim(), scenario);
  };

  const isValid =
    name.trim() &&
    prompt.trim() &&
    (!needsOptions || options.filter((o) => o.trim()).length >= 2);

  return (
    <div className="space-y-6">
      {/* Experiment name */}
      <div>
        <label className="block text-sm text-white/50 mb-2">Experiment Name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., Cola preference test, Pricing sensitivity"
          className="w-full px-4 py-3 bg-darpan-surface border border-darpan-border rounded-lg
                   text-white placeholder-white/30 focus:border-darpan-lime focus:outline-none"
        />
      </div>

      {/* Scenario type */}
      <div>
        <label className="block text-sm text-white/50 mb-2">Scenario Type</label>
        <div className="grid grid-cols-2 gap-2">
          {(Object.entries(SCENARIO_TYPES) as [ScenarioType, { label: string; description: string }][]).map(
            ([key, info]) => (
              <button
                key={key}
                onClick={() => setType(key)}
                className={`p-3 rounded-lg border text-left transition-colors ${
                  type === key
                    ? 'border-darpan-lime bg-darpan-lime/5'
                    : 'border-darpan-border hover:border-white/20'
                }`}
              >
                <p className={`text-sm font-medium ${type === key ? 'text-darpan-lime' : 'text-white'}`}>
                  {info.label}
                </p>
                <p className="text-xs text-white/40 mt-0.5">{info.description}</p>
              </button>
            )
          )}
        </div>
      </div>

      {/* Scenario prompt */}
      <div>
        <label className="block text-sm text-white/50 mb-2">Scenario Prompt</label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe the scenario or question you want to test against the twins..."
          rows={4}
          className="w-full px-4 py-3 bg-darpan-surface border border-darpan-border rounded-lg
                   text-white placeholder-white/30 focus:border-darpan-lime focus:outline-none resize-none"
        />
      </div>

      {/* Context (optional) */}
      <div>
        <label className="block text-sm text-white/50 mb-2">
          Context <span className="text-white/30">(optional)</span>
        </label>
        <textarea
          value={context}
          onChange={(e) => setContext(e.target.value)}
          placeholder="Additional context about the scenario, brand, or product..."
          rows={2}
          className="w-full px-4 py-3 bg-darpan-surface border border-darpan-border rounded-lg
                   text-white placeholder-white/30 focus:border-darpan-lime focus:outline-none resize-none"
        />
      </div>

      {/* Options (for forced_choice / preference_rank) */}
      {needsOptions && (
        <div>
          <label className="block text-sm text-white/50 mb-2">Options</label>
          <div className="space-y-2">
            {options.map((opt, i) => (
              <div key={i} className="flex gap-2">
                <input
                  type="text"
                  value={opt}
                  onChange={(e) => updateOption(i, e.target.value)}
                  placeholder={`Option ${i + 1}`}
                  className="flex-1 px-4 py-2 bg-darpan-surface border border-darpan-border rounded-lg
                           text-white placeholder-white/30 focus:border-darpan-lime focus:outline-none"
                />
                {options.length > 2 && (
                  <button
                    onClick={() => removeOption(i)}
                    className="p-2 text-white/30 hover:text-red-400"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
            {options.length < 10 && (
              <button
                onClick={addOption}
                className="flex items-center gap-1 text-sm text-darpan-lime/70 hover:text-darpan-lime"
              >
                <Plus className="w-3 h-3" />
                Add Option
              </button>
            )}
          </div>
        </div>
      )}

      {/* Likert info */}
      {isLikert && (
        <div className="p-3 bg-darpan-surface border border-darpan-border rounded-lg">
          <p className="text-xs text-white/50">
            Likert scale automatically uses 1-5 rating. Twins will rate based on your prompt.
          </p>
        </div>
      )}

      {/* Submit */}
      <motion.button
        onClick={handleSubmit}
        disabled={!isValid || isSubmitting}
        className="w-full flex items-center justify-center gap-2 px-6 py-3
                 bg-gradient-to-r from-darpan-lime to-darpan-cyan text-black font-semibold rounded-lg
                 disabled:opacity-30 disabled:cursor-not-allowed
                 hover:opacity-90 transition-opacity"
        whileTap={{ scale: 0.98 }}
      >
        {isSubmitting ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : (
          <Play className="w-5 h-5" />
        )}
        Run Experiment
      </motion.button>
    </div>
  );
}
