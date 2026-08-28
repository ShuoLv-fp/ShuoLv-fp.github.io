const form = document.getElementById("login-form");
const passwordInput = document.getElementById("workflow-password");
const message = document.getElementById("login-error");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const password = passwordInput.value;
  passwordInput.value = "";
  message.textContent = "Checking access…";

  try {
    const response = await fetch("/api/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ password })
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(response.status === 429
        ? "Too many attempts. Wait fifteen minutes before trying again."
        : payload.error || "The password was not accepted.");
    }
    window.location.replace("/app#dossiers");
  } catch (error) {
    message.textContent = error.message;
    passwordInput.focus();
  }
});
