"use client";

import clsx from "clsx";
import type { ChatEntry } from "@/lib/types";

export function ChatLog({ entries }: { entries: ChatEntry[] }) {
  return (
    <div className="chat-scroll flex flex-col gap-4 overflow-y-auto px-1 pb-4">
      {entries.map((e) => (
        <Bubble key={e.id} entry={e} />
      ))}
    </div>
  );
}

function Bubble({ entry }: { entry: ChatEntry }) {
  const isInterviewer = entry.role === "interviewer";
  return (
    <div
      className={clsx(
        "max-w-[min(44rem,90%)] whitespace-pre-wrap rounded-xl px-4 py-3 text-[15px] leading-relaxed",
        isInterviewer
          ? "self-start border border-darpan-border bg-darpan-surface text-neutral-100"
          : "self-end bg-darpan-lime/10 text-darpan-lime border border-darpan-lime/30",
      )}
    >
      {entry.text}
    </div>
  );
}
