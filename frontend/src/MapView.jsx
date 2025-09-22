import React, { useEffect, useRef, useState } from 'react';
import './MapView.css';
import { fetchData, predict, ingestFile } from './api';

export default function MapView() {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markersLayer = useRef(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [pred, setPred] = useState(null);
  const [form, setForm] = useState({ x_coord: '', y_coord: '', z_coord: '' });
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState(null);

  useEffect(() => {
    if (!mapRef.current || mapInstance.current) return;
    const L = window.L;
    // Initialize map, set a default view (center can be adjusted to your data)
    mapInstance.current = L.map(mapRef.current).setView([34.0, -6.8], 6);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(mapInstance.current);

    // LayerGroup for forage markers so we can refresh without duplicates
    markersLayer.current = L.layerGroup().addTo(mapInstance.current);

    // Load existing forages and add markers
    (async () => {
      try {
        await loadMarkers();
      } catch (e) {
        setError(String(e));
      }
    })();
  }, []);

  const loadMarkers = async () => {
    const L = window.L;
    const data = await fetchData();
    if (markersLayer.current) {
      markersLayer.current.clearLayers();
    }
    data.forEach((row) => {
      const lat = row.y_coord;
      const lng = row.x_coord;
      if (Number.isFinite(lat) && Number.isFinite(lng)) {
        L.marker([lat, lng])
          .bindPopup(
            `<b>Forage #${row.id}</b><br/>X: ${row.x_coord}<br/>Y: ${row.y_coord}<br/>Z: ${row.z_coord}<br/>Teneur: ${row.teneur}`
          )
          .addTo(markersLayer.current);
      }
    });
  };

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((s) => ({ ...s, [name]: value }));
  };

  const onFileChange = (e) => {
    setError('');
    setFile(e.target.files && e.target.files[0] ? e.target.files[0] : null);
  };

  const onUpload = async () => {
    if (!file) return;
    setError('');
    setUploading(true);
    try {
      await ingestFile(file);
      await loadMarkers();
    } catch (e) {
      setError(String(e));
    } finally {
      setUploading(false);
    }
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setPred(null);
    const x = parseFloat(form.x_coord);
    const y = parseFloat(form.y_coord);
    const z = parseFloat(form.z_coord);
    if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(z)) {
      setError('Please enter valid numeric values for X, Y, Z.');
      return;
    }
    try {
      setLoading(true);
      const res = await predict({ x_coord: x, y_coord: y, z_coord: z });
      setPred(res);
      if (mapInstance.current) {
        const L = window.L;
        const lat = y;
        const lng = x;
        const marker = L.marker([lat, lng]).addTo(mapInstance.current);
        marker.bindPopup(
          `<b>Predicted</b><br/>X: ${x}<br/>Y: ${y}<br/>Z: ${z}<br/><b>Teneur:</b> ${Number(res.predicted_teneur).toFixed(4)}`
        ).openPopup();
        mapInstance.current.setView([lat, lng], 10);
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="sidebar">
        <div className="header">
          <div className="title">Smart Mining Panel</div>
          <div className="subtitle">Visualize forages and predict teneur from coordinates.</div>
        </div>
        <form onSubmit={onSubmit} className="form card">
          <label>
            <span className="label">X</span>
            <input name="x_coord" value={form.x_coord} onChange={onChange} placeholder="e.g., 426218.951" />
          </label>
          <label>
            <span className="label">Y</span>
            <input name="y_coord" value={form.y_coord} onChange={onChange} placeholder="e.g., 5839036.034" />
          </label>
          <label>
            <span className="label">Z</span>
            <input name="z_coord" value={form.z_coord} onChange={onChange} placeholder="e.g., 8764.087675" />
          </label>
          <button type="submit" className="btn" disabled={loading}>{loading ? 'Predicting...' : 'Predict'}</button>
        </form>
        <div className="form card" style={{ marginTop: 12 }}>
          <label>
            <span className="label">Upload CSV</span>
            <input type="file" accept=".csv" onChange={onFileChange} />
          </label>
          <button className="btn" onClick={onUpload} disabled={uploading || !file}>
            {uploading ? 'Uploading...' : 'Upload & Ingest'}
          </button>
        </div>
        {pred && (
          <div className="result card">
            <div className="result-title">Prediction</div>
            <div className="result-value">{Number(pred.predicted_teneur).toFixed(6)}</div>
            {pred.model && <div className="result-model">Model: {pred.model}</div>}
          </div>
        )}
        {error && <div className="error card">{error}</div>}
        <div className="hint">Use the form to add a predicted point. Existing forages are displayed on the map.</div>
      </div>
      <div className="map" ref={mapRef} />
    </div>
  );
}
