import numpy as np
from src.data import load_data
from src.model import evaluate_loocv, knn_predict, estimate_station
from src.tools import get_pm25, search_environmental_docs, estimate_monthly_mean


def test_dataset():
    df = load_data()
    assert len(df) == 23
    assert df['periodo'].nunique() == 1
    assert df['media_diaria'].between(df['min_diario'], df['max_diario']).all()


def test_knn_manual():
    p = knn_predict([[0, 0], [1, 1], [4, 4]], [1, 3, 10], [[0, 0]], k=1)
    assert np.isclose(p[0], 1)


def test_evaluation():
    df = load_data()
    result = evaluate_loocv(df)
    assert result['mae_knn'] >= 0
    assert result['mae_baseline'] >= 0
    assert np.isfinite(estimate_station(df, 'CEN-TRAF'))


def test_tools():
    assert get_pm25('CEN-TRAF')['promedio_mensual_pm25'] == 25.6
    assert 'error' in get_pm25('DESCONOCIDA')
    assert 'estimacion_media_mensual_pm25' in estimate_monthly_mean('CEN-TRAF')
    assert len(search_environmental_docs('PM2.5 contaminación')['documentos']) >= 1
