export type WidgetKind =
  | "slider_battery"
  | "slider_matrix"
  | "brand_lattice"
  | "conjoint"
  | "rank"
  | "tone_pair";

export interface BaseWidget {
  type: WidgetKind;
}

export interface SliderBatteryWidget extends BaseWidget {
  type: "slider_battery";
  instrument: string;
  stem?: string;
  instruction?: string;
  scale: { min: number; max: number; labels: Record<string, string> };
  items: Array<{ n: number; text: string; trait?: string; reversed?: boolean; value?: string }>;
  items_per_screen: number;
  citation?: string;
}

export interface BrandLatticeWidget extends BaseWidget {
  type: "brand_lattice";
  brands: string[];
  attributes: string[];
  scale: { min: number; max: number; labels: Record<string, string> };
  dont_know_escape: boolean;
}

export interface ConjointWidget extends BaseWidget {
  type: "conjoint";
  set_index: number;
  scenario: string;
  alternatives: Array<{
    alt_index: number;
    label: string;
    attributes: Record<string, string | number>;
    display: Record<string, string>;
  }>;
  include_none: boolean;
}

export interface RankWidget extends BaseWidget {
  type: "rank";
  adjectives: string[];
  top_n: number;
}

export interface TonePairWidget extends BaseWidget {
  type: "tone_pair";
  prompt: string;
  ad_a: { id: string; label: string; description: string };
  ad_b: { id: string; label: string; description: string };
}

export type AnyWidget =
  | SliderBatteryWidget
  | BrandLatticeWidget
  | ConjointWidget
  | RankWidget
  | TonePairWidget;

export interface InterviewerMessage {
  phase: string;
  block?: string | null;
  item_id?: string | null;
  text: string;
  widget?: AnyWidget | null;
  progress_label?: string | null;
  is_terminal: boolean;
}

export interface ChatEntry {
  id: string;
  role: "interviewer" | "user";
  text: string;
  widget?: AnyWidget | null;
  ts: number;
}
