const BASE_URL = "http://127.0.0.1:8000";

export async function getGoals() {
  const res = await fetch(`${BASE_URL}/goals`);
  if (!res.ok) throw new Error("Failed to fetch goals");
  return res.json();
}

export async function getRecommendations({
  goalId,
  priorEducation,
  earnedCredits,
  preferOnline,
  useAI = false,
}) {
  const endpoint = useAI ? "/recommendations/ai" : "/recommendations";
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      goalId,
      priorEducation,
      earnedCredits,
      preferOnline,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Request failed: ${res.status} - ${text}`);
  }

  return res.json();
}
