document.getElementById("test-form").addEventListener("submit", async function (e) {
  e.preventDefault();
  const formData = new FormData(this);
  const responseBox = document.getElementById("response-box");
  responseBox.innerHTML = "<p class='loading-msg'>🧠 Generando evaluación...</p>";

  for (let [key, value] of formData.entries()) {
    if (key.startsWith("q") && !key.includes("_")) {
      const qid = key.replace("q", "");
      const correct = formData.get(`correct_${qid}`);
      const questionText = formData.get(`q${qid}_text`);

      const res = await fetch("/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_answer: value,
          correct_option: correct,
          question_text: questionText,
        }),
      });

      const data = await res.json();
      responseBox.innerHTML += `<div class='response-card'><strong>📝 Pregunta ${qid}</strong><br><em>${questionText}</em><br>${data.response}</div>`;
    }
  }
});
