"use client";

import dynamic from "next/dynamic";
import { useMemo, useState } from "react";
import "leaflet/dist/leaflet.css";

/* =========================================================
   DYNAMIC IMPORTS (SSR SAFE)
========================================================= */
const MapContainer = dynamic(
  () => import("react-leaflet").then((m) => m.MapContainer),
  { ssr: false }
);

const TileLayer = dynamic(
  () => import("react-leaflet").then((m) => m.TileLayer),
  { ssr: false }
);

const GeoJSON = dynamic(
  () => import("react-leaflet").then((m) => m.GeoJSON),
  { ssr: false }
);

/* =========================================================
   RESULTS PANEL
========================================================= */
export default function ResultsPanel({ result, aoi }: any) {

  /* =========================================================
     STATE
  ========================================================= */
  const [slider, setSlider] = useState<number>(50);
  const [mode, setMode] = useState<"ndvi" | "urban">("ndvi");

  /* =========================================================
     AOI GEOJSON
  ========================================================= */
  const aoiGeoJSON = useMemo(() => {
    if (!aoi) return null;
    return {
      type: "Feature",
      geometry: {
        type: "Polygon",
        coordinates: aoi,
      },
    };
  }, [aoi]);

  /* =========================================================
     MAP CENTER
  ========================================================= */
  const center = useMemo(() => {
    if (!aoi || !aoi[0]?.length) return [0, 0];
    const [lng, lat] = aoi[0][0];
    return [lat, lng];
  }, [aoi]);

  /* =========================================================
     NDVI TILE SOURCES (VISUAL)
  ========================================================= */
  const NDVI_PAST =
  "https://tiles.maps.eox.at/wmts/1.0.0/sentinel2-ndvi-2016/default/g/{z}/{y}/{x}.jpg";

  const NDVI_PRESENT =
  "https://tiles.maps.eox.at/wmts/1.0.0/sentinel2-ndvi-2024/default/g/{z}/{y}/{x}.jpg";


  const URBAN =
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

  /* =========================================================
     RENDER
  ========================================================= */
  return (
    <section
      style={{
        marginTop: "2rem",
        padding: "1.5rem",
        background: "#f9fafb",
        borderRadius: "8px",
      }}
    >
      <h2>📊 Analysis Results</h2>

      {/* ================= METRICS ================= */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "1rem",
          marginBottom: "1.5rem",
        }}
      >
        <Metric
          label="Past Vegetation Cover"
          value={`${result.satellite_comparison.past_cover_ha} ha`}
          color="#27ae60"
        />
        <Metric
          label="Present Vegetation Cover"
          value={`${result.satellite_comparison.present_cover_ha} ha`}
          color="#e67e22"
        />
      </div>

      {/* ================= MODE TOGGLE ================= */}
      <div style={{ marginBottom: "0.75rem" }}>
        <button onClick={() => setMode("ndvi")}>🌿 NDVI Mode</button>{" "}
        <button onClick={() => setMode("urban")}>🏙️ Urban Mode</button>
      </div>

      {/* ================= MAP ================= */}
      <div
        style={{
          height: "460px",
          borderRadius: "12px",
          overflow: "hidden",
          position: "relative",
        }}
      >
        <MapContainer
          key={`${mode}-${result?.satellite_comparison?.past_cover_ha}-${result?.satellite_comparison?.present_cover_ha}`}
          center={center}
          zoom={12}
          style={{ height: "100%", width: "100%" }}
        >
          {/* BASE LAYER */}
          <TileLayer url={URBAN} />

          {/* NDVI PAST */}
          {mode === "ndvi" && (
            <TileLayer
              url={NDVI_PAST}
              opacity={slider / 100}
            />
          )}

          {/* NDVI PRESENT */}
          {mode === "ndvi" && (
            <TileLayer
              url={NDVI_PRESENT}
              opacity={(100 - slider) / 100}
            />
          )}

          {/* AOI */}
          {aoiGeoJSON && (
            <GeoJSON
              data={aoiGeoJSON}
              style={{
                color: "#00ff88",
                weight: 2,
                fillOpacity: 0.15,
              }}
            />
          )}
        </MapContainer>

        {/* ================= SLIDER ================= */}
        {mode === "ndvi" && (
          <div
            style={{
              position: "absolute",
              bottom: "12px",
              left: "50%",
              transform: "translateX(-50%)",
              width: "80%",
              background: "rgba(0,0,0,0.65)",
              padding: "0.75rem 1rem",
              borderRadius: "10px",
              backdropFilter: "blur(10px)",
            }}
          >
            <input
              type="range"
              min={0}
              max={100}
              value={slider}
              onChange={(e) => setSlider(Number(e.target.value))}
              style={{ width: "100%" }}
            />
            <div
              style={{
                textAlign: "center",
                marginTop: "0.4rem",
                fontSize: "0.85rem",
                color: "#fff",
              }}
            >
              Past ⟷ Present NDVI
            </div>
          </div>
        )}
      </div>

      {/* ================= LEGEND ================= */}
      {mode === "ndvi" && (
        <div style={{ marginTop: "1rem", fontSize: "0.85rem" }}>
          <strong>NDVI Legend:</strong>{" "}
          <span style={{ color: "#7f0000" }}>Low</span> →{" "}
          <span style={{ color: "#00ff00" }}>High</span>
        </div>
      )}
    </section>
  );
}

/* =========================================================
   METRIC
========================================================= */
function Metric({ label, value, color }: any) {
  return (
    <div
      style={{
        padding: "1rem",
        background: "#fff",
        borderRadius: "6px",
        border: "1px solid #ddd",
      }}
    >
      <div style={{ fontSize: "0.85rem", color: "#666" }}>
        {label}
      </div>
      <div style={{ fontSize: "1.6rem", fontWeight: 700, color }}>
        {value}
      </div>
    </div>
  );
}
