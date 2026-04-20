"use client";

import type { AnyWidget } from "@/lib/types";
import { BrandLattice } from "./BrandLattice";
import { ConjointCards } from "./ConjointCards";
import { ForcedRank } from "./ForcedRank";
import { SliderBattery } from "./SliderBattery";
import { TextComposer } from "./TextComposer";
import { TonePair } from "./TonePair";

export function Composer({
  widget,
  disabled,
  onSubmitText,
  onSubmitStructured,
}: {
  widget?: AnyWidget | null;
  disabled?: boolean;
  onSubmitText: (text: string) => void;
  onSubmitStructured: (struct: Record<string, unknown>) => void;
}) {
  if (!widget) {
    return <TextComposer onSubmit={onSubmitText} disabled={disabled} />;
  }
  switch (widget.type) {
    case "slider_battery":
      return <SliderBattery widget={widget} onSubmit={onSubmitStructured} disabled={disabled} />;
    case "brand_lattice":
      return <BrandLattice widget={widget} onSubmit={onSubmitStructured} disabled={disabled} />;
    case "conjoint":
      return <ConjointCards widget={widget} onSubmit={onSubmitStructured} disabled={disabled} />;
    case "rank":
      return <ForcedRank widget={widget} onSubmit={onSubmitStructured} disabled={disabled} />;
    case "tone_pair":
      return <TonePair widget={widget} onSubmit={onSubmitStructured} disabled={disabled} />;
    default:
      return <TextComposer onSubmit={onSubmitText} disabled={disabled} />;
  }
}
