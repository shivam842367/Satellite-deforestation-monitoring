"use client";

import { MapContainer, TileLayer, FeatureGroup } from "react-leaflet";
import { EditControl } from "react-leaflet-draw";
import { useState } from "react";
import "leaflet/dist/leaflet.css";
import "leaflet-draw/dist/leaflet.draw.css";
import L from "leaflet";

type Props = {
  onAOISelect: (coords: number[][][]) => void;
};

export default function MapAOIClient({ onAOISelect }: Props) {
  // ======================================
  // STATE: Past vs Present toggle
  // ======================================
  const [yearView, setYearView] = useState<"past" | "present">("present");
  const NDVI_PAST_TILE =
  "https://earthengine.googleapis.com/v1alpha/projects/earthengine-legacy/maps/NDVI_PAST/{z}/{x}/{y}";

  const NDVI_PRESENT_TILE =
  "https://earthengine.googleapis.com/v1alpha/projects/earthengine-legacy/maps/NDVI_PRESENT/{z}/{x}/{y}";


  // ======================================
  // TILE LAYER SWITCH (VISUAL ONLY)
  // ======================================
  const tileUrl =
    yearView === "past"
      ? "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      : "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png";

  // ======================================
  // AOI HANDLER
  // ======================================
  const handleCreated = (e: any) => {
    const layer = e.layer as L.Polygon;
    const latLngs = layer.getLatLngs()[0] as L.LatLng[];

    const coordinates = [
      latLngs.map((p) => [p.lng, p.lat]),
    ];

    onAOISelect(coordinates);
  };

  // ======================================
  // RENDER
  // ======================================
  return (
    <div style={{ position: "relative" }}>
      <MapContainer
        center={[26.9124, 75.7873]}
        zoom={11}
        style={{
          height: "420px",
          width: "100%",
          borderRadius: "14px",
          overflow: "hidden",
        }}
      >
        <TileLayer url={tileUrl} />

        <FeatureGroup>
          <EditControl
            position="topright"
            onCreated={handleCreated}
            draw={{
              rectangle: false,
              circle: false,
              circlemarker: false,
              marker: false,
              polyline: false,
            }}
          />
        </FeatureGroup>
      </MapContainer>

      {/* ======================================
          SLIDER UI — PAST vs PRESENT
      ====================================== */}
      <div
        className="map-slider"
        style={{
          position: "absolute",
          bottom: "12px",
          left: "50%",
          transform: "translateX(-50%)",
          width: "80%",
          background: "rgba(0,0,0,0.6)",
          padding: "0.6rem 1rem",
          borderRadius: "10px",
          backdropFilter: "blur(10px)",
        }}
      >
        <input
          type="range"
          min={0}
          max={1}
          step={1}
          value={yearView === "past" ? 0 : 1}
          onChange={(e) =>
            setYearView(e.target.value === "0" ? "past" : "present")
          }
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
          Viewing:{" "}
          <strong>
            {yearView === "past"
              ? "Past Satellite (Baseline)"
              : "Present Satellite (Current)"}
          </strong>
        </div>
      </div>
    </div>
  );
}
