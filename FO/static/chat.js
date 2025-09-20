document.getElementById("chat-form").addEventListener("submit", async function (e) {
  e.preventDefault();

  const input = document.getElementById("user-input");
  const msg = input.value.trim();
  if (!msg) return;

  const chatBox = document.getElementById("chat-box");
  chatBox.innerHTML += `<div class="chat-msg user-msg">${msg}</div>`;
  input.value = "";

  const res = await fetch("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: msg }),
  });

  const data = await res.json();
  chatBox.innerHTML += `<div class="chat-msg bot-msg">${data.response}</div>`;
  chatBox.scrollTop = chatBox.scrollHeight;
});
