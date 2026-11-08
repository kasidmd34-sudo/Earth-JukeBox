"""Direct model class test."""
import pandas as pd
from app.models.time_series_models import ValidatedTimeSeriesModel

def test_model_artifact_save_load(tmp_path):
    dates = pd.date_range("2020-01-01", periods=36, freq="MS")
    df = pd.DataFrame({
        "timestamp": [d.strftime("%Y-%m-%d") for d in dates],
        "value": [15.0 + (i % 6) for i in range(36)]
    })
    model = ValidatedTimeSeriesModel("test_save_load")
    model.fit(df, "value")
    
    file_path = tmp_path / "model.joblib"
    model.save(str(file_path))
    
    loaded = ValidatedTimeSeriesModel("loaded")
    loaded.load(str(file_path))
    assert loaded.is_trained is True