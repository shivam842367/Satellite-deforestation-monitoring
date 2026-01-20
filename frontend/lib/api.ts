const API_URL = process.env.NEXT_PUBLIC_API_URL!;

export async function submitAnalysis(payload: any) {
  const res = await fetch(`${API_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error("Failed to submit analysis");
  }

  return res.json(); // { job_id, status }
}

export async function fetchResult(jobId: string) {
  const res = await fetch(`${API_URL}/result/${jobId}`);

  if (!res.ok) {
    throw new Error("Failed to fetch result");
  }

  return res.json();
}
