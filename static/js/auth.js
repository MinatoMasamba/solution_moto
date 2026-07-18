const AUTH_STORAGE_KEYS = { access: "go_mboka_access", refresh: "go_mboka_refresh" };

function storeTokens({ access, refresh }) {
  localStorage.setItem(AUTH_STORAGE_KEYS.access, access);
  localStorage.setItem(AUTH_STORAGE_KEYS.refresh, refresh);
}

function extractErrorMessage(data) {
  if (!data || typeof data !== "object") {
    return "Une erreur est survenue. Réessayez.";
  }
  const firstKey = Object.keys(data)[0];
  const firstValue = data[firstKey];
  const message = Array.isArray(firstValue) ? firstValue[0] : firstValue;
  return typeof message === "string" ? message : "Une erreur est survenue. Réessayez.";
}

async function submitJSON(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(extractErrorMessage(data));
  }
  return data;
}

function bindForm(formId, errorId, buildPayload, url) {
  const form = document.getElementById(formId);
  const errorEl = document.getElementById(errorId);
  if (!form) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorEl.classList.add("hidden");

    const submitButton = form.querySelector("button[type='submit']");
    submitButton.disabled = true;

    try {
      const data = await submitJSON(url, buildPayload(form));
      storeTokens(data);
      window.location.href = "/";
    } catch (error) {
      errorEl.textContent = error.message;
      errorEl.classList.remove("hidden");
    } finally {
      submitButton.disabled = false;
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  bindForm("register-form", "register-error", (form) => ({
    phone_number: form.phone_number.value.trim(),
    first_name: form.first_name.value.trim(),
    last_name: form.last_name.value.trim(),
    email: form.email.value.trim(),
    role: form.role.value,
    password: form.password.value,
  }), "/api/v1/auth/register/");

  bindForm("login-form", "login-error", (form) => ({
    phone_number: form.phone_number.value.trim(),
    password: form.password.value,
  }), "/api/v1/auth/login/");
});
