/* App Client GO-MBOKA — navigation + branchement API réel. */
(function () {
  "use strict";

  function $(id) { return document.getElementById(id); }
  function set(id, html) { var e = $(id); if (e) e.innerHTML = html; }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function fc(n) { return (window.gmFmt ? window.gmFmt(Math.round(n || 0)) : Math.round(n || 0)) + " FC"; }
  function rows(d) { return (d && (d.results || d)) || []; }
  function initials(name) {
    var p = String(name || "").trim().split(/\s+/);
    return ((p[0] || "")[0] || "") + ((p[1] || "")[0] || "");
  }
  function toast(m, t) { if (window.showAppToast) window.showAppToast(m, t || "info"); }

  // POST ne suffit pas pour PATCH/DELETE : petit helper méthode + CSRF.
  function sendJSON(url, method, body) {
    var doFetch = window.fetchWithTimeout || fetch;
    return doFetch(url, {
      method: method,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-CSRFToken": window.gmCsrf ? window.gmCsrf() : "",
      },
      body: body ? JSON.stringify(body) : undefined,
    }).then(function (res) {
      if (!res.ok) {
        return res.json().catch(function () { return {}; }).then(function (d) { throw new Error(d.detail || "Erreur"); });
      }
      return res.status === 204 ? {} : res.json().catch(function () { return {}; });
    });
  }

  // ── Navigation ────────────────────────────────────────────────────────
  var TABS = ["home", "places", "create", "wallet", "profil"];
  var ICONS = { home: "ph-house", places: "ph-map-pin-line", create: "ph-plus-circle", wallet: "ph-wallet", profil: "ph-user" };

  function tabFor(v) {
    if (TABS.indexOf(v) !== -1) return v;
    if (["create", "searching", "ontrip", "rate"].indexOf(v) !== -1) return "create";
    if (["wallet", "topup"].indexOf(v) !== -1) return "wallet";
    if (["profil", "compte", "motdepasse", "momo", "referral"].indexOf(v) !== -1) return "profil";
    return "home";
  }

  function go(v) {
    document.querySelectorAll("[data-panel]").forEach(function (p) {
      p.style.display = p.getAttribute("data-panel") === v ? "" : "none";
    });
    var tk = tabFor(v);
    document.querySelectorAll(".gm-navi").forEach(function (n) {
      var key = n.getAttribute("data-view"), on = key === tk;
      n.style.color = on ? "var(--color-accent-300)" : "var(--color-neutral-500)";
      var ic = n.querySelector("i");
      if (ic) { ic.className = (on ? "ph-fill " : "ph ") + ICONS[key]; ic.style.fontSize = key === "create" ? "24px" : "21px"; }
    });
    var sc = $("gm-scroll"); if (sc) sc.scrollTop = 0;
    if (v === "wallet") loadWallet();
    if (v === "places") loadPlaces();
    if (v === "referral") loadSummary();
  }
  window.gmClientGo = go;

  // ── Résumé client ─────────────────────────────────────────────────────
  function loadSummary() {
    window.gmGetJSON("/api/v1/client/summary/").then(function (d) {
      var ratingTxt = d.rating ? "★ " + String(d.rating).replace(".", ",") : "Cliente";
      set("gm-cl-sub", (d.rating ? "Cliente · " + ratingTxt : "Cliente"));
      set("gm-cl-profil-sub", "Cliente · " + (d.rides_count || 0) + " course(s)" + (d.rating ? " · " + ratingTxt : ""));
      set("gm-cl-balance", window.gmFmt(d.wallet_balance || 0));
      set("gm-cl-free", d.free_rides || 0);
      set("gm-cl-refcode", esc(d.referral_code || "—"));
      set("gm-cl-refcount", d.referred_count || 0);
      var eb = $("gm-cl-emptybanner");
      if (eb) eb.style.display = (Number(d.wallet_balance) || 0) <= 0 ? "flex" : "none";
      window.__gmRef = d.referral_code;
    }).catch(function () {});
  }

  // ── Lieux enregistrés ─────────────────────────────────────────────────
  function placeRow(p, compact) {
    var addr = esc(p.address || "");
    if (compact) {
      return '<div class="gm-cta gm-cl-pick" data-dest="' + addr + '" style="display:flex;align-items:center;gap:12px;background:var(--color-surface);border:1px solid var(--color-neutral-800);border-radius:13px;padding:12px 14px">' +
        '<span style="width:34px;height:34px;border-radius:10px;background:rgba(145,132,217,.14);display:flex;align-items:center;justify-content:center"><i class="ph-fill ph-map-pin" style="color:var(--color-accent-300);font-size:16px"></i></span>' +
        '<div style="flex:1"><div style="font-size:13px;font-weight:600;color:var(--color-text)">' + esc(p.label) + '</div><div style="font-size:11px;color:var(--color-neutral-500)">' + addr + '</div></div>' +
        '<i class="ph ph-arrow-up-right" style="color:var(--color-neutral-600);font-size:15px"></i></div>';
    }
    return '<div style="display:flex;align-items:center;gap:12px;background:var(--color-surface);border:1px solid var(--color-neutral-800);border-radius:14px;padding:13px 15px">' +
      '<span style="width:38px;height:38px;border-radius:11px;background:rgba(145,132,217,.14);display:flex;align-items:center;justify-content:center;flex-shrink:0"><i class="ph-fill ph-map-pin" style="color:var(--color-accent-300);font-size:17px"></i></span>' +
      '<div style="flex:1"><div style="font-size:13.5px;font-weight:600;color:var(--color-text)">' + esc(p.label) + '</div><div style="font-size:11px;color:var(--color-neutral-500)">' + addr + '</div></div>' +
      '<button class="btn btn-secondary gm-cta gm-cl-pick" data-dest="' + addr + '" style="font-size:11.5px;padding:7px 12px">Y aller</button>' +
      '<button class="btn btn-secondary gm-cta gm-cl-delplace" data-id="' + p.id + '" style="font-size:11.5px;padding:7px 10px;color:#d98a8a"><i class="ph ph-trash"></i></button></div>';
  }

  function loadPlaces() {
    window.gmGetJSON("/api/v1/saved-places/").then(function (d) {
      var list = rows(d);
      set("gm-cl-quickplaces", list.length
        ? list.slice(0, 3).map(function (p) { return placeRow(p, true); }).join("")
        : '<div style="padding:12px;color:var(--color-neutral-500);font-size:12px">Aucun lieu enregistré.</div>');
      set("gm-cl-places", list.length
        ? list.map(function (p) { return placeRow(p, false); }).join("")
        : '<div style="padding:12px;color:var(--color-neutral-500);font-size:12px">Aucun lieu enregistré. Ajoutez-en un ci-dessous.</div>');
    }).catch(function () {});
  }

  // ── Création de course ────────────────────────────────────────────────
  var pickupCoords = { lat: null, lng: null };
  function grabGPS() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(function (pos) {
      pickupCoords.lat = pos.coords.latitude; pickupCoords.lng = pos.coords.longitude;
      var el = $("gm-cl-pickup"); if (el) el.value = "Position actuelle (GPS ✓)";
    }, function () {}, { timeout: 8000 });
  }

  function requestRide(btn) {
    var dest = ($("gm-cl-dest") || {}).value || "";
    if (!dest.trim()) { toast("Saisissez une destination.", "warning"); return; }
    var payload = {
      pickup_address: ($("gm-cl-pickup") || {}).value || "Position actuelle",
      dropoff_address: dest.trim(),
    };
    if (pickupCoords.lat != null) { payload.pickup_latitude = pickupCoords.lat; payload.pickup_longitude = pickupCoords.lng; }
    window.withButtonLoading(btn, function () { return window.gmPostJSON("/api/v1/rides/", payload); })
      .then(function () { go("searching"); startPolling(); })
      .catch(function (err) { toast((err && err.message) || "Impossible de créer la course.", "error"); });
  }

  // ── Suivi de la course active ─────────────────────────────────────────
  var currentRide = null, pollTimer = null;
  function startPolling() { stopPolling(); pollCurrent(); pollTimer = setInterval(pollCurrent, 5000); }
  function stopPolling() { if (pollTimer) clearInterval(pollTimer); pollTimer = null; }

  function pollCurrent() {
    window.gmGetJSON("/api/v1/rides/current/").then(function (d) {
      var r = d.ride;
      currentRide = r;
      if (!r) { stopPolling(); return; }
      set("gm-cl-trip-from", esc(r.pickup_address || "Départ"));
      set("gm-cl-trip-to", esc(r.dropoff_address || "Destination") + (r.agreed_price ? " · " + fc(r.agreed_price) : ""));
      if (r.status === "requested") {
        set("gm-cl-search-sub", "Nous contactons les motards proches. En attente d'acceptation…");
      } else if (r.motard) {
        // Un motard a accepté → écran course en cours
        set("gm-cl-driver", esc(r.motard_name || "Chauffeur"));
        set("gm-cl-driver-sub", "En route vers vous");
        set("gm-cl-driver-av", esc(initials(r.motard_name)));
        var visible = $('[data-panel="ontrip"]');
        if (!visible || visible.style.display === "none") go("ontrip");
        if (r.status === "completed") { stopPolling(); go("rate"); }
      }
    }).catch(function () {});
  }

  // ── Notation ──────────────────────────────────────────────────────────
  var rateValue = 0;
  var RATE_LABELS = { 1: "Décevant", 2: "Passable", 3: "Correct", 4: "Très bien", 5: "Excellent !" };
  function wireStars() {
    document.querySelectorAll(".gm-star").forEach(function (s) {
      s.addEventListener("click", function () {
        rateValue = parseInt(s.getAttribute("data-star"), 10);
        document.querySelectorAll(".gm-star").forEach(function (x) {
          var on = parseInt(x.getAttribute("data-star"), 10) <= rateValue;
          x.className = (on ? "ph-fill ph-star" : "ph ph-star") + " gm-star";
          x.style.color = on ? "#d9a866" : "var(--color-neutral-700)";
        });
        set("gm-cl-ratelabel", RATE_LABELS[rateValue] || "&nbsp;");
      });
    });
  }
  function submitRating(btn) {
    if (!currentRide) { toast("Aucune course à noter.", "warning"); go("home"); return; }
    if (!rateValue) { toast("Choisissez une note.", "warning"); return; }
    var payload = { ride: currentRide.id, score: rateValue, comment: ($("gm-cl-comment") || {}).value || "" };
    window.withButtonLoading(btn, function () { return window.gmPostJSON("/api/v1/ride-ratings/", payload); })
      .then(function () { toast("Merci pour votre avis !", "success"); rateValue = 0; currentRide = null; go("home"); loadSummary(); })
      .catch(function (err) { toast((err && err.message) || "Envoi impossible.", "error"); });
  }

  // ── Portefeuille ──────────────────────────────────────────────────────
  function loadWallet() {
    window.gmGetJSON("/api/v1/wallet/").then(function (d) {
      set("gm-cl-wallet-balance", window.gmFmt(d.balance || 0));
      var t = d.transactions || [];
      set("gm-cl-txns", t.length ? t.map(function (x) {
        var credit = Number(x.amount) >= 0;
        return '<div style="display:flex;align-items:center;gap:12px;background:var(--color-surface);border:1px solid var(--color-neutral-800);border-radius:12px;padding:11px 13px">' +
          '<span style="width:32px;height:32px;border-radius:9px;background:' + (credit ? "rgba(111,174,144,.14)" : "rgba(207,127,127,.14)") + ';display:flex;align-items:center;justify-content:center"><i class="ph-fill ' + (credit ? "ph-arrow-down-left" : "ph-arrow-up-right") + '" style="color:' + (credit ? "#8fceac" : "#d98a8a") + ';font-size:15px"></i></span>' +
          '<div style="flex:1"><div style="font-size:12.5px;font-weight:600;color:var(--color-text)">' + esc(x.kind_display || x.label || "Transaction") + '</div><div style="font-size:10.5px;color:var(--color-neutral-500)">' + esc((x.created_at || "").slice(0, 10)) + '</div></div>' +
          '<div style="font-size:13px;font-weight:700;color:' + (credit ? "#8fceac" : "var(--color-text)") + '">' + (credit ? "+" : "") + fc(x.amount) + '</div></div>';
      }).join("") : '<div style="padding:20px;text-align:center;color:var(--color-neutral-500);font-size:12px;border:1px dashed var(--color-neutral-800);border-radius:14px">Aucune transaction pour le moment.</div>');
    }).catch(function () {});
  }

  var topupProvider = "mpesa";
  function wireTopup() {
    document.querySelectorAll(".gm-cl-amount").forEach(function (s) {
      s.addEventListener("click", function () {
        var amt = s.getAttribute("data-amount");
        var inp = $("gm-cl-topup-amount"); if (inp) inp.value = amt;
        document.querySelectorAll(".gm-cl-amount").forEach(function (x) {
          var on = x === s;
          x.style.background = on ? "var(--color-accent-900)" : "var(--color-bg)";
          x.style.color = on ? "var(--color-accent-200)" : "var(--color-neutral-400)";
          x.style.borderColor = on ? "var(--color-accent-700)" : "var(--color-neutral-800)";
        });
      });
    });
    document.querySelectorAll(".gm-cl-momo").forEach(function (s) {
      s.addEventListener("click", function () {
        topupProvider = s.getAttribute("data-provider");
        document.querySelectorAll(".gm-cl-momo").forEach(function (x) {
          var on = x === s; x.style.borderColor = on ? "var(--color-accent-400)" : "var(--color-neutral-800)";
          var m = x.querySelector(".gm-cl-momomark");
          if (m) { m.className = (on ? "ph-fill ph-check-circle" : "ph ph-circle") + " gm-cl-momomark"; m.style.color = on ? "var(--color-accent-400)" : "var(--color-neutral-700)"; }
        });
      });
    });
    var btn = $("gm-cl-topup-confirm");
    if (btn) btn.addEventListener("click", function () {
      var amt = (($("gm-cl-topup-amount") || {}).value || "").replace(/\s/g, "");
      if (!amt || Number(amt) <= 0) { toast("Montant invalide.", "warning"); return; }
      window.withButtonLoading(btn, function () { return window.gmPostJSON("/api/v1/wallet/", { amount: amt, provider: topupProvider }); })
        .then(function () { toast("Dépôt confirmé.", "success"); go("wallet"); loadSummary(); })
        .catch(function (err) { toast((err && err.message) || "Dépôt impossible.", "error"); });
    });
  }

  // ── Notifications (pas d'endpoint client dédié : état honnête) ─────────
  function loadNotifs() {
    set("gm-cl-notifs", '<div style="padding:22px 10px;text-align:center;color:var(--color-neutral-500);font-size:12.5px;border:1px dashed var(--color-neutral-800);border-radius:14px"><i class="ph ph-bell-slash" style="font-size:22px;display:block;margin-bottom:6px"></i>Aucune notification pour le moment.</div>');
  }

  // ── Compte / mot de passe ─────────────────────────────────────────────
  function loadAccount() {
    window.gmGetJSON("/api/v1/auth/me/").then(function (u) {
      if ($("gm-cl-first")) $("gm-cl-first").value = u.first_name || "";
      if ($("gm-cl-last")) $("gm-cl-last").value = u.last_name || "";
      if ($("gm-cl-email")) $("gm-cl-email").value = u.email || "";
      if ($("gm-cl-phone")) $("gm-cl-phone").value = u.phone_number || "";
    }).catch(function () {});
  }
  function wireAccount() {
    var save = $("gm-cl-account-save");
    if (save) save.addEventListener("click", function () {
      var payload = {
        first_name: ($("gm-cl-first") || {}).value || "",
        last_name: ($("gm-cl-last") || {}).value || "",
        email: ($("gm-cl-email") || {}).value || "",
      };
      window.withButtonLoading(save, function () { return sendJSON("/api/v1/auth/me/", "PATCH", payload); })
        .then(function () { toast("Compte mis à jour.", "success"); loadSummary(); })
        .catch(function () { toast("Mise à jour impossible.", "error"); });
    });
    var pw = $("gm-cl-pw-submit");
    if (pw) pw.addEventListener("click", function () {
      var payload = {
        old_password: ($("gm-cl-pw-old") || {}).value || "",
        new_password: ($("gm-cl-pw-new") || {}).value || "",
        new_password2: ($("gm-cl-pw-new2") || {}).value || "",
      };
      window.withButtonLoading(pw, function () { return window.gmPostJSON("/api/account/password/", payload); })
        .then(function () { toast("Mot de passe mis à jour.", "success"); ["gm-cl-pw-old", "gm-cl-pw-new", "gm-cl-pw-new2"].forEach(function (id) { if ($(id)) $(id).value = ""; }); go("profil"); })
        .catch(function (err) { toast((err && err.message) || "Échec.", "error"); });
    });
  }

  // ── Ajouter / supprimer un lieu ───────────────────────────────────────
  function wirePlaces() {
    var add = $("gm-cl-addplace");
    if (add) add.addEventListener("click", function () {
      var label = window.prompt("Nom du lieu (ex. Maison, Bureau) :");
      if (!label) return;
      var address = window.prompt("Adresse :") || label;
      window.gmPostJSON("/api/v1/saved-places/", { label: label, address: address })
        .then(function () { toast("Lieu enregistré.", "success"); loadPlaces(); })
        .catch(function () { toast("Enregistrement impossible.", "error"); });
    });
  }

  // ── Parrainage : partager / copier ────────────────────────────────────
  function wireReferral() {
    var copy = $("gm-cl-copy");
    if (copy) copy.addEventListener("click", function () {
      var code = window.__gmRef || "";
      if (navigator.clipboard) navigator.clipboard.writeText(code).then(function () { toast("Code copié : " + code, "success"); });
      else toast("Votre code : " + code, "info");
    });
    var share = $("gm-cl-share");
    if (share) share.addEventListener("click", function () {
      var code = window.__gmRef || "";
      var text = "Rejoins-moi sur GO-MBOKA avec mon code " + code + " et gagne des courses gratuites !";
      if (navigator.share) navigator.share({ title: "GO-MBOKA", text: text }).catch(function () {});
      else toast(text, "info");
    });
  }

  // ── Délégation des clics de navigation ────────────────────────────────
  function wireNav() {
    document.addEventListener("click", function (e) {
      var g = e.target.closest && e.target.closest("[data-goto]");
      if (g) { go(g.getAttribute("data-goto")); return; }
      var t = e.target.closest && e.target.closest(".gm-navi");
      if (t) { go(t.getAttribute("data-view")); return; }
      var pick = e.target.closest && e.target.closest(".gm-cl-pick");
      if (pick) { var dst = pick.getAttribute("data-dest"); var el = $("gm-cl-dest"); if (el) el.value = dst; go("create"); return; }
      var del = e.target.closest && e.target.closest(".gm-cl-delplace");
      if (del) {
        sendJSON("/api/v1/saved-places/" + del.getAttribute("data-id") + "/", "DELETE")
          .then(function () { loadPlaces(); }).catch(function () { loadPlaces(); });
        return;
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    wireNav();
    wireStars();
    wireTopup();
    wireAccount();
    wirePlaces();
    wireReferral();
    var rq = $("gm-cl-request"); if (rq) rq.addEventListener("click", function () { requestRide(rq); });
    var cancel = $("gm-cl-cancel"); if (cancel) cancel.addEventListener("click", function () { stopPolling(); go("create"); });
    var arr = $("gm-cl-arrived"); if (arr) arr.addEventListener("click", function () { go("rate"); });
    var rate = $("gm-cl-rate-submit"); if (rate) rate.addEventListener("click", function () { submitRating(rate); });

    go("home");
    loadSummary();
    loadPlaces();
    loadNotifs();
    loadAccount();
    grabGPS();
    // Reprise : si une course est déjà active, on la suit.
    startPolling();
  });
})();
