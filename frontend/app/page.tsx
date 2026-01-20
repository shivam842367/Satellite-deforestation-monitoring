"use client";

import { useState, useEffect } from "react";
import MapAOI from "@/components/MapAOI";

export default function Home() {
  const [aoi, setAOI] = useState<any>(null);
  const [slider, setSlider] = useState(50);
  const [pastYear, setPastYear] = useState(2016);
  const [presentYear, setPresentYear] = useState(2024);
  const [result, setResult] = useState<any>(null);

  // Update CSS variable for map swipe
  useEffect(() => {
    document.documentElement.style.setProperty("--slider", `${slider}%`);
  }, [slider]);

  function runAnalysis() {
    // Demo result – backend will replace this
    setResult({
      past_cover_ha: 120.5,
      present_cover_ha: 95.2,
      percent_change: -21.0,
    });
  }

  return (
    <main style={{ padding: "2rem", maxWidth: "1100px", margin: "0 auto" }}>
      <h1>Drone-Based Deforestation Monitor</h1>

      <h3>1. Select Area of Interest</h3>
      <MapAOI onAOIChange={setAOI} sliderValue={slider} />

      <h3>2. Compare Time Periods</h3>

      {/* Map swipe slider */}
      <input
        type="range"
        min={0}
        max={100}
        value={slider}
        onChange={(e) => setSlider(Number(e.target.value))}
        style={{ width: "100%", marginBottom: "0.5rem" }}
      />

      <p>
        <strong>{pastYear}</strong> (Past) ←→{" "}
        <strong>{presentYear}</strong> (Present)
      </p>

      {/* Date selectors */}
      <div style={{ display: "flex", gap: "1rem", marginBottom: "1.5rem" }}>
        <div>
          <label>Past Year</label>
          <br />
          <select value={pastYear} onChange={(e) => setPastYear(+e.target.value)}>
            {[2016, 2018, 2020, 2022].map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label>Present Year</label>
          <br />
          <select
            value={presentYear}
            onChange={(e) => setPresentYear(+e.target.value)}
          >
            {[2021, 2022, 2023, 2024].map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </div>
      </div>

      <button disabled={!aoi} onClick={runAnalysis}>
        Run Analysis
      </button>

      {/* Legend */}
      <div
        style={{
          marginTop: "1.5rem",
          padding: "1rem",
          border: "1px solid #ccc",
          borderRadius: "6px",
          background: "#fafafa",
        }}
      >
        <h4>Legend</h4>
        <p>
          <span style={{ color: "#27ae60", fontWeight: "bold" }}>■</span> Past
          vegetation cover
        </p>
        <p>
          <span style={{ color: "#c0392b", fontWeight: "bold" }}>■</span> Present
          vegetation cover
        </p>
      </div>

      {/* Results */}
      {result && (
        <>
          <h3>3. Vegetation Change Summary</h3>
          <p>Past Cover: {result.past_cover_ha} ha</p>
          <p>Present Cover: {result.present_cover_ha} ha</p>
          <p>Change: {result.percent_change}%</p>
        </>
      )}
    </main>
  );
}
