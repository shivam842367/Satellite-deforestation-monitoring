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

      {/* ================= GAIN VS LOSS ================= */}
      <div>
        <h4 style={{ marginBottom: "0.75rem" }}>
          🌿 Vegetation Gain vs Loss
        </h4>

        {/* Diverging Bar */}
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
          {!isGain && (
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

        {/* Labels */}
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
