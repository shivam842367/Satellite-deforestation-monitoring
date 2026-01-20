"use client";

import { MapContainer, TileLayer, FeatureGroup, Polygon } from "react-leaflet";
import { EditControl } from "react-leaflet-draw";
import { useState } from "react";

interface MapAOIProps {
  onAOIChange: (coords: any) => void;
  sliderValue: number; // 0–100
}

export default function MapAOIClient({ onAOIChange, sliderValue }: MapAOIProps) {
  const [polygon, setPolygon] = useState<any>(null);

  function handleCreate(e: any) {
    const layer = e.layer;
    const latlngs = layer.getLatLngs()[0].map((p: any) => [
      p.lng,
      p.lat,
    ]);
    const geojson = [[[...latlngs, latlngs[0]]]];
    setPolygon(geojson);
    onAOIChange(geojson);
  }

  function handleDelete() {
    setPolygon(null);
    onAOIChange(null);
  }

  return (
    <div style={{ height: "420px", position: "relative" }}>
      <MapContainer center={[26.8, 81.03]} zoom={12} style={{ height: "100%" }}>
        {/* PRESENT (Sentinel / ESRI) */}
        <TileLayer
          attribution="© Esri"
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        />

        {/* PAST (Landsat 8 – clipped) */}
        <TileLayer
          attribution="© Landsat 8"
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Landsat8_Views/ImageServer/tile/{z}/{y}/{x}"
          className="past-layer"
        />

        <FeatureGroup>
          <EditControl
            position="topright"
            onCreated={handleCreate}
            onDeleted={handleDelete}
            draw={{
              rectangle: false,
              circle: false,
              circlemarker: false,
              marker: false,
              polyline: false,
            }}
          />
        </FeatureGroup>

        {polygon && (
          <Polygon
            positions={polygon[0].map((c: any) => [c[1], c[0]])}
            pathOptions={{ color: "yellow", weight: 2 }}
          />
        )}
      </MapContainer>

      {/* Slider */}
      <input
        type="range"
        min={0}
        max={100}
        value={sliderValue}
        readOnly
        className="map-slider"
      />
    </div>
  );
}
