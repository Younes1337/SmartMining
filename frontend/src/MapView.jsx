import React, { useEffect, useRef, useState } from 'react';
import './MapView.css';
import { fetchData, predict, ingestFile } from './api';
import { utmToLatLng, latLngToUtm } from './utils/coordinateUtils';
import logo from './logo.svg';

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
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (!mapRef.current || mapInstance.current) return;
    const L = window.L;
    // Initialize map with a default view for Northwest Canada
    // Convert UTM coordinates to lat/lng for the initial view
    const [initialLng, initialLat] = utmToLatLng(426000, 5839000);
    mapInstance.current = L.map(mapRef.current).setView([initialLat, initialLng], 10);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(mapInstance.current);

    // LayerGroup for forage markers so we can refresh without duplicates
    markersLayer.current = L.layerGroup().addTo(mapInstance.current);

    // Allow clicking on the map to autofill X/Y coordinates
    mapInstance.current.on('click', (e) => {
      const { lat, lng } = e.latlng;
      // Convert the clicked lat/lng back to UTM for the form
      const { easting, northing } = latLngToUtm(lat, lng);
      setForm((s) => ({
        ...s,
        x_coord: String(easting),
        y_coord: String(northing),
      }));
    });

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
      const easting = parseFloat(row.x_coord);
      const northing = parseFloat(row.y_coord);
      
      if (Number.isFinite(easting) && Number.isFinite(northing)) {
        // Convert UTM to lat/lng for display on the map
        const [lng, lat] = utmToLatLng(easting, northing);
        
        if (lat !== null && lng !== null) {
          L.marker([lat, lng])
            .bindPopup(
              `<b>Forage #${row.id}</b><br/>
               X (Easting): ${easting.toFixed(2)}<br/>
               Y (Northing): ${northing.toFixed(2)}<br/>
               Z: ${row.z_coord}<br/>
               Teneur: ${row.teneur}`
            )
            .addTo(markersLayer.current);
        }
      }
    });
  };

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((s) => ({ ...s, [name]: value }));
  };

  const onFileChange = (e) => {
    setError('');
    setSuccess('');
    setFile(e.target.files && e.target.files[0] ? e.target.files[0] : null);
  };

  const onUpload = async () => {
    if (!file) return;
    setError('');
    setSuccess('');
    setUploading(true);
    try {
      const res = await ingestFile(file);
      if (res && typeof res.rows_inserted === 'number') {
        setSuccess(`${res.rows_inserted} points ingested successfully`);
      }
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
        // Convert UTM to lat/lng for display on the map
        const [lng, lat] = utmToLatLng(x, y);
        
        if (lat !== null && lng !== null) {
          const marker = L.marker([lat, lng]).addTo(mapInstance.current);
          marker.bindPopup(
            `<b>Predicted</b><br/>
             X (Easting): ${x.toFixed(2)}<br/>
             Y (Northing): ${y.toFixed(2)}<br/>
             Z: ${z}<br/>
             <b>Teneur:</b> ${Number(res.predicted_teneur).toFixed(4)}`
          ).openPopup();
          mapInstance.current.setView([lat, lng], 10);
        }
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
          <div className="brand">
            <img src={logo} className="brand-logo" alt="Smart Mining Panel logo" />
            <div className="brand-text">
              <div className="title">Smart Mining Panel</div>
              <div className="subtitle">Visualize forages and predict teneur from coordinates.</div>
            </div>
          </div>
        </div>
        <form onSubmit={onSubmit} className="form card">
          <label>
            <span className="label">X</span>
            <input name="x_coord" value={form.x_coord} onChange={onChange} placeholder="e.g., 426218.951 (Easting)" />
          </label>
          <label>
            <span className="label">Y</span>
            <input name="y_coord" value={form.y_coord} onChange={onChange} placeholder="e.g., 5839036.034 (Northing)" />
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
        {success && <div className="card" style={{ background: '#e6ffed', border: '1px solid #b7eb8f', color: '#135200' }}>{success}</div>}
        {error && <div className="error card">{error}</div>}
        <div className="hint">Use the form to add a predicted point. Existing forages are displayed on the map.</div>
      </div>
      <div className="map" ref={mapRef} />
    </div>
  );
}
