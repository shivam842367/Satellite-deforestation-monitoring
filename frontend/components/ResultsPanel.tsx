"use client";

import { useMemo } from "react";

/* =========================================================
   RESULTS PANEL — NO MAPS, NO TILES
========================================================= */
export default function ResultsPanel({ result }: { result: any }) {
  if (!result || !result.satellite_comparison) return null;

  const {
    past_year,
    present_year,
    past_cover_ha,
    present_cover_ha,
    change_ha,
  } = result.satellite_comparison;

  /* =======================================================
     CALCULATIONS
  ======================================================= */
  const percentageChange = useMemo(() => {
    if (!past_cover_ha || past_cover_ha === 0) return 0;
    return ((present_cover_ha - past_cover_ha) / past_cover_ha) * 100;
  }, [past_cover_ha, present_cover_ha]);

  const isGain = change_ha > 0;
  const absChange = Math.abs(change_ha);

  /* =======================================================
     VISUAL SCALE (CAP TO AVOID EXAGGERATION)
  ======================================================= */
  const MAX_VISUAL_PERCENT = 5; // ±5% fills bar completely
  const visualPercent = Math.min(
    Math.abs(percentageChange),
    MAX_VISUAL_PERCENT
  );

  /* =======================================================
     DRONE VS SATELLITE CALCS (SAFE)
  ======================================================= */
  const droneData = result.drone_data || null;
  const satellitePresent = present_cover_ha;
  const droneVegetation = droneData?.vegetation_area_ha ?? null;

  const droneDiffPct =
    droneVegetation !== null && satellitePresent > 0
      ? ((droneVegetation - satellitePresent) / satellitePresent) * 100
      : null;

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
          color="#27ae60"
        />
        <StatBox
          label={`Present Vegetation (${present_year})`}
          value={`${present_cover_ha.toFixed(2)} ha`}
          color="#e67e22"
        />
        <StatBox
          label="Percentage Change"
          value={`${percentageChange.toFixed(2)}%`}
          color={percentageChange >= 0 ? "#27ae60" : "#c0392b"}
        />
      </div>
      {/* ================= DRONE STATUS ================= */}
      {result.drone_data?.error && (
        <div
          style={{
            marginBottom: "1.25rem",
            padding: "0.75rem 1rem",
            background: "#fff3cd",
            border: "1px solid #ffeeba",
            borderRadius: "10px",
            color: "#856404",
            fontSize: "0.85rem",
          }}
        >
          🚁 <strong>Drone analysis skipped:</strong>{" "}
          {result.drone_data.error}
        </div>
      )}


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
          {/* Center Line */}
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

          {/* Gain */}
          {isGain && (
            <div
              style={{
                position: "absolute",
                left: "50%",
                height: "100%",
                width: `${(visualPercent / MAX_VISUAL_PERCENT) * 50}%`,
                background: "#27ae60",
              }}
            />
          )}

          {/* Loss */}
          {!isGain && change_ha !== 0 && (
            <div
              style={{
                position: "absolute",
                right: "50%",
                height: "100%",
                width: `${(visualPercent / MAX_VISUAL_PERCENT) * 50}%`,
                background: "#c0392b",
              }}
            />
          )}
        </div>

        <div
          style={{
            marginTop: "0.5rem",
            fontSize: "0.85rem",
            color: "#555",
          }}
        >
          {change_ha === 0
            ? "No detectable change"
            : isGain
            ? `Gain of ${absChange.toFixed(2)} ha`
            : `Loss of ${absChange.toFixed(2)} ha`}
        </div>

        <div
          style={{
            marginTop: "0.25rem",
            fontSize: "0.75rem",
            color: "#888",
          }}
        >
          Bar scaled to ±{MAX_VISUAL_PERCENT}% to avoid visual exaggeration
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
            <div>
              Vegetation %: {droneData.vegetation_percentage}%
            </div>
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

          <div style={{ marginBottom: "0.5rem" }}>
            Difference:{" "}
            <strong
              style={{
                color:
                  droneDiffPct !== null && droneDiffPct >= 0
                    ? "#27ae60"
                    : "#c0392b",
              }}
            >
              {droneDiffPct?.toFixed(2)}%
            </strong>
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "flex-end",
              gap: "2rem",
              height: "140px",
            }}
          >
            {[
              {
                label: "Satellite",
                value: satellitePresent,
                color: "#2980b9",
              },
              {
                label: "Drone",
                value: droneVegetation,
                color: "#27ae60",
              },
            ].map((item) => (
              <div key={item.label} style={{ textAlign: "center" }}>
                <div
                  style={{
                    height: `${
                      (item.value /
                        Math.max(satellitePresent, droneVegetation, 1)) *
                      120
                    }px`,
                    width: "50px",
                    background: item.color,
                    borderRadius: "6px",
                  }}
                />
                <div style={{ marginTop: "0.5rem", fontSize: "0.8rem" }}>
                  {item.label}
                </div>
                <div style={{ fontSize: "0.75rem" }}>
                  {item.value} ha
                </div>
              </div>
            ))}
          </div>
        </div>
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

