"""Core validation engine for brand consistency checks."""

from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from PIL import Image

from .brand_schema import BrandSpec


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Violation:
    """A single brand violation."""

    rule: str
    message: str
    severity: Severity
    context: Optional[str] = None


@dataclass
class CheckResult:
    """Aggregated result of a brand check."""

    passed: bool
    violations: List[Violation] = field(default_factory=list)
    checked_items: int = 0
    passed_items: int = 0

    @property
    def score(self) -> float:
        if self.checked_items == 0:
            return 100.0
        return round((self.passed_items / self.checked_items) * 100, 1)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _color_distance(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def _find_closest_brand_color(
    rgb: tuple[int, int, int], brand_colors: list[dict]
) -> tuple[dict | None, float]:
    best = None
    best_dist = float("inf")
    for bc in brand_colors:
        dist = _color_distance(rgb, _hex_to_rgb(bc["hex"]))
        if dist < best_dist:
            best_dist = dist
            best = bc
    return best, best_dist


# Maximum Euclidean distance in RGB space to consider a color "on-brand".
# 80 is a reasonable threshold that catches clearly off-brand colors while
# allowing minor anti-aliasing or compression artifacts.
MAX_COLOR_DISTANCE = 80.0


class BrandChecker:
    """Validates content against a brand specification."""

    def __init__(self, spec: BrandSpec):
        self.spec = spec

    def check_image(self, image_path: str) -> CheckResult:
        """Check an image's dominant colors against the brand palette."""
        violations: List[Violation] = []
        checked = 0
        passed = 0

        if not os.path.isfile(image_path):
            return CheckResult(
                passed=False,
                violations=[
                    Violation(
                        rule="file.exists",
                        message=f"Image file not found: {image_path}",
                        severity=Severity.ERROR,
                    )
                ],
            )

        try:
            img = Image.open(image_path)
        except Exception as exc:
            return CheckResult(
                passed=False,
                violations=[
                    Violation(
                        rule="file.readable",
                        message=f"Cannot open image: {exc}",
                        severity=Severity.ERROR,
                    )
                ],
            )

        # Check logo rules if present
        if self.spec.logo:
            width, height = img.size
            if self.spec.logo.min_width_px and width < self.spec.logo.min_width_px:
                violations.append(
                    Violation(
                        rule="logo.min_width",
                        message=f"Image width {width}px < minimum {self.spec.logo.min_width_px}px",
                        severity=Severity.ERROR,
                    )
                )
            else:
                passed += 1
            checked += 1

            if self.spec.logo.min_height_px and height < self.spec.logo.min_height_px:
                violations.append(
                    Violation(
                        rule="logo.min_height",
                        message=f"Image height {height}px < minimum {self.spec.logo.min_height_px}px",
                        severity=Severity.ERROR,
                    )
                )
            else:
                passed += 1
            checked += 1

        # Check colors
        if self.spec.colors:
            rgb_img = img.convert("RGB")
            pixels = list(rgb_img.getdata())
            sample_size = min(len(pixels), 1000)
            step = max(1, len(pixels) // sample_size)
            sample = pixels[::step]

            off_brand = 0
            for pixel in sample:
                closest, dist = _find_closest_brand_color(pixel, self.spec.colors)
                if dist > MAX_COLOR_DISTANCE:
                    off_brand += 1

            ratio = off_brand / len(sample) if sample else 0
            checked += 1
            if ratio > 0.3:
                violations.append(
                    Violation(
                        rule="colors.palette",
                        message=f"{ratio:.0%} of sampled pixels are off-brand",
                        severity=Severity.WARNING,
                        context=f"Closest brand colors: {[c['name'] for c in self.spec.colors[:3]]}",
                    )
                )
            else:
                passed += 1

        return CheckResult(
            passed=len([v for v in violations if v.severity == Severity.ERROR]) == 0,
            violations=violations,
            checked_items=checked,
            passed_items=passed,
        )

    def check_text(self, text: str) -> CheckResult:
        """Check text against voice/tone and typography rules."""
        violations: List[Violation] = []
        checked = 0
        passed = 0

        if not text or not text.strip():
            return CheckResult(
                passed=False,
                violations=[
                    Violation(
                        rule="text.empty",
                        message="Input text is empty",
                        severity=Severity.ERROR,
                    )
                ],
            )

        voice = self.spec.voice
        if voice:
            # Banned words
            text_lower = text.lower()
            for word in voice.banned_words:
                checked += 1
                if word.lower() in text_lower:
                    violations.append(
                        Violation(
                            rule="voice.banned_word",
                            message=f"Banned word found: '{word}'",
                            severity=Severity.ERROR,
                            context=word,
                        )
                    )
                else:
                    passed += 1

            # Sentence length
            if voice.max_sentence_length:
                sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
                for sentence in sentences:
                    checked += 1
                    word_count = len(sentence.split())
                    if word_count > voice.max_sentence_length:
                        violations.append(
                            Violation(
                                rule="voice.sentence_length",
                                message=f"Sentence has {word_count} words (max {voice.max_sentence_length})",
                                severity=Severity.WARNING,
                                context=sentence[:80] + ("..." if len(sentence) > 80 else ""),
                            )
                        )
                    else:
                        passed += 1

            # Required includes
            if voice.required_includes:
                for phrase in voice.required_includes:
                    checked += 1
                    if phrase.lower() not in text_lower:
                        violations.append(
                            Violation(
                                rule="voice.required_include",
                                message=f"Required phrase missing: '{phrase}'",
                                severity=Severity.WARNING,
                            )
                        )
                    else:
                        passed += 1

        return CheckResult(
            passed=len([v for v in violations if v.severity == Severity.ERROR]) == 0,
            violations=violations,
            checked_items=checked,
            passed_items=passed,
        )

    def generate_report(self, checks: list[tuple[str, CheckResult]]) -> str:
        """Generate a human-readable compliance report."""
        lines: list[str] = []
        lines.append(f"Brand Compliance Report — {self.spec.brand_name}")
        lines.append("=" * 60)

        total_errors = 0
        total_warnings = 0
        all_passed = True

        for label, result in checks:
            lines.append("")
            lines.append(f"--- {label} ---")
            if not result.violations:
                lines.append("  PASS — no violations found")
            else:
                for v in result.violations:
                    icon = {"error": "ERROR", "warning": "WARN", "info": "INFO"}[
                        v.severity.value
                    ]
                    lines.append(f"  [{icon}] {v.rule}: {v.message}")
                    if v.context:
                        lines.append(f"         {v.context}")
                    if v.severity == Severity.ERROR:
                        total_errors += 1
                        all_passed = False
                    elif v.severity == Severity.WARNING:
                        total_warnings += 1

        lines.append("")
        lines.append("=" * 60)
        lines.append(
            f"Summary: {total_errors} error(s), {total_warnings} warning(s) — "
            + ("COMPLIANT" if all_passed else "NON-COMPLIANT")
        )
        return "\n".join(lines)
