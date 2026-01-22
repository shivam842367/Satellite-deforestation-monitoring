const API_BASE = "https://deforestation-backend.onrender.com";

export async function submitAnalysis({
  aoi,
  past_year,
  present_year,
}: {
  aoi: any;
  past_year: number;
  present_year: number;
}) {
  // 🔴 THIS IS THE CRITICAL FIX
  const geometry = aoi.geometry ? aoi.geometry : aoi;

  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      geometry,
      past_year,
      present_year,
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(err);
  }

  return res.json();
}

export async function fetchResult(jobId: string) {
  const res = await fetch(`${API_BASE}/result/${jobId}`);
  if (!res.ok) throw new Error("Failed to fetch result");
  return res.json();
}
