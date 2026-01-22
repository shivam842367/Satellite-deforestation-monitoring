import { useState, useEffect } from "react";

export default function DeforestationMonitor() {
  const [aoi, setAOI] = useState(null);
  const [pastYear, setPastYear] = useState(2016);
  const [presentYear, setPresentYear] = useState(2024);
  
  // Drone upload
  const [droneFile, setDroneFile] = useState(null);
  const [droneFileId, setDroneFileId] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  
  // Analysis state
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState("");

  const API_BASE = "http://localhost:8000"; // Change for production

  // ==========================================
  // HANDLE DRONE FILE UPLOAD
  // ==========================================
  async function handleDroneUpload() {
    if (!droneFile) {
      setUploadStatus("Please select a file first");
      return;
    }

    setUploadStatus("Uploading...");
    
    const formData = new FormData();
    formData.append("file", droneFile);

    try {
      const response = await fetch(`${API_BASE}/upload-drone-image`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Upload failed");

      const data = await response.json();
      setDroneFileId(data.file_id);
      setUploadStatus(`✅ Uploaded: ${data.filename} (${data.size_mb} MB)`);
    } catch (err) {
      setUploadStatus(`❌ Upload failed: ${err.message}`);
    }
  }

  // ==========================================
  // RUN MULTI-SOURCE ANALYSIS
  // ==========================================
  async function runAnalysis() {
    if (!aoi) {
      setError("Please draw an area of interest on the map first");
      return;
    }

    setResult(null);
    setError(null);
    setLoading(true);
    setProgress("Submitting analysis job...");

    try {
      // 1️⃣ Submit job
      const payload = {
        geometry: {
          type: "Polygon",
          coordinates: aoi,
        },
        past_year: pastYear,
        present_year: presentYear,
      };

      const submitUrl = droneFileId
        ? `${API_BASE}/analyze?drone_image_id=${droneFileId}`
        : `${API_BASE}/analyze`;

      const submitResponse = await fetch(submitUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!submitResponse.ok) throw new Error("Failed to submit job");

      const { job_id } = await submitResponse.json();
      setProgress(`Job submitted. Processing... (Job ID: ${job_id.slice(0, 8)}...)`);

      // 2️⃣ Poll for result
      const pollInterval = setInterval(async () => {
        const pollResponse = await fetch(`${API_BASE}/jobs/${job_id}`);
        const jobData = await pollResponse.json();

        if (jobData.status === "completed") {
          setResult(jobData);
          setLoading(false);
          setProgress("");
          clearInterval(pollInterval);
        } else if (jobData.status === "failed") {
          setError(`Analysis failed: ${jobData.error}`);
          setLoading(false);
          setProgress("");
          clearInterval(pollInterval);
        } else {
          setProgress(`Processing satellite and drone data...`);
        }
      }, 3000);

    } catch (err) {
      setError(`Request failed: ${err.message}`);
      setLoading(false);
      setProgress("");
    }
  }

  // ==========================================
  // MOCK AOI SELECTION (Replace with real map)
  // ==========================================
  function selectMockAOI() {
    // Example: Lucknow area polygon
    setAOI([
      [
        [80.9, 26.8],
        [81.0, 26.8],
        [81.0, 26.9],
        [80.9, 26.9],
        [80.9, 26.8],
      ],
    ]);
  }

  return (
    <div style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto", fontFamily: "system-ui" }}>
      <h1 style={{ marginBottom: "0.5rem" }}>🛰️ Drone-Based Deforestation Monitor</h1>
      <p style={{ color: "#666", marginBottom: "2rem" }}>
        Multi-source analysis: Past Satellite → Present Satellite → Current Drone
      </p>

      {/* ==========================================
          STEP 1: SELECT AREA
      ========================================== */}
      <section style={sectionStyle}>
        <h2>Step 1: Select Area of Interest</h2>
        <p style={{ color: "#666", fontSize: "0.9rem" }}>
          Draw a polygon on the map (replace this with actual map component)
        </p>
        
        <button onClick={selectMockAOI} style={buttonStyle}>
          📍 Use Sample Area (Lucknow)
        </button>
        
        {aoi && (
          <div style={{ marginTop: "1rem", padding: "1rem", background: "#f0f9ff", borderRadius: "6px" }}>
            ✅ Area selected: {aoi[0].length} coordinates
          </div>
        )}
      </section>

      {/* ==========================================
          STEP 2: UPLOAD DRONE IMAGE
      ========================================== */}
      <section style={sectionStyle}>
        <h2>Step 2: Upload Drone Image (Optional)</h2>
        <p style={{ color: "#666", fontSize: "0.9rem" }}>
          Multispectral GeoTIFF with bands: [Red, Green, Blue, NIR]
        </p>

        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <input
            type="file"
            accept=".tif,.tiff"
            onChange={(e) => setDroneFile(e.target.files?.[0] || null)}
            style={{ flex: 1 }}
          />
          <button onClick={handleDroneUpload} disabled={!droneFile} style={buttonStyle}>
            📤 Upload
          </button>
        </div>

        {uploadStatus && (
          <div style={{ marginTop: "1rem", color: uploadStatus.includes("✅") ? "green" : "red" }}>
            {uploadStatus}
          </div>
        )}
      </section>

      {/* ==========================================
          STEP 3: SELECT TIME PERIODS
      ========================================== */}
      <section style={sectionStyle}>
        <h2>Step 3: Select Time Periods</h2>
        
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
          <div>
            <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "600" }}>
              Past Year (Baseline)
            </label>
            <select
              value={pastYear}
              onChange={(e) => setPastYear(Number(e.target.value))}
              style={selectStyle}
            >
              {[2010, 2012, 2014, 2016, 2018, 2020].map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "600" }}>
              Present Year (Comparison)
            </label>
            <select
              value={presentYear}
              onChange={(e) => setPresentYear(Number(e.target.value))}
              style={selectStyle}
            >
              {[2020, 2021, 2022, 2023, 2024].map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      {/* ==========================================
          STEP 4: RUN ANALYSIS
      ========================================== */}
      <section style={sectionStyle}>
        <button
          onClick={runAnalysis}
          disabled={!aoi || loading}
          style={{
            ...buttonStyle,
            padding: "1rem 2rem",
            fontSize: "1.1rem",
            background: loading ? "#666" : "#000",
          }}
        >
          {loading ? "⏳ Processing..." : "🚀 Run Analysis"}
        </button>

        {progress && (
          <div style={{ marginTop: "1rem", color: "#0066cc" }}>
            {progress}
          </div>
        )}

        {error && (
          <div style={{ marginTop: "1rem", padding: "1rem", background: "#fee", borderRadius: "6px", color: "red" }}>
            ❌ {error}
          </div>
        )}
      </section>

      {/* ==========================================
          RESULTS PANEL
      ========================================== */}
      {result && result.satellite_comparison && (
        <section style={{ ...sectionStyle, background: "#f9fafb" }}>
          <h2>📊 Analysis Results</h2>

          {/* Satellite Comparison */}
          <div style={resultCardStyle}>
            <h3 style={{ marginTop: 0, color: "#0066cc" }}>🛰️ Satellite Data Comparison</h3>
            
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
              <StatBox
                label={`${result.satellite_comparison.past_year} (Baseline)`}
                value={`${result.satellite_comparison.past_cover_ha} ha`}
                color="#27ae60"
              />
              <StatBox
                label={`${result.satellite_comparison.present_year} (Current)`}
                value={`${result.satellite_comparison.present_cover_ha} ha`}
                color="#e67e22"
              />
            </div>

            <div style={{ padding: "1rem", background: "#fff3cd", borderRadius: "6px", marginTop: "1rem" }}>
              <strong>Change:</strong> {result.satellite_comparison.change_ha} ha
              <br />
              <strong>Annual Rate:</strong>{" "}
              <span style={{ fontSize: "1.2rem", color: "#c0392b" }}>
                {result.satellite_comparison.deforestation_rate_pct_per_year}% / year
              </span>
            </div>
          </div>

          {/* Drone Data */}
          {result.drone_data && !result.drone_data.error && (
            <div style={resultCardStyle}>
              <h3 style={{ marginTop: 0, color: "#8e44ad" }}>🚁 Drone Data Analysis</h3>
              
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                <StatBox
                  label="Vegetation Cover"
                  value={`${result.drone_data.vegetation_area_ha} ha`}
                  color="#16a085"
                />
                <StatBox
                  label="Coverage Percentage"
                  value={`${result.drone_data.vegetation_percentage}%`}
                  color="#2980b9"
                />
              </div>

              <div style={{ marginTop: "1rem", padding: "1rem", background: "#e8f5e9", borderRadius: "6px" }}>
                <strong>Mean NDVI:</strong> {result.drone_data.mean_ndvi}
                <br />
                <strong>Original Resolution:</strong> {result.drone_data.original_resolution_m}m
                <br />
                <strong>Downscaled to:</strong> {result.drone_data.downscaled_resolution_m}m (satellite equivalent)
              </div>

              {result.drone_data.comparison_with_satellite && (
                <div style={{ marginTop: "1rem", padding: "1rem", background: "#fff9e6", borderRadius: "6px" }}>
                  <strong>Difference from Satellite:</strong>{" "}
                  {result.drone_data.comparison_with_satellite.difference_from_present_satellite_ha} ha
                  <br />
                  <strong>Recent Trend:</strong>{" "}
                  {result.drone_data.comparison_with_satellite.recent_trend_rate_pct_per_year}% / year
                </div>
              )}
            </div>
          )}

          {/* Summary */}
          {result.summary && (
            <div style={{ ...resultCardStyle, background: "#f8d7da", borderLeft: "4px solid #c0392b" }}>
              <h3 style={{ marginTop: 0 }}>📉 Overall Summary</h3>
              <p>
                <strong>Total Loss:</strong> {result.summary.total_loss_ha} ha ({result.summary.total_loss_pct}%)
              </p>
              <p>
                <strong>Time Period:</strong> {result.summary.time_period_years} years
              </p>
            </div>
          )}
        </section>
      )}
    </div>
  );
}

// ==========================================
// HELPER COMPONENTS
// ==========================================
function StatBox({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ padding: "1rem", background: "#fff", borderRadius: "6px", border: "1px solid #ddd" }}>
      <div style={{ fontSize: "0.85rem", color: "#666", marginBottom: "0.5rem" }}>{label}</div>
      <div style={{ fontSize: "1.5rem", fontWeight: "700", color }}>{value}</div>
    </div>
  );
}

// ==========================================
// STYLES
// ==========================================
const sectionStyle: React.CSSProperties = {
  marginBottom: "2rem",
  padding: "1.5rem",
  background: "#fff",
  borderRadius: "8px",
  boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
};

const buttonStyle: React.CSSProperties = {
  background: "#000",
  color: "#fff",
  border: "none",
  padding: "0.75rem 1.5rem",
  borderRadius: "6px",
  cursor: "pointer",
  fontWeight: "600",
  transition: "all 0.2s",
};

const selectStyle: React.CSSProperties = {
  width: "100%",
  padding: "0.75rem",
  borderRadius: "6px",
  border: "1px solid #ddd",
  fontSize: "1rem",
};

const resultCardStyle: React.CSSProperties = {
  padding: "1.5rem",
  background: "#fff",
  borderRadius: "8px",
  marginBottom: "1rem",
  boxShadow: "0 1px 4px rgba(0,0,0,0.1)",
};