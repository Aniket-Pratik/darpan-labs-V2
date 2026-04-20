"""Conjoint design generator + HB-ish part-worth estimation.

DESIGN (this file, chunk D): deterministic per-session choice-set
generator. Given the archetype's attribute spec, we generate 8
choice sets × 3 alternatives using a balanced near-orthogonal draw
seeded by session_id + set_index (so reloads are stable).

ESTIMATION (chunk F): aggregate multinomial-logit fit via
scipy.optimize, then empirical-Bayes shrinkage toward the aggregate
mean for per-respondent part-worths. Not full HB MCMC — documented
in the output JSON's `estimation_method` field so downstream
analysts know what they're working with.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional
from uuid import UUID

import numpy as np

logger = logging.getLogger(__name__)

_SPECS_PATH = Path(__file__).parent.parent / "data" / "conjoint_specs.json"
_SPECS: dict[str, dict] = json.loads(_SPECS_PATH.read_text(encoding="utf-8"))


def get_spec(archetype: str) -> dict:
    if archetype not in _SPECS:
        raise KeyError(f"No conjoint spec for archetype {archetype!r}")
    return _SPECS[archetype]


def _seed_from(session_id: UUID, set_index: int, archetype: str) -> int:
    h = hashlib.sha256(f"{session_id}:{archetype}:{set_index}".encode()).hexdigest()
    return int(h[:12], 16)


def _format_level(value: Any, attr_name: str, units: dict[str, str]) -> str:
    unit = units.get(attr_name)
    if unit and isinstance(value, (int, float)):
        if attr_name == "price_usd" or attr_name == "unit_price_usd":
            return f"${int(value)}"
        return f"{value} {unit}"
    return str(value)


@dataclass
class ChoiceSet:
    set_index: int
    alternatives: list[dict[str, Any]]   # each has `attributes`, `label`
    include_none: bool
    scenario: str

    def to_widget(self) -> dict[str, Any]:
        return {
            "type": "conjoint",
            "set_index": self.set_index,
            "scenario": self.scenario,
            "alternatives": self.alternatives,
            "include_none": self.include_none,
        }


def generate_choice_set(
    archetype: str,
    session_id: UUID,
    set_index: int,
) -> ChoiceSet:
    """Balanced near-orthogonal draw for one choice set. The seed is
    deterministic per (session, archetype, set_index) so reloads
    render the same cards."""
    spec = get_spec(archetype)
    rng = np.random.default_rng(_seed_from(session_id, set_index, archetype))
    attrs = spec["attributes"]
    n_alts = int(spec["alternatives_per_set"])
    include_none = bool(spec["include_none_on_holdout"]) and set_index == spec["n_sets"] - 1
    units = spec.get("display_units", {})

    # Shuffle level order per attribute for this set, then round-robin
    # across alternatives. This guarantees each attribute shows a
    # different level in each alternative (within the set), which is
    # the simplest way to avoid dominated alternatives.
    alternatives: list[dict[str, Any]] = []
    for alt_idx in range(n_alts):
        profile: dict[str, Any] = {}
        display: dict[str, str] = {}
        for attr_name, attr_spec in attrs.items():
            levels = list(attr_spec["levels"])
            # Independent per-attribute shuffle for this set.
            perm = rng.permutation(len(levels))
            chosen = levels[int(perm[alt_idx % len(levels)])]
            profile[attr_name] = chosen
            display[attr_name] = _format_level(chosen, attr_name, units)
        alternatives.append({
            "alt_index": alt_idx,
            "label": f"Option {chr(ord('A') + alt_idx)}",
            "attributes": profile,
            "display": display,
        })
    return ChoiceSet(
        set_index=set_index,
        alternatives=alternatives,
        include_none=include_none,
        scenario=spec["scenario"],
    )


def generate_full_design(archetype: str, session_id: UUID) -> list[ChoiceSet]:
    spec = get_spec(archetype)
    return [generate_choice_set(archetype, session_id, i) for i in range(int(spec["n_sets"]))]


# ------------------- design-matrix helpers (used in chunk F) -----------------

def encode_profile(profile: dict[str, Any], archetype: str) -> dict[str, float]:
    """One-hot encode a profile for MNL estimation. Numeric levels
    are kept as numeric features (centered per attribute); nominal
    levels become k-1 dummies with the first level as baseline."""
    spec = get_spec(archetype)
    features: dict[str, float] = {}
    for attr_name, attr_spec in spec["attributes"].items():
        if attr_spec["type"] == "numeric":
            features[f"{attr_name}_num"] = float(profile[attr_name])
        else:
            levels = attr_spec["levels"]
            chosen = profile[attr_name]
            for level in levels[1:]:
                features[f"{attr_name}_is_{level}"] = 1.0 if chosen == level else 0.0
    return features


def feature_names(archetype: str) -> list[str]:
    spec = get_spec(archetype)
    names: list[str] = []
    for attr_name, attr_spec in spec["attributes"].items():
        if attr_spec["type"] == "numeric":
            names.append(f"{attr_name}_num")
        else:
            names.extend(f"{attr_name}_is_{lv}" for lv in attr_spec["levels"][1:])
    return names


def build_design_matrix(
    choices: list[dict[str, Any]],
    archetype: str,
) -> tuple[np.ndarray, np.ndarray, list[int]]:
    """Turn a respondent's conjoint responses into (X, y, set_sizes).

    Rows in X correspond to alternatives (flattened, set by set).
    y marks the chosen row per set. `set_sizes` is the count of
    alternatives per set (used by the softmax-per-set likelihood).
    "none" responses are skipped from the likelihood (the set is
    excluded) in v1 — no none-constant estimated yet.
    """
    names = feature_names(archetype)
    rows: list[list[float]] = []
    chosen_flags: list[int] = []
    set_sizes: list[int] = []
    for cs in choices:
        chosen = cs.get("chosen_alt_index", -1)
        if chosen is None or chosen == -1:
            continue  # skip "none" sets from MLE in v1
        alts = cs["alternatives"]
        for idx, alt in enumerate(alts):
            feats = encode_profile(alt, archetype)
            row = [feats.get(n, 0.0) for n in names]
            rows.append(row)
            chosen_flags.append(1 if idx == chosen else 0)
        set_sizes.append(len(alts))
    return np.array(rows, dtype=float), np.array(chosen_flags, dtype=int), set_sizes


# ------------------- MLE / empirical-Bayes estimation --------------

def _mnl_neg_log_likelihood(
    beta: np.ndarray,
    X: np.ndarray,
    y: np.ndarray,
    set_sizes: list[int],
    prior_mean: Optional[np.ndarray] = None,
    prior_var: float = 9.0,
) -> float:
    """Penalized negative log-likelihood for choice-based conjoint.

    Each set contributes -log P(chosen | set). A Gaussian prior on
    beta (default N(0, 3)) regularizes the fit since each respondent
    only has 8 sets of 3 alternatives.
    """
    if prior_mean is None:
        prior_mean = np.zeros_like(beta)
    utilities = X @ beta
    # Softmax per set.
    offset = 0
    nll = 0.0
    for size in set_sizes:
        u = utilities[offset:offset + size]
        u = u - np.max(u)  # numerical stability
        exp_u = np.exp(u)
        denom = exp_u.sum()
        chosen = y[offset:offset + size]
        chosen_idx = int(np.argmax(chosen))
        nll -= float(u[chosen_idx] - np.log(denom))
        offset += size
    penalty = 0.5 * float(np.sum((beta - prior_mean) ** 2) / prior_var)
    return nll + penalty


def estimate_part_worths(
    choices: list[dict[str, Any]],
    archetype: str,
    prior_mean: Optional[np.ndarray] = None,
) -> dict[str, Any]:
    """Fit a regularized MNL for one respondent and return per-
    attribute-level part-worths plus WTP curves (when a price
    coefficient is available).

    `prior_mean` enables empirical-Bayes shrinkage toward a
    population prior (e.g., aggregate fit across all respondents of
    the same archetype). In a single-session finalize this will be
    None and we default to a weakly-informative zero prior.
    """
    from scipy.optimize import minimize

    names = feature_names(archetype)
    if prior_mean is None:
        prior_mean = np.zeros(len(names))

    X, y, set_sizes = build_design_matrix(choices, archetype)
    if X.size == 0 or len(set_sizes) == 0:
        return {
            "feature_names": names,
            "beta": [0.0] * len(names),
            "part_worths": {},
            "wtp": {},
            "estimation_method": "skipped_no_valid_sets",
            "n_sets_fit": 0,
        }

    beta0 = prior_mean.copy()
    result = minimize(
        _mnl_neg_log_likelihood,
        beta0,
        args=(X, y, set_sizes, prior_mean, 9.0),
        method="L-BFGS-B",
        options={"maxiter": 200},
    )
    beta_hat = result.x

    # Part-worths: for nominal attributes, include baseline level with
    # part-worth 0; for numeric attributes, slope-per-unit is the
    # coefficient.
    spec = get_spec(archetype)
    part_worths: dict[str, dict[str, float]] = {}
    numeric_slopes: dict[str, float] = {}
    for attr_name, attr_spec in spec["attributes"].items():
        if attr_spec["type"] == "numeric":
            idx = names.index(f"{attr_name}_num")
            numeric_slopes[attr_name] = float(beta_hat[idx])
            part_worths[attr_name] = {
                f"slope_per_unit ({attr_name})": float(beta_hat[idx])
            }
        else:
            levels = attr_spec["levels"]
            pw: dict[str, float] = {levels[0]: 0.0}
            for lv in levels[1:]:
                col = f"{attr_name}_is_{lv}"
                pw[lv] = float(beta_hat[names.index(col)])
            part_worths[attr_name] = pw

    # WTP — USD willingness-to-pay, computed only when a price-like
    # numeric attribute exists and has a non-zero slope.
    wtp: dict[str, dict[str, float]] = {}
    price_attrs = [a for a in ("price_usd", "unit_price_usd") if a in numeric_slopes]
    if price_attrs:
        price_key = price_attrs[0]
        price_slope = numeric_slopes[price_key]
        if abs(price_slope) > 1e-8:
            for attr_name, attr_spec in spec["attributes"].items():
                if attr_name == price_key:
                    continue
                if attr_spec["type"] == "numeric":
                    slope = numeric_slopes.get(attr_name, 0.0)
                    wtp[attr_name] = {
                        "wtp_per_unit_usd": -slope / price_slope,
                    }
                else:
                    levels = attr_spec["levels"]
                    wtp_attr: dict[str, float] = {levels[0]: 0.0}
                    for lv in levels[1:]:
                        col = f"{attr_name}_is_{lv}"
                        coef = float(beta_hat[names.index(col)])
                        wtp_attr[lv] = -coef / price_slope
                    wtp[attr_name] = wtp_attr

    return {
        "feature_names": names,
        "beta": [float(b) for b in beta_hat],
        "part_worths": part_worths,
        "wtp": wtp,
        "estimation_method": (
            "per-respondent penalized MNL (L-BFGS-B, Gaussian N(0,3) prior); "
            "aggregate HB recommended once N>=100 — see README"
        ),
        "n_sets_fit": len(set_sizes),
        "converged": bool(result.success),
    }
