"""Centralized constants for the Invoca Intent Explorer."""

from __future__ import annotations

# Intent color map (for consistent chart colors)
INTENT_COLORS: dict[str, str] = {
    "legal_inquiry": "#3B82F6",
    "brand_confusion": "#EF4444",
    "information_request": "#10B981",
    "complaint": "#F59E0B",
    "unknown": "#94A3B8",
}

# Quality bands (from walker_brain pattern)
QUALITY_BANDS: dict[str, dict] = {
    "POOR": {"range": (1.0, 2.0), "color": "#EF4444"},
    "NEEDS_IMPROVEMENT": {"range": (2.0, 3.0), "color": "#F59E0B"},
    "ADEQUATE": {"range": (3.0, 3.5), "color": "#6B7280"},
    "STRONG": {"range": (3.5, 4.5), "color": "#10B981"},
    "EXCEPTIONAL": {"range": (4.5, 5.0), "color": "#3B82F6"},
}

# Filter presets (canonical source — referenced by ui.py)
MAIN_FILTER_PRESETS: dict[str, tuple[str, str]] = {
    "All Calls": ("", ""),
    "BC Focus": ("betterclaims", "5BC%"),
    "LD Focus": ("defensores", "LD%"),
    "AF Focus": ("accident fighters", "AF%"),
    "1800LAW2 Focus": ("law2", "1800%"),
}
