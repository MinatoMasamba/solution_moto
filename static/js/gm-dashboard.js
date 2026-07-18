/*
 * gm-dashboard.js — runtime partagé des consoles GO-MBOKA (DG, Gérant, Console)
 * et des pages d'auth converties depuis les maquettes « nocturne ».
 *
 * Remplace l'ancien runtime propriétaire (x-dc / DCLogic). Tout est piloté par
 * des attributs `data-*` posés dans les templates :
 *   - navigation sidebar : .gm-nav[data-view]  ->  [data-panel]
 *   - thème clair/sombre : [data-gm-theme-toggle] (bouton) ou .gm-theme[data-theme] (segmenté)
 *   - afficher/masquer mot de passe : [data-gm-pw-toggle="idDuChamp"]
 *   - onglets (auth)     : .gm-tab[data-tab]  ->  [data-form]
 *   - horloge live       : .gm-clock
 *   - marqueurs carte     : .gm-marker[data-move="1"]
 *
 * Helpers réseau exposés : window.gmGetJSON, gmPostJSON, gmCsrf, gmFmt, gmClear.
 */
(function () {
  "use strict";

  // ---------------------------------------------------------------- utilitaires
  function getCookie(name) {
    const m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return m ? decodeURIComponent(m.pop()) : "";
  }
  function gmCsrf() { return getCookie("csrftoken"); }

  function gmFmt(n, opts) {
    if (n === null || n === undefined || isNaN(n)) return "—";
    return Number(n).toLocaleString("fr-FR", opts || {});
  }

  async function gmGetJSON(url) {
    const doFetch = window.fetchWithTimeout || fetch;
    const res = await doFetch(url, { headers: { Accept: "application/json" } });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const err = new Error((data && (data.detail || data.error)) || "Erreur " + res.status);
      err.status = res.status;
      throw err;
    }
    return data;
  }

  async function gmPostJSON(url, body) {
    const doFetch = window.fetchWithTimeout || fetch;
    const res = await doFetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-CSRFToken": gmCsrf(),
      },
      body: JSON.stringify(body || {}),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const err = new Error((data && (data.detail || data.error)) || "Erreur " + res.status);
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  }

  // Vide un conteneur et y écrit un message (chargement / vide / erreur).
  function gmClear(el, message, tone) {
    if (!el) return;
    const color = tone === "error" ? "#d98a8a" : "var(--color-neutral-500)";
    el.innerHTML =
      '<div style="padding:22px 8px;font-size:13px;color:' + color + '">' +
      (message || "") + "</div>";
  }

  // ---------------------------------------------------------------- thème
  function applyTheme(theme) {
    const light = theme === "light";
    // Source de vérité : attribut sur <html> (appliqué dès le <head>, sans flash).
    document.documentElement.setAttribute("data-gm-theme", theme);
    // Compat : la classe sur .gm-root reste supportée par les CSS existantes.
    document.querySelectorAll(".gm-root").forEach((r) => r.classList.toggle("gm-light", light));
    // segmentés (réglages)
    document.querySelectorAll(".gm-theme[data-theme]").forEach((o) => {
      o.classList.toggle("gm-on", o.getAttribute("data-theme") === theme);
    });
    // bouton toggle (auth / login DG)
    document.querySelectorAll(".gm-thi").forEach((ic) => {
      ic.className = (light ? "ph-fill ph-sun" : "ph-fill ph-moon") + " gm-thi";
    });
    document.querySelectorAll(".gm-thl").forEach((lb) => {
      lb.textContent = light ? "Clair" : "Sombre";
    });
    try { localStorage.setItem("gm-theme", theme); } catch (e) {}
    window.__gmTheme = theme;
  }

  function setupTheme() {
    applyTheme(window.__gmTheme || "dark");
    document.addEventListener("click", (e) => {
      const seg = e.target.closest && e.target.closest(".gm-theme[data-theme]");
      if (seg) { applyTheme(seg.getAttribute("data-theme")); return; }
      const btn = e.target.closest && e.target.closest("[data-gm-theme-toggle]");
      if (btn) { applyTheme((window.__gmTheme === "light") ? "dark" : "light"); }
    });
  }

  // ---------------------------------------------------------------- mot de passe
  function setupPasswordToggles() {
    document.addEventListener("click", (e) => {
      const t = e.target.closest && e.target.closest("[data-gm-pw-toggle]");
      if (!t) return;
      const input = document.getElementById(t.getAttribute("data-gm-pw-toggle"));
      if (!input) return;
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      if (t.classList.contains("ph-eye") || t.classList.contains("ph-eye-slash")) {
        t.classList.toggle("ph-eye", !show);
        t.classList.toggle("ph-eye-slash", show);
      }
    });
  }

  // ---------------------------------------------------------------- onglets (auth)
  function setupTabs() {
    document.addEventListener("click", (e) => {
      const tab = e.target.closest && e.target.closest(".gm-tab[data-tab]");
      if (!tab) return;
      const name = tab.getAttribute("data-tab");
      document.querySelectorAll("[data-form]").forEach((f) => {
        f.style.display = f.getAttribute("data-form") === name ? "" : "none";
      });
      document.querySelectorAll(".gm-tab[data-tab]").forEach((s) => {
        const on = s.getAttribute("data-tab") === name;
        s.style.background = on ? "var(--color-surface)" : "transparent";
        s.style.color = on ? "var(--color-accent-200)" : "var(--color-neutral-400)";
        s.style.fontWeight = on ? "600" : "500";
      });
    });
  }

  // ---------------------------------------------------------------- navigation
  // Appelé par chaque console avec sa propre table de titres.
  function gmSetupNav(titles, defaultView) {
    function nav(v) {
      document.querySelectorAll("[data-panel]").forEach((p) => {
        p.style.display = p.getAttribute("data-panel") === v ? "" : "none";
      });
      document.querySelectorAll(".gm-nav[data-view]").forEach((n) => {
        const on = n.getAttribute("data-view") === v;
        n.style.background = on ? "rgba(145,132,217,.13)" : "transparent";
        n.style.color = on ? "var(--color-accent-200)" : "var(--color-neutral-400)";
        n.style.fontWeight = on ? "600" : "500";
        n.style.boxShadow = on ? "inset 2px 0 0 var(--color-accent)" : "none";
      });
      const t = titles && titles[v];
      if (t) {
        const title = document.getElementById("gm-title");
        const sub = document.getElementById("gm-sub");
        if (title) title.textContent = t[0];
        if (sub) sub.textContent = t[1];
      }
      const sc = document.getElementById("gm-scroll");
      if (sc) sc.scrollTop = 0;
      window.__gmView = v;
      document.dispatchEvent(new CustomEvent("gm:view", { detail: { view: v } }));
    }
    document.addEventListener("click", (e) => {
      const link = e.target.closest && e.target.closest("[data-view]");
      if (!link) return;
      nav(link.getAttribute("data-view"));
    });
    window.gmNav = nav;
    nav(defaultView || "overview");
  }

  // ---------------------------------------------------------------- live (horloge + carte)
  function setupLive() {
    const tick = () => {
      const s = new Date().toLocaleTimeString("fr-FR");
      document.querySelectorAll(".gm-clock").forEach((e) => { e.textContent = s; });
    };
    if (document.querySelector(".gm-clock")) { tick(); setInterval(tick, 1000); }
    if (document.querySelector('.gm-marker[data-move="1"]')) {
      setInterval(() => {
        document.querySelectorAll('.gm-marker[data-move="1"]').forEach((el) => {
          if (el.offsetParent === null) return;
          const dx = (Math.random() * 2 - 1) * 9;
          const dy = (Math.random() * 2 - 1) * 9;
          el.style.transform = "translate(" + dx + "px," + dy + "px)";
        });
      }, 1900);
    }
  }

  // ---------------------------------------------------------------- exports
  window.gmCsrf = gmCsrf;
  window.gmFmt = gmFmt;
  window.gmGetJSON = gmGetJSON;
  window.gmPostJSON = gmPostJSON;
  window.gmClear = gmClear;
  window.gmSetupNav = gmSetupNav;

  document.addEventListener("DOMContentLoaded", function () {
    setupTheme();
    setupPasswordToggles();
    setupTabs();
    setupLive();
  });
})();
