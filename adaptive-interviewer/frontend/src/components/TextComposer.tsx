"use client";

import { useState } from "react";

export function TextComposer({
  onSubmit,
  disabled,
  placeholder = "Type your answer…",
}: {
  onSubmit: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}) {
  const [value, setValue] = useState("");

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setValue("");
  };

  return (
    <div className="flex items-end gap-2">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
            e.preventDefault();
            submit();
          }
        }}
        placeholder={placeholder}
        disabled={disabled}
        rows={3}
        className="flex-1 resize-none rounded-lg border border-darpan-border bg-darpan-surface px-3 py-2 text-sm text-neutral-100 outline-none focus:border-darpan-lime disabled:opacity-50"
      />
      <button
        onClick={submit}
        disabled={disabled || !value.trim()}
        className="rounded-lg border border-darpan-lime bg-darpan-lime/15 px-4 py-2 text-sm font-medium text-darpan-lime hover:bg-darpan-lime/25 disabled:opacity-40"
      >
        Send
      </button>
    </div>
  );
}
