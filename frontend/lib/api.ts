const API_URL = "https://deforestation-backend.onrender.com";

export async function submitAnalysis(payload: {
  geometry: any;
  past_year: number;
  present_year: number;
}) {
  const res = await fetch(`${API_URL}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Analysis failed");
  }

  return res.json();
}

export async function fetchResult(jobId: string) {
  const res = await fetch(`${API_URL}/result/${jobId}`);

  if (!res.ok) {
    throw new Error("Failed to fetch job result");
  }

  return res.json();
}
