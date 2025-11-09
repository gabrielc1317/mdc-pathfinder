export async function invokeLLM({ prompt }) {
  const res = await fetch("http://localhost:8000/api/invoke_llm", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });

  const data = await res.json();
  console.log("AI response:", data);
  return data;
}
