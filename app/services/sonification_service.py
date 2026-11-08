"""Deterministic Sonification Parameter Engine for Earth Jukebox.
Maps continuous physical units to synthesizer parameters (MIDI, Hz, tempo, intensity, musical scale).
"""
import numpy as np
from typing import List, Dict, Any, Tuple
from app.schemas.sonification import SonificationSeries, SonificationDataPoint
from app.schemas.responses import TimeSeriesPoint

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Ambient harmonic scale modes (cinematic & scientific palette)
SCALE_MODES: Dict[str, List[int]] = {
    "pentatonic_minor": [0, 3, 5, 7, 10],   # Ambient cinematic, resonant
    "dorian": [0, 2, 3, 5, 7, 9, 10],       # Atmospheric, reflective
    "lydian": [0, 2, 4, 6, 7, 9, 11],       # Biophilic, bright
    "pentatonic_major": [0, 2, 4, 7, 9],     # Harmonic, oceanic
}

CATEGORY_SOUND_PROFILES: Dict[str, Dict[str, Any]] = {
    "temperature": {
        "instrument": "Warm Analog Sine & Tonal Brightness",
        "description": "Direct frequency mapping representing thermal energy; higher values increase pitch brightness.",
        "pitch_min": 110.0,  # A2
        "pitch_max": 880.0,  # A5
        "tempo_min": 60.0,
        "tempo_max": 120.0,
        "scale_mode": "pentatonic_minor",
        "root_semitone": 9,  # Key of A
    },
    "rain": {
        "instrument": "Granular Percussion & Hydro-Acoustic Drops",
        "description": "Precipitation volume drives rhythmic density and percussive triggers.",
        "pitch_min": 150.0,
        "pitch_max": 600.0,
        "tempo_min": 50.0,
        "tempo_max": 160.0,
        "scale_mode": "dorian",
        "root_semitone": 2,  # Key of D
    },
    "wind": {
        "instrument": "Resonant Noise Generator & Modulated Swell",
        "description": "Wind velocity modulates filter resonance and tempo cadence.",
        "pitch_min": 80.0,
        "pitch_max": 400.0,
        "tempo_min": 40.0,
        "tempo_max": 140.0,
        "scale_mode": "dorian",
        "root_semitone": 4,  # Key of E
    },
    "fires": {
        "instrument": "Aggressive Staccato Pulse & FM Noise",
        "description": "Fire Radiative Power dictates pulse attack and harmonic harshness.",
        "pitch_min": 60.0,
        "pitch_max": 350.0,
        "tempo_min": 80.0,
        "tempo_max": 180.0,
        "scale_mode": "pentatonic_minor",
        "root_semitone": 7,  # Key of G
    },
    "vegetation": {
        "instrument": "Harmonic Chords & Biophilic Drone",
        "description": "NDVI changes drive chord voicing density and acoustic resonance.",
        "pitch_min": 130.0,
        "pitch_max": 520.0,
        "tempo_min": 50.0,
        "tempo_max": 90.0,
        "scale_mode": "lydian",
        "root_semitone": 5,  # Key of F
    },
    "ocean": {
        "instrument": "Deep Sub-bass & Flowing Continuous Pads",
        "description": "Sea surface temperature fluctuations dictate slow spectral swells.",
        "pitch_min": 55.0,
        "pitch_max": 220.0,
        "tempo_min": 40.0,
        "tempo_max": 80.0,
        "scale_mode": "pentatonic_major",
        "root_semitone": 0,  # Key of C
    },
    "ice": {
        "instrument": "Crystalline Sparse Chimes",
        "description": "Cryospheric extent translates to long-decay ringing harmonics.",
        "pitch_min": 440.0,
        "pitch_max": 1760.0,
        "tempo_min": 30.0,
        "tempo_max": 70.0,
        "scale_mode": "pentatonic_minor",
        "root_semitone": 11,  # Key of B
    },
    "storms": {
        "instrument": "Dynamic Atmospheric Rumble & Transient Clustered Brass",
        "description": "Storm precipitation rate maps to dynamic range surges and tempo spikes.",
        "pitch_min": 65.0,
        "pitch_max": 500.0,
        "tempo_min": 90.0,
        "tempo_max": 190.0,
        "scale_mode": "pentatonic_minor",
        "root_semitone": 0,  # Key of C
    },
}


class SonificationService:
    @staticmethod
    def _hz_to_raw_midi(hz: float) -> float:
        if hz <= 0:
            return 0.0
        return float(69 + 12 * np.log2(hz / 440.0))

    @staticmethod
    def _quantize_to_scale(raw_midi: float, scale_mode: str, root_semitone: int = 9) -> int:
        """Quantize continuous MIDI note to the nearest degree in a chosen musical scale."""
        intervals = SCALE_MODES.get(scale_mode, SCALE_MODES["pentatonic_minor"])
        int_midi = int(np.clip(np.round(raw_midi), 0, 127))
        octave = int_midi // 12
        pitch_class = int_midi % 12

        # Relative semitone offset from root
        rel = (pitch_class - root_semitone) % 12

        # Find closest allowed interval in the scale
        closest_rel = min(intervals, key=lambda x: min(abs(x - rel), 12 - abs(x - rel)))
        quantized_pitch_class = (root_semitone + closest_rel) % 12

        quantized_midi = octave * 12 + quantized_pitch_class
        return int(np.clip(quantized_midi, 0, 127))

    @staticmethod
    def _midi_to_hz(midi: int) -> float:
        return float(440.0 * (2.0 ** ((midi - 69) / 12.0)))

    @staticmethod
    def _midi_to_name(midi: int) -> str:
        octave = (midi // 12) - 1
        name = NOTE_NAMES[midi % 12]
        return f"{name}{octave}"

    @classmethod
    def generate_sonification_series(
        cls,
        category: str,
        series: List[TimeSeriesPoint],
    ) -> SonificationSeries:
        profile = CATEGORY_SOUND_PROFILES.get(
            category,
            CATEGORY_SOUND_PROFILES["temperature"],
        )

        scale_mode = profile.get("scale_mode", "pentatonic_minor")
        root_semitone = profile.get("root_semitone", 9)
        root_name = NOTE_NAMES[root_semitone]

        if not series:
            return SonificationSeries(
                category=category,
                sound_profile=profile["instrument"],
                mapping_description=profile["description"],
                scale_mode=scale_mode,
                musical_key=root_name,
                parameters=[],
                dynamic_range_min=0.0,
                dynamic_range_max=1.0,
            )

        values = [p.value for p in series]
        val_min = min(values)
        val_max = max(values)
        span = val_max - val_min if val_max > val_min else 1.0

        parameters: List[SonificationDataPoint] = []
        for p in series:
            # Deterministic linear normalization [0.0, 1.0]
            norm_val = float(np.clip((p.value - val_min) / span, 0.0, 1.0))

            raw_pitch = float(profile["pitch_min"] + norm_val * (profile["pitch_max"] - profile["pitch_min"]))
            raw_midi = cls._hz_to_raw_midi(raw_pitch)

            # Harmonic scale quantization
            quant_midi = cls._quantize_to_scale(raw_midi, scale_mode, root_semitone)
            quant_hz = cls._midi_to_hz(quant_midi)
            note_name = cls._midi_to_name(quant_midi)

            tempo = float(profile["tempo_min"] + norm_val * (profile["tempo_max"] - profile["tempo_min"]))
            volume_db = float(-36.0 + norm_val * 30.0)  # -36 dB to -6 dB
            intensity = float(norm_val)
            rhythm_density = float(0.2 + norm_val * 0.8)
            duration_ms = float(60000.0 / tempo * 0.75)  # Note gate length

            parameters.append(
                SonificationDataPoint(
                    timestamp=p.timestamp,
                    original_value=p.value,
                    normalized_value=norm_val,
                    pitch_hz=round(quant_hz, 2),
                    midi_note=quant_midi,
                    musical_note=note_name,
                    volume_db=round(volume_db, 2),
                    tempo_bpm=round(tempo, 1),
                    rhythm_density=round(rhythm_density, 3),
                    intensity=round(intensity, 3),
                    duration_ms=round(duration_ms, 1),
                    profile_instrument=profile["instrument"],
                )
            )

        return SonificationSeries(
            category=category,
            sound_profile=profile["instrument"],
            mapping_description=profile["description"],
            scale_mode=scale_mode,
            musical_key=root_name,
            parameters=parameters,
            dynamic_range_min=val_min,
            dynamic_range_max=val_max,
        )
