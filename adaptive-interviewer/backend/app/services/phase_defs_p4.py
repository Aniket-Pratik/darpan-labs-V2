"""Phase 4 — Universal tail (BFI-2-S + PVQ-10 + aspirational ranking + close).

Registered at import time via `register_phase`.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.services.phase_defs import BlockDef, ItemDef, PhaseDef, register_phase

DATA_DIR = Path(__file__).parent.parent / "data"
_BFI = json.loads((DATA_DIR / "bfi_2s_items.json").read_text())
_PVQ = json.loads((DATA_DIR / "pvq10_items.json").read_text())
_IDENTITY = json.loads((DATA_DIR / "identity_adjectives.json").read_text())


BFI_ITEM = ItemDef(
    id="phase4.F_BFI",
    module_code="F_BFI",
    phase="phase4",
    block="personality",
    kind="slider_battery",
    prompt=(
        "Quick shift — I'm going to show you 30 short statements. For "
        "each one, tell me how much it sounds like you on a 1 to 5 "
        "scale. 1 means 'not at all', 5 means 'very much'. No right "
        "answers."
    ),
    purpose="BFI-2-S Big Five personality inventory (30 items).",
    max_probes=0,
    widget={
        "type": "slider_battery",
        "instrument": "bfi_2s",
        "stem": _BFI["stem"],
        "scale": _BFI["scale"],
        "items": _BFI["items"],
        "items_per_screen": _BFI.get("items_per_screen", 10),
        "citation": _BFI["citation"],
    },
)

PVQ_ITEM = ItemDef(
    id="phase4.F_PVQ",
    module_code="F_PVQ",
    phase="phase4",
    block="values",
    kind="slider_battery",
    prompt=(
        "Ten more short descriptions — each one describes a different "
        "person. For each, tell me how much this person is like you "
        "on a 1 to 6 scale."
    ),
    purpose="Schwartz PVQ-10 basic values inventory (10 items).",
    max_probes=0,
    widget={
        "type": "slider_battery",
        "instrument": "pvq_10",
        "instruction": _PVQ["instruction"],
        "scale": _PVQ["scale"],
        "items": _PVQ["items"],
        "items_per_screen": 5,
        "citation": _PVQ["citation"],
    },
)

RANK_ITEM = ItemDef(
    id="phase4.F_RANK",
    module_code="F_RANK",
    phase="phase4",
    block="identity",
    kind="rank",
    prompt=_IDENTITY["instruction"],
    purpose="Aspirational identity forced ranking.",
    max_probes=0,
    widget={
        "type": "rank",
        "adjectives": _IDENTITY["adjectives"],
        "top_n": _IDENTITY["top_n"],
    },
)

CLOSE_ITEM = ItemDef(
    id="phase4.F_CLOSE",
    module_code="F_CLOSE",
    phase="phase4",
    block="close",
    kind="open",
    prompt=(
        "Two last things. First — anything you expected me to ask that "
        "I didn't? I'd rather know now than miss it.\n\nAnd finally — "
        "thanks for this. If you have any feedback on the interview "
        "itself, this is the place."
    ),
    purpose="Meta-feedback close. Also final QA check for missed items.",
    max_probes=1,
)


register_phase(PhaseDef(
    id="phase4",
    label="Universal Tail",
    budget_minutes=15,
    blocks=[
        BlockDef(
            id="personality",
            phase="phase4",
            label="Personality (BFI-2-S)",
            budget_minutes=6,
            items=[BFI_ITEM],
        ),
        BlockDef(
            id="values",
            phase="phase4",
            label="Values (PVQ-10)",
            budget_minutes=4,
            items=[PVQ_ITEM],
        ),
        BlockDef(
            id="identity",
            phase="phase4",
            label="Aspirational identity ranking",
            budget_minutes=3,
            items=[RANK_ITEM],
        ),
        BlockDef(
            id="close",
            phase="phase4",
            label="Close",
            budget_minutes=2,
            items=[CLOSE_ITEM],
        ),
    ],
))
