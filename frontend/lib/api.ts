export async function startAnalysis(payload: any) {
  const res = await fetch("http://127.0.0.1:8000/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function getResult(jobId: string) {
  const res = await fetch("http://127.0.0.1:8000/analyze-demo");
  return res.json();
}
