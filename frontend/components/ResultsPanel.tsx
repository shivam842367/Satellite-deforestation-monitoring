"use client";

import { useMemo } from "react";
import NDVIDiffMap from "./NDVIDiffMap";

/* =========================================================
   TYPES
========================================================= */
type SatelliteComparison = {
  past_year: number;
  present_year: number;
  past_cover_ha: number;
  present_cover_ha: number;
  change_ha: number;
};

type DroneData = {
  vegetation_area_ha: number;
  total_area_ha: number;
  vegetation_percentage: number;
  mean_ndvi: number;
  error?: string;
};

type ResultPayload = {
  satellite_comparison?: SatelliteComparison;
  drone_data?: DroneData;
  ndvi_difference?: {
    tile_url: string;
  };
};

type ResultsPanelProps = {
  result: ResultPayload;
  aoi: number[][][];
};

/* =========================================================
   RESULTS PANEL
========================================================= */
export default function ResultsPanel({ result, aoi }: ResultsPanelProps) {
  if (!result?.satellite_comparison) return null;

  const {
    past_year,
    present_year,
    past_cover_ha,
    present_cover_ha,
    change_ha,
  } = result.satellite_comparison;

  /* =======================================================
     DERIVED VALUES
  ======================================================= */
  const ndviTileUrl = result.ndvi_difference?.tile_url ?? null;

  const percentageChange = useMemo(() => {
    if (past_cover_ha <= 0) return 0;
    return ((present_cover_ha - past_cover_ha) / past_cover_ha) * 100;
  }, [past_cover_ha, present_cover_ha]);

  const isGain = present_cover_ha > past_cover_ha;
  const isLoss = present_cover_ha < past_cover_ha;
  const absChange = Math.abs(change_ha);

  const MAX_VISUAL_PERCENT = 5;
  const visualPercent = Math.min(
    Math.abs(percentageChange),
    MAX_VISUAL_PERCENT
  );

  const droneData = result.drone_data ?? null;
  const satellitePresent = present_cover_ha;
  const droneVegetation = droneData?.vegetation_area_ha ?? null;

  const droneDiffPct =
    droneVegetation !== null && satellitePresent > 0
      ? ((droneVegetation - satellitePresent) / satellitePresent) * 100
      : null;

  const aoiPoints = aoi?.[0]?.length ?? 0;

  const COLORS = {
    gain: "#27ae60",
    loss: "#c0392b",
    neutral: "#7f8c8d",
  };

  /* =======================================================
     RENDER
  ======================================================= */
  return (
    <section
      style={{
        marginTop: "2rem",
        padding: "1.75rem",
        borderRadius: "16px",
        background: "#fff",
        boxShadow: "0 12px 32px rgba(0,0,0,0.12)",
      }}
    >
      <h2 style={{ marginBottom: "1.25rem" }}>📊 Analysis Results</h2>

      <p style={{ fontSize: "0.8rem", color: "#666" }}>
        AOI Points: {aoiPoints}
      </p>

      {/* ================= STATS ================= */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gap: "1rem",
          marginBottom: "1.75rem",
        }}
      >
        <StatBox
          label={`Past Vegetation (${past_year})`}
          value={`${past_cover_ha.toFixed(2)} ha`}
          color={COLORS.neutral}
        />

        <StatBox
          label={`Present Vegetation (${present_year})`}
          value={`${present_cover_ha.toFixed(2)} ha`}
          color={
            isGain
              ? COLORS.gain
              : isLoss
              ? COLORS.loss
              : COLORS.neutral
          }
        />

        <StatBox
          label="Percentage Change"
          value={`${percentageChange.toFixed(2)}%`}
          color={
            isGain
              ? COLORS.gain
              : isLoss
              ? COLORS.loss
              : COLORS.neutral
          }
        />
      </div>

      {/* ================= GAIN VS LOSS ================= */}
      <div>
        <h4 style={{ marginBottom: "0.75rem" }}>
          🌿 Vegetation Gain vs Loss
        </h4>

        <div
          style={{
            position: "relative",
            height: "18px",
            background: "#ecf0f1",
            borderRadius: "999px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              position: "absolute",
              left: "50%",
              top: 0,
              bottom: 0,
              width: "2px",
              background: "#bbb",
            }}
          />

          {isGain && (
            <div
              style={{
                position: "absolute",
                left: "50%",
                height: "100%",
                width: `${(visualPercent / MAX_VISUAL_PERCENT) * 50}%`,
                background: COLORS.gain,
              }}
            />
          )}

          {isLoss && (
            <div
              style={{
                position: "absolute",
                right: "50%",
                height: "100%",
                width: `${(visualPercent / MAX_VISUAL_PERCENT) * 50}%`,
                background: COLORS.loss,
              }}
            />
          )}
        </div>

        <div
          style={{
            marginTop: "0.5rem",
            fontSize: "0.85rem",
            fontWeight: 600,
            color: isGain
              ? COLORS.gain
              : isLoss
              ? COLORS.loss
              : COLORS.neutral,
          }}
        >
          {change_ha === 0
            ? "No detectable change"
            : isGain
            ? `Gain of ${absChange.toFixed(2)} ha`
            : `Loss of ${absChange.toFixed(2)} ha`}
        </div>
      </div>

      {/* ================= DRONE ANALYSIS ================= */}
      {droneData && (
        <div style={{ marginTop: "2rem" }}>
          <h4 style={{ marginBottom: "0.75rem" }}>🚁 Drone Analysis</h4>

          <div
            style={{
              background: "#f4f4f4",
              padding: "1rem",
              borderRadius: "8px",
              fontSize: "0.85rem",
            }}
          >
            <div>Vegetation Area: {droneData.vegetation_area_ha} ha</div>
            <div>Total Area: {droneData.total_area_ha} ha</div>
            <div>Vegetation %: {droneData.vegetation_percentage}%</div>
            <div>Mean NDVI: {droneData.mean_ndvi}</div>
          </div>
        </div>
      )}

      {/* ================= DRONE vs SATELLITE ================= */}
      {droneVegetation !== null && (
        <div style={{ marginTop: "2rem" }}>
          <h4 style={{ marginBottom: "0.75rem" }}>
            🚁 Drone vs 🛰 Satellite
          </h4>

          <div>
            Difference:{" "}
            <strong
              style={{
                color:
                  droneDiffPct !== null && droneDiffPct >= 0
                    ? COLORS.gain
                    : COLORS.loss,
              }}
            >
              {droneDiffPct?.toFixed(2)}%
            </strong>
          </div>
        </div>
      )}

      {/* ================= NDVI DIFFERENCE MAP ================= */}
      {ndviTileUrl && (
        <NDVIDiffMap aoi={aoi} tileUrl={ndviTileUrl} />
      )}
    </section>
  );
}

/* =========================================================
   STAT BOX
========================================================= */
function StatBox({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div
      style={{
        padding: "1rem",
        borderRadius: "12px",
        background: "#fafafa",
        border: "1px solid #ddd",
      }}
    >
      <div style={{ fontSize: "0.8rem", color: "#666" }}>{label}</div>
      <div style={{ fontSize: "1.4rem", fontWeight: 700, color }}>
        {value}
      </div>
    </div>
  );
}
