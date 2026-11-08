"""Sonification deterministic normalization and bounds tests."""
from app.services.sonification_service import SonificationService
from app.schemas.responses import TimeSeriesPoint


def test_sonification_mapping_bounds():
    points = [
        TimeSeriesPoint(timestamp="2023-01-01", value=10.0, unit="C"),
        TimeSeriesPoint(timestamp="2023-02-01", value=20.0, unit="C"),
        TimeSeriesPoint(timestamp="2023-03-01", value=30.0, unit="C"),
    ]
    sonif = SonificationService.generate_sonification_series("temperature", points)
    assert len(sonif.parameters) == 3

    # Check normalized values span [0.0, 1.0]
    norm_values = [p.normalized_value for p in sonif.parameters]
    assert norm_values[0] == 0.0
    assert norm_values[1] == 0.5
    assert norm_values[2] == 1.0

    # Check bounds
    for p in sonif.parameters:
        assert 20.0 <= p.pitch_hz <= 20000.0
        assert 0 <= p.midi_note <= 127
        assert -60.0 <= p.volume_db <= 0.0
        assert 30.0 <= p.tempo_bpm <= 240.0
        assert 0.0 <= p.intensity <= 1.0


def test_empty_sonification():
    sonif = SonificationService.generate_sonification_series("fires", [])
    assert len(sonif.parameters) == 0
    assert sonif.category == "fires"


def test_single_point_sonification():
    points = [TimeSeriesPoint(timestamp="2023-01-01", value=25.0, unit="C")]
    sonif = SonificationService.generate_sonification_series("ocean", points)
    assert len(sonif.parameters) == 1
    assert sonif.parameters[0].normalized_value == 0.0


def test_all_eight_module_profiles():
    categories = ["temperature", "rain", "wind", "fires", "ocean", "ice", "storms", "vegetation"]
    dummy = [
        TimeSeriesPoint(timestamp="2023-01-01", value=10.0, unit="U"),
        TimeSeriesPoint(timestamp="2023-02-01", value=20.0, unit="U"),
    ]
    for cat in categories:
        s = SonificationService.generate_sonification_series(cat, dummy)
        assert s.category == cat
        assert len(s.parameters) == 2
        assert s.sound_profile != ""
