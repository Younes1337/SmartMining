# Models

Pretrained scikit-learn artifacts used by the backend prediction pipeline.

- Contents:
  - `poly_transform.pkl` — PolynomialFeatures transformer.
  - `scaler.pkl` — StandardScaler fitted to training data.
  - `pca_transform.pkl` — PCA transformer for dimensionality reduction.
  - `knn_model.pkl` — KNeighborsRegressor for predicting `teneur`.

## Notes
- The backend loads these files at startup. If any are missing or incompatible, `GET /model/info` will report the status and `POST /predict` will be unavailable.
- Keep versions of scikit-learn compatible with the artifacts to avoid unpickle warnings.
