"use client";

import { MapContainer, TileLayer, GeoJSON } from "react-leaflet";
import "leaflet/dist/leaflet.css";

type Props = {
  aoi: number[][][];
  tileUrl: string;
};

export default function NDVIDiffMap({ aoi, tileUrl }: Props) {
  const center = [
    aoi[0][0][1], // lat
    aoi[0][0][0], // lng
  ] as [number, number];

  const geojsonAOI = {
    type: "Feature",
    geometry: {
      type: "Polygon",
      coordinates: aoi,
    },
  };

  return (
    <div style={{ marginTop: "2rem" }}>
      <h3 style={{ marginBottom: "0.75rem" }}>
        🗺️ NDVI Difference Map (Present − Past)
      </h3>

      <MapContainer
        center={center}
        zoom={12}
        style={{
          height: "420px",
          width: "100%",
          borderRadius: "12px",
        }}
      >
        {/* Base Map */}
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* NDVI Difference Layer */}
        <TileLayer
          url={tileUrl}
          opacity={0.75}
        />

        {/* AOI Outline */}
        <GeoJSON
          data={geojsonAOI as any}
          style={{
            color: "#000",
            weight: 2,
            fillOpacity: 0,
          }}
        />
      </MapContainer>

      {/* Legend */}
      <div
        style={{
          marginTop: "0.75rem",
          fontSize: "0.85rem",
          display: "flex",
          gap: "1.5rem",
        }}
      >
        <span style={{ color: "#27ae60" }}>⬤ NDVI Increase</span>
        <span style={{ color: "#c0392b" }}>⬤ NDVI Decrease</span>
      </div>
    </div>
  );
}
