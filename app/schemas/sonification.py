"""Sonification parameter schemas structured for consumption by audio synthesis engines."""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SonificationDataPoint(BaseModel):
    timestamp: str
    original_value: float
    normalized_value: float = Field(..., ge=0.0, le=1.0)
    pitch_hz: float = Field(..., ge=20.0, le=20000.0, description="Synthesizer frequency in Hertz")
    midi_note: int = Field(..., ge=0, le=127, description="Standard MIDI note value")
    musical_note: Optional[str] = Field(default=None, description="Note letter and octave e.g. A4, C#3")
    volume_db: float = Field(..., ge=-60.0, le=0.0, description="Sound pressure level in dB")
    tempo_bpm: float = Field(..., ge=30.0, le=240.0, description="Rhythmic pulse cadence")
    rhythm_density: float = Field(..., ge=0.0, le=1.0, description="Notes per pulse subdivision")
    intensity: float = Field(..., ge=0.0, le=1.0, description="Harmonic distortion or brightness")
    duration_ms: float = Field(..., gt=0, description="Envelope gate duration")
    profile_instrument: str = Field(..., description="Acoustic or synth palette allocation")


class SonificationSeries(BaseModel):
    category: str
    sound_profile: str
    mapping_description: str
    scale_mode: str = "pentatonic_minor"
    musical_key: str = "A"
    parameters: List[SonificationDataPoint]
    dynamic_range_min: float
    dynamic_range_max: float
    uncertainty_acoustic_cue: str = "Mapped to envelope stereo-spread / lowpass resonance"
