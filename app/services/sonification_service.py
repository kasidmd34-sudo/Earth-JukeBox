"""Deterministic Sonification Parameter Engine for Earth Jukebox.
Maps continuous physical units to synthesizer parameters (MIDI, Hz, tempo, intensity, musical scale, chords).
"""
import numpy as np
from typing import List, Dict, Any
from app.schemas.sonification import SonificationSeries, SonificationDataPoint
from app.schemas.responses import TimeSeriesPoint

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

SCALE_MODES: Dict[str, List[int]] = {
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "pentatonic_major": [0, 2, 4, 7, 9],
}

CATEGORY_SOUND_PROFILES: Dict[str, Dict[str, Any]] = {
    "temperature": {
        "instrument": "Warm Analog Sine & Tonal Brightness",
        "description": "Thermal energy maps directly to pitch brightness and warm analog harmonics.",
        "pitch_min": 110.0,
        "pitch_max": 880.0,
        "tempo_min": 60.0,
        "tempo_max": 120.0,
        "scale_mode": "pentatonic_minor",
        "root_semitone": 9,
    },
    "rain": {
        "instrument": "Granular Percussion & Hydro-Acoustic Drops",
        "description": "Precipitation intensity drives rhythmic droplet density and Dorian voicings.",
        "pitch_min": 150.0,
        "pitch_max": 600.0,
        "tempo_min": 50.0,
        "tempo_max": 160.0,
        "scale_mode": "dorian",
        "root_semitone": 2,
    },
    "wind": {
        "instrument": "Resonant Noise Generator & Modulated Swell",
        "description": "Wind velocity modulates bandpass resonance, tempo cadence, and airy swells.",
        "pitch_min": 80.0,
        "pitch_max": 400.0,
        "tempo_min": 40.0,
        "tempo_max": 140.0,
        "scale_mode": "dorian",
        "root_semitone": 4,
    },
    "fires": {
        "instrument": "Staccato Pulse & FM Thermal Crackle",
        "description": "Fire Radiative Power drives percussive staccato pulses and FM harmonic bite.",
        "pitch_min": 60.0,
        "pitch_max": 350.0,
        "tempo_min": 80.0,
        "tempo_max": 180.0,
        "scale_mode": "pentatonic_minor",
        "root_semitone": 7,
    },
    "vegetation": {
        "instrument": "Harmonic Chords & Biophilic Drone",
        "description": "Biophysical radiation/vegetation flux shapes warm Lydian harmonic pads.",
        "pitch_min": 130.0,
        "pitch_max": 520.0,
        "tempo_min": 50.0,
        "tempo_max": 90.0,
        "scale_mode": "lydian",
        "root_semitone": 5,
    },
    "ocean": {
        "instrument": "Deep Sub-bass & Flowing Continuous Pads",
        "description": "Ocean thermal shifts produce deep sub-bass swells and major pentatonic pads.",
        "pitch_min": 55.0,
        "pitch_max": 220.0,
        "tempo_min": 40.0,
        "tempo_max": 80.0,
        "scale_mode": "pentatonic_major",
        "root_semitone": 0,
    },
    "ice": {
        "instrument": "Crystalline Sparse Chimes",
        "description": "Polar cryosphere values map to high-register crystalline bell harmonics.",
        "pitch_min": 440.0,
        "pitch_max": 1760.0,
        "tempo_min": 30.0,
        "tempo_max": 70.0,
        "scale_mode": "pentatonic_minor",
        "root_semitone": 11,
    },
    "storms": {
        "instrument": "Dynamic Atmospheric Rumble & Clustered Brass",
        "description": "Storm precipitation surges trigger deep atmospheric rumbles and dynamic chords.",
        "pitch_min": 65.0,
        "pitch_max": 500.0,
        "tempo_min": 90.0,
        "tempo_max": 190.0,
        "scale_mode": "pentatonic_minor",
        "root_semitone": 0,
    },
}


class SonificationService:
    @staticmethod
    def sample_marker_indices(total_points: int, max_markers: int = 12) -> List[int]:
        """Select evenly spaced, sorted unique indices for A-Z chart/PDF cross-referencing."""
        if total_points <= 0:
            return []
        count = min(max_markers, total_points)
        return sorted(set(np.linspace(0, total_points - 1, count, dtype=int).tolist()))

    @staticmethod
    def _hz_to_raw_midi(hz: float) -> float:
        if hz <= 0:
            return 0.0
        return float(69 + 12 * np.log2(hz / 440.0))

    @staticmethod
    def _quantize_to_scale(raw_midi: float, scale_mode: str, root_semitone: int = 9) -> int:
        intervals = SCALE_MODES.get(scale_mode, SCALE_MODES["pentatonic_minor"])
        int_midi = int(np.clip(np.round(raw_midi), 0, 127))
        octave = int_midi // 12
        pitch_class = int_midi % 12
        rel = (pitch_class - root_semitone) % 12
        closest_rel = min(intervals, key=lambda x: min(abs(x - rel), 12 - abs(x - rel)))
        quantized_midi = octave * 12 + ((root_semitone + closest_rel) % 12)
        return int(np.clip(quantized_midi, 0, 127))

    @staticmethod
    def _midi_to_hz(midi: int) -> float:
        return float(440.0 * (2.0 ** ((midi - 69) / 12.0)))

    @staticmethod
    def _midi_to_name(midi: int) -> str:
        octave = (midi // 12) - 1
        name = NOTE_NAMES[midi % 12]
        return f"{name}{octave}"

    @staticmethod
    def _excel_label(index: int) -> str:
        """Return A..Z, AA..AZ labels deterministically."""
        label = ""
        n = index
        while True:
            label = chr(65 + (n % 26)) + label
            n = n // 26 - 1
            if n < 0:
                break
        return label

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
                chord_hierarchy={},
            )

        values = [p.value for p in series]
        val_min = min(values)
        val_max = max(values)
        span = val_max - val_min if val_max > val_min else 1.0

        parameters: List[SonificationDataPoint] = []
        tiers: Dict[str, Dict[str, Any]] = {
            "high": {"label": "Peak Register (High 67-100%)", "count": 0, "chords": [], "values": []},
            "mid": {"label": "Mid Register (Moderate 33-67%)", "count": 0, "chords": [], "values": []},
            "low": {"label": "Base Register (Low 0-33%)", "count": 0, "chords": [], "values": []},
        }

        for idx, p in enumerate(series):
            norm_val = float(np.clip((p.value - val_min) / span, 0.0, 1.0))
            raw_pitch = float(profile["pitch_min"] + norm_val * (profile["pitch_max"] - profile["pitch_min"]))
            raw_midi = cls._hz_to_raw_midi(raw_pitch)

            quant_midi = cls._quantize_to_scale(raw_midi, scale_mode, root_semitone)
            quant_hz = cls._midi_to_hz(quant_midi)
            note_name = cls._midi_to_name(quant_midi)

            is_minor = scale_mode in ("pentatonic_minor", "dorian")
            chord_intervals = [0, 3, 7] if is_minor else [0, 4, 7]
            chord_midis = [int(np.clip(quant_midi + interval, 0, 127)) for interval in chord_intervals]
            chord_notes = [cls._midi_to_name(note) for note in chord_midis]
            chord_name = f"{chord_notes[0]} {'minor' if is_minor else 'major'}"

            pitch_direction = "initial"
            if parameters:
                prev_hz = parameters[-1].pitch_hz
                if quant_hz > prev_hz:
                    pitch_direction = "higher"
                elif quant_hz < prev_hz:
                    pitch_direction = "lower"
                else:
                    pitch_direction = "unchanged"

            pitch_tier = "high" if norm_val >= 0.67 else ("mid" if norm_val >= 0.33 else "low")
            tiers[pitch_tier]["count"] += 1
            tiers[pitch_tier]["values"].append(p.value)
            if chord_name not in tiers[pitch_tier]["chords"]:
                tiers[pitch_tier]["chords"].append(chord_name)

            tempo = float(profile["tempo_min"] + norm_val * (profile["tempo_max"] - profile["tempo_min"]))
            volume_db = float(-36.0 + norm_val * 30.0)
            intensity = float(norm_val)
            rhythm_density = float(0.2 + norm_val * 0.8)
            duration_ms = float(60000.0 / tempo * 0.75)

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
                    event_label=cls._excel_label(idx),
                    chord_name=chord_name,
                    chord_notes=chord_notes,
                    chord_midi=chord_midis,
                    chord_frequencies_hz=[round(cls._midi_to_hz(note), 2) for note in chord_midis],
                    pitch_direction=pitch_direction,
                    pitch_tier=pitch_tier,
                )
            )

        formatted_tiers = {}
        for key in ("high", "mid", "low"):
            vals = tiers[key]["values"]
            formatted_tiers[key] = {
                "label": tiers[key]["label"],
                "event_count": tiers[key]["count"],
                "distinct_chords": tiers[key]["chords"],
                "value_min": round(min(vals), 3) if vals else None,
                "value_max": round(max(vals), 3) if vals else None,
            }

        return SonificationSeries(
            category=category,
            sound_profile=profile["instrument"],
            mapping_description=profile["description"],
            scale_mode=scale_mode,
            musical_key=root_name,
            parameters=parameters,
            dynamic_range_min=val_min,
            dynamic_range_max=val_max,
            chord_hierarchy={
                "level_1_tonal_center": f"Key of {root_name} ({scale_mode.replace('_', ' ').title()})",
                "level_2_instrument_voice": profile["instrument"],
                "level_3_register_tiers": formatted_tiers,
            },
        )