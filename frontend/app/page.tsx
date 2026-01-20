"use client";

import { useState, useEffect } from "react";
import MapAOI from "@/components/MapAOI";
import { submitAnalysis, fetchResult } from "@/lib/api";

export default function Home() {
  const [aoi, setAOI] = useState<any>(null);
  const [slider, setSlider] = useState(50);
  const [pastYear, setPastYear] = useState(2016);
  const [presentYear, setPresentYear] = useState(2024);

  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /* -------------------------------------------------
     MAP SWIPE (CSS VARIABLE)
  --------------------------------------------------*/
  useEffect(() => {
    document.documentElement.style.setProperty("--slider", `${slider}%`);
  }, [slider]);

  /* -------------------------------------------------
     RUN ANALYSIS (REAL BACKEND)
  --------------------------------------------------*/
  async function runAnalysis() {
    if (!aoi) return;

    setResult(null);
    setError(null);
    setLoading(true);

    try {
      // 1️⃣ Submit job
      const cleanedAOI =
        aoi.type === "FeatureCollection" ? aoi.features[0] : aoi;

      const { job_id } = await submitAnalysis({
        aoi: cleanedAOI,
        past_year: pastYear,
        present_year: presentYear,
      });


      // 2️⃣ Poll for result
      const interval = setInterval(async () => {
        const res = await fetchResult(job_id);

        if (res.status === "completed") {
          setResult(res);
          setLoading(false);
          clearInterval(interval);
        }

        if (res.status === "failed") {
          setError("Analysis failed. Please try again.");
          setLoading(false);
          clearInterval(interval);
        }
      }, 3000);

    } catch (err) {
      setError("Backend request failed.");
      setLoading(false);
    }
  }

  /* -------------------------------------------------
     UI
  --------------------------------------------------*/
  return (
    <main style={{ padding: "2rem", maxWidth: "1100px", margin: "0 auto" }}>
      <h1 style={{ textShadow: "0 2px 4px rgba(0,0,0,0.3)" }}>
        Drone-Based Deforestation Monitor
      </h1>

      {/* AOI */}
      <h3>1. Select Area of Interest</h3>
      <MapAOI onAOIChange={setAOI} sliderValue={slider} />

      {/* SLIDER */}
      <h3>2. Compare Time Periods</h3>

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

      {/* YEAR SELECTORS */}
      <div style={{ display: "flex", gap: "1rem", marginBottom: "1.5rem" }}>
        <div>
          <label>Past Year</label>
          <br />
          <select value={pastYear} onChange={(e) => setPastYear(+e.target.value)}>
            {[2016, 2018, 2020, 2022].map((y) => (
              <option key={y} value={y}>{y}</option>
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
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
      </div>

      {/* RUN BUTTON */}
      <button
        disabled={!aoi || loading}
        onClick={runAnalysis}
        style={{
          background: "#000",
          color: "#fff",
          padding: "0.6rem 1.2rem",
          borderRadius: "6px",
          boxShadow: "0 4px 10px rgba(0,0,0,0.4)",
          cursor: "pointer",
        }}
      >
        {loading ? "Processing…" : "Run Analysis"}
      </button>

      {/* STATUS */}
      {loading && <p style={{ marginTop: "1rem" }}>Processing satellite data…</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      {/* LEGEND */}
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
          <span style={{ color: "#27ae60", fontWeight: "bold" }}>■</span> Past vegetation cover
        </p>
        <p>
          <span style={{ color: "#c0392b", fontWeight: "bold" }}>■</span> Present vegetation cover
        </p>
      </div>

      {/* RESULTS */}
      {result && (
        <>
          <h3>3. Vegetation Change Summary</h3>
          <p>Past Cover: {result.past_cover_ha} ha</p>
          <p>Present Cover: {result.present_cover_ha} ha</p>
          <p>
            Change Rate:{" "}
            <strong>{result.deforestation_rate_pct_per_year}% / year</strong>
          </p>
        </>
      )}
    </main>
  );
}
