document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("api-status-check");
  const result = document.getElementById("api-status-result");

  if (!button || !result) {
    return;
  }

  button.addEventListener("click", async () => {
    result.textContent = "Vérification en cours…";
    try {
      const response = await fetch("/api/v1/health/");
      const data = await response.json();
      result.textContent = response.ok
        ? `API opérationnelle (statut: ${data.status}).`
        : "L'API a répondu avec une erreur.";
    } catch (error) {
      result.textContent = "Impossible de contacter l'API.";
    }
  });
});
