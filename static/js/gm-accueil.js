/* Page d'accueil GO-MBOKA — animations d'apparition, carrousel d'avis, contact. */
(function () {
  "use strict";

  // Apparition au défilement
  function setupReveal() {
    var els = document.querySelectorAll(".gm-reveal");
    if (!("IntersectionObserver" in window)) {
      els.forEach(function (el) { el.classList.add("gm-in"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("gm-in"); io.unobserve(e.target); }
      });
    }, { threshold: 0.12 });
    els.forEach(function (el) { io.observe(el); });
  }

  // Carrousel d'avis
  function setupCarousel() {
    var slides = document.querySelectorAll(".gm-slide");
    if (!slides.length) return;
    var count = slides.length;
    var cur = 0;
    function show(i) {
      cur = (i + count) % count;
      slides.forEach(function (s) {
        s.style.display = String(s.getAttribute("data-i")) === String(cur) ? "block" : "none";
      });
      document.querySelectorAll(".gm-dot").forEach(function (d) {
        var on = String(d.getAttribute("data-i")) === String(cur);
        d.style.width = on ? "22px" : "8px";
        d.style.background = on ? "var(--color-accent-500)" : "var(--color-neutral-700)";
      });
    }
    document.addEventListener("click", function (e) {
      var ctl = e.target.closest && e.target.closest("[data-gm-carousel]");
      if (ctl) { show(cur + (ctl.getAttribute("data-gm-carousel") === "prev" ? -1 : 1)); return; }
      var dot = e.target.closest && e.target.closest(".gm-dot");
      if (dot) { show(parseInt(dot.getAttribute("data-i"), 10) || 0); }
    });
    var timer = setInterval(function () { show(cur + 1); }, 5500);
    // pause l'auto-défilement au survol
    var wrap = slides[0].parentNode;
    if (wrap) {
      wrap.addEventListener("mouseenter", function () { clearInterval(timer); });
    }
    show(0);
  }

  // Formulaire de contact (pas de stockage : confirmation chaleureuse)
  function setupContact() {
    var btn = document.getElementById("gm-contact-send");
    if (!btn) return;
    btn.addEventListener("click", function () {
      if (window.showAppToast) {
        window.showAppToast("Merci ! Votre message est bien parti — nous vous répondons très vite, avec le sourire. 🧡", "success");
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    setupReveal();
    setupCarousel();
    setupContact();
  });
})();
