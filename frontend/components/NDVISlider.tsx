"use client";

export default function NDVISlider() {
  return (
    <div style={{ position: "relative", height: "350px", marginTop: "1rem" }}>
      <img
        src="/after.jpg"
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />

      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "50%",
          height: "100%",
          overflow: "hidden",
          borderRight: "3px solid white",
        }}
      >
        <img
          src="/before.jpg"
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </div>
    </div>
  );
}
