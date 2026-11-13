"""KNN regression FROM SCRATCH and honest leave-one-out evaluation."""
import numpy as np

FEATURES = ["min_diario", "max_diario"]


def knn_predict(X_train, y_train, X_query, k=3):
    """Euclidean KNN regressor, implemented without sklearn's prediction classes."""
    X_train = np.asarray(X_train, dtype=float)
    y_train = np.asarray(y_train, dtype=float)
    X_query = np.atleast_2d(np.asarray(X_query, dtype=float))
    if len(X_train) == 0 or len(X_train) != len(y_train):
        raise ValueError("Se requieren datos de entrenamiento válidos")
    scale = np.std(X_train, axis=0)
    scale[scale == 0] = 1.0
    distances = np.sqrt(np.sum(((X_query[:, None, :] - X_train[None, :, :]) / scale) ** 2, axis=2))
    nearest = np.argsort(distances, axis=1)[:, :min(k, len(y_train))]
    return np.mean(y_train[nearest], axis=1)


def evaluate_loocv(df, k=3):
    """Compare KNN vs train-only global-mean baseline without leakage."""
    X = df[FEATURES].to_numpy(dtype=float)
    y = df["media_diaria"].to_numpy(dtype=float)
    if len(y) < 5:
        raise ValueError("Se requieren al menos cinco estaciones")
    predictions, baselines = [], []
    for i in range(len(y)):
        mask = np.arange(len(y)) != i
        predictions.append(float(knn_predict(X[mask], y[mask], [X[i]], k)[0]))
        baselines.append(float(y[mask].mean()))
    predictions, baselines = np.array(predictions), np.array(baselines)
    return {
        "mae_knn": float(np.mean(np.abs(y - predictions))),
        "mae_baseline": float(np.mean(np.abs(y - baselines))),
        "predictions": predictions,
        "baseline_predictions": baselines,
        "observed": y,
    }


def estimate_station(df, station, k=3):
    """Hold the selected station out, then estimate its monthly mean from extrema."""
    sample = df.loc[df.estacion == station]
    if len(sample) != 1:
        raise ValueError("Selecciona una estación existente")
    rest = df.loc[df.estacion != station]
    prediction = knn_predict(rest[FEATURES].values, rest.media_diaria.values, sample[FEATURES].values, k)
    return float(prediction[0])
