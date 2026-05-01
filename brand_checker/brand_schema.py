"""Pydantic models for brand specification validation."""

from __future__ import annotations

import re
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class HexColor(str):
    """Validated hex color string."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        import pydantic
        return pydantic.BeforeValidator(cls._validate)

    @classmethod
    def _validate(cls, v: str) -> str:
        if not isinstance(v, str):
            raise TypeError("Color must be a string")
        v = v.strip()
        if not re.match(r"^#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$", v):
            raise ValueError(f"Invalid hex color: {v}")
        if len(v) == 4:
            r, g, b = v[1], v[2], v[3]
            v = f"#{r}{r}{g}{g}{b}{b}"
        return v.upper()


class ColorEntry(BaseModel):
    """A named color in the brand palette."""

    name: str = Field(..., min_length=1, description="Human-readable color name")
    hex: str = Field(..., pattern=r"^#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$", description="Hex color value")
    cmyk: Optional[str] = Field(None, description="CMYK values, e.g. '0, 85, 100, 0'")
    pantone: Optional[str] = Field(None, description="Pantone code, e.g. 'PMS 186 C'")

    @field_validator("hex")
    @classmethod
    def normalize_hex(cls, v: str) -> str:
        v = v.strip()
        if len(v) == 4:
            r, g, b = v[1], v[2], v[3]
            v = f"#{r}{r}{g}{g}{b}{b}"
        return v.upper()


class TypographyRule(BaseModel):
    """Typography constraint."""

    font_family: str = Field(..., min_length=1, description="Allowed font family name")
    allowed_sizes: Optional[List[int]] = Field(None, description="Allowed font sizes in px")
    allowed_weights: Optional[List[int]] = Field(None, description="Allowed font weights (e.g. 400, 700)")
    max_size: Optional[int] = Field(None, ge=1, description="Maximum font size in px")
    min_size: Optional[int] = Field(None, ge=1, description="Minimum font size in px")


class LogoRules(BaseModel):
    """Logo usage constraints."""

    min_width_px: Optional[int] = Field(None, ge=1, description="Minimum logo width in pixels")
    min_height_px: Optional[int] = Field(None, ge=1, description="Minimum logo height in pixels")
    clear_space_ratio: Optional[float] = Field(
        None, gt=0, description="Minimum clear space as ratio of logo width"
    )
    allowed_formats: Optional[List[str]] = Field(
        None, description="Allowed image formats, e.g. ['PNG', 'SVG']"
    )


class VoiceTone(BaseModel):
    """Brand voice and tone guidelines."""

    tone_keywords: List[str] = Field(
        default_factory=list, description="Desired tone descriptors"
    )
    banned_words: List[str] = Field(
        default_factory=list, description="Words to avoid in copy"
    )
    max_sentence_length: Optional[int] = Field(
        None, ge=1, description="Maximum words per sentence"
    )
    max_paragraph_length: Optional[int] = Field(
        None, ge=1, description="Maximum sentences per paragraph"
    )
    required_includes: Optional[List[str]] = Field(
        None, description="Words/phrases that must appear"
    )


class BrandSpec(BaseModel):
    """Top-level brand specification."""

    brand_name: str = Field(..., min_length=1, description="Brand name")
    colors: List[ColorEntry] = Field(default_factory=list, description="Brand color palette")
    typography: List[TypographyRule] = Field(default_factory=list, description="Typography rules")
    logo: Optional[LogoRules] = Field(None, description="Logo usage rules")
    voice: Optional[VoiceTone] = Field(None, description="Voice and tone guidelines")
