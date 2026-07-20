/* App Chauffeur (motard) — navigation par onglets + données réelles. */
(function () {
  "use strict";

  var ICONS = { home: "ph-house", moto: "ph-motorcycle", gains: "ph-wallet", profil: "ph-user" };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function initials(name) {
    var p = String(name || "").trim().split(/\s+/);
    return (((p[0] || "")[0] || "") + ((p[1] || "")[0] || "")).toUpperCase() || "?";
  }
  function fc(n) { return window.gmFmt(Math.round(n || 0)) + " FC"; }
  function rows(data) { return (data && (data.results || data)) || []; }
  function set(id, html) { var el = document.getElementById(id); if (el) el.innerHTML = html; }
  function setText(id, t) { var el = document.getElementById(id); if (el) el.textContent = t; }
  function setVal(id, v) { var el = document.getElementById(id); if (el) el.value = v; }
  function hhmm(iso) { return iso ? new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" }) : "—"; }

  var profileId = null;
  var isAvailable = false;
  var activeRide = null;   // course acceptée en cours

  // ---------------------------------------------------------------- navigation
  function go(v) {
    document.querySelectorAll("[data-panel]").forEach(function (p) {
      p.style.display = p.getAttribute("data-panel") === v ? "" : "none";
    });
    document.querySelectorAll(".gm-navi").forEach(function (n) {
      var key = n.getAttribute("data-view");
      var on = key === v;
      n.style.color = on ? "var(--color-accent-300)" : "var(--color-neutral-500)";
      var ic = n.querySelector("i");
      if (ic && ICONS[key]) { ic.className = (on ? "ph-fill " : "ph ") + ICONS[key]; ic.style.fontSize = "21px"; }
    });
    var sc = document.getElementById("gm-scroll"); if (sc) sc.scrollTop = 0;
  }

  function setupNav() {
    document.addEventListener("click", function (e) {
      var tab = e.target.closest && e.target.closest(".gm-navi[data-view]");
      if (tab) { go(tab.getAttribute("data-view")); return; }
      var goto = e.target.closest && e.target.closest("[data-goto]");
      if (goto) { go(goto.getAttribute("data-goto")); return; }
    });
  }

  // ---------------------------------------------------------------- GPS temps réel
  function sendPosition() {
    if (!isAvailable || !navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(function (pos) {
      window.gmPostJSON("/api/v1/location-pings/", {
        latitude: pos.coords.latitude,
        longitude: pos.coords.longitude
      }).catch(function () {});
    }, function (err) {
      console.warn("Géolocalisation échouée :", err);
    }, { enableHighAccuracy: true, timeout: 5000 });
  }

  // ---------------------------------------------------------------- disponibilité
  function renderAvail() {
    var dot = document.getElementById("gm-avail-dot");
    var sw = document.getElementById("gm-avail-switch");
    var knob = document.getElementById("gm-avail-knob");
    setText("gm-avail-title", isAvailable ? "Vous êtes en ligne" : "Hors ligne");
    setText("gm-avail-sub", isAvailable ? "Vous recevez des courses" : "Touchez pour passer en ligne");
    if (dot) { dot.style.background = isAvailable ? "#6fae90" : "var(--color-neutral-600)"; dot.style.animation = isAvailable ? "gmPulse 1.6s infinite" : "none"; }
    if (sw) sw.style.background = isAvailable ? "#6fae90" : "var(--color-neutral-700)";
    if (knob) { knob.style.left = isAvailable ? "auto" : "2px"; knob.style.right = isAvailable ? "2px" : "auto"; }
  }

  function wireAvail() {
    var el = document.getElementById("gm-avail");
    if (!el) return;
    el.addEventListener("click", function () {
      if (profileId == null) return;
      var next = !isAvailable;
      window.gmPostJSON;  // noop (garde gmPostJSON chargé)
      window.fetchWithTimeout("/api/v1/motard-profiles/" + profileId + "/", {
        method: "PATCH",
        headers: { "Content-Type": "application/json", "X-CSRFToken": window.gmCsrf() },
        body: JSON.stringify({ is_available: next }),
      }).then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
        .then(function (res) {
          if (!res.ok) throw new Error((res.d && res.d.detail) || "Erreur");
          isAvailable = !!res.d.is_available;
          renderAvail();
          if (window.showAppToast) window.showAppToast(isAvailable ? "Vous êtes en ligne." : "Vous êtes hors ligne.", "success");
        }).catch(function (err) {
          if (window.showAppToast) window.showAppToast(err.message || "Échec.", "error");
        });
    });
  }

  // ---------------------------------------------------------------- dashboard KPIs
  function loadDashboard() {
    window.gmGetJSON("/api/dashboard/motard/").then(function (d) {
      var k = d.kpis || {};
      setText("gm-c-today", fc(k.today_earnings));
      setText("gm-c-today-sub", (k.today_rides || 0) + " course" + ((k.today_rides || 0) > 1 ? "s" : ""));
      setText("gm-c-today2", fc(k.today_earnings));
      setText("gm-c-week", fc(k.week_earnings));
      setText("gm-c-week-sub", (k.week_rides || 0) + " course" + ((k.week_rides || 0) > 1 ? "s" : "") + " cette semaine");
      setText("gm-c-total", window.gmFmt(k.total_rides || 0));
      setText("gm-c-rating", Number(k.rating || 0).toFixed(1).replace(".", ","));
      setText("gm-c-rating-sub", "· " + (k.total_rides || 0) + " courses");

      var active = k.subscription_status === "active";
      var alert = document.getElementById("gm-sub-alert");
      if (alert) alert.style.display = active ? "none" : "flex";
      setText("gm-c-sub", active ? "Motard actif · en service" : "Abonnement inactif");
    }).catch(function () {});
  }

  // ---------------------------------------------------------------- profil / dispo initial
  function loadProfile() {
    window.gmGetJSON("/api/v1/motard-profiles/").then(function (d) {
      var list = rows(d);
      var p = list[0];
      if (!p) return;
      profileId = p.id;
      isAvailable = !!p.is_available;
      renderAvail();
    }).catch(function () {});
  }

  // ---------------------------------------------------------------- demande de course
  function requestCard(r) {
    return '<div style="background:var(--color-surface);border:1px solid var(--color-accent-700);border-radius:16px;overflow:hidden">' +
      '<div style="padding:14px 17px 12px;border-bottom:1px solid var(--color-neutral-800);display:flex;align-items:center;gap:8px"><span style="width:8px;height:8px;border-radius:50%;background:var(--color-accent-400);animation:gmPulse 1.4s infinite"></span><span style="font-size:13px;font-weight:600;color:var(--color-accent-200)">Nouvelle demande de course</span></div>' +
      '<div style="padding:15px 17px">' +
      '<div style="display:flex;align-items:center;gap:10px;margin-bottom:9px"><i class="ph-fill ph-circle" style="color:#6fae90;font-size:11px"></i><div style="font-size:13px;color:var(--color-text)">' + esc(r.pickup_address || "—") + "</div></div>" +
      '<div style="width:1px;height:12px;background:var(--color-neutral-700);margin-left:5px"></div>' +
      '<div style="display:flex;align-items:center;gap:10px;margin-top:9px;margin-bottom:14px"><i class="ph-fill ph-map-pin" style="color:var(--color-accent-400);font-size:12px"></i><div style="font-size:13px;color:var(--color-text)">' + esc(r.dropoff_address || "—") + "</div></div>" +
      '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px"><div><div style="font-size:11px;color:var(--color-neutral-500)">Prix proposé</div><div style="font-size:18px;font-weight:700;color:var(--color-text)">' + (r.agreed_price ? fc(r.agreed_price) : "À négocier") + "</div></div></div>" +
      '<div style="display:flex;gap:10px"><button class="btn btn-secondary" data-refuse="' + r.id + '" style="flex:1;font-size:13px;padding:10px">Refuser</button><button class="btn btn-primary" data-accept="' + r.id + '" style="flex:1.4;font-size:13px;padding:10px">Accepter</button></div>' +
      "</div></div>";
  }

  function loadRequests() {
    // Course déjà acceptée/en cours ?
    window.gmGetJSON("/api/v1/rides/").then(function (d) {
      var list = rows(d);
      var mine = list.filter(function (r) { return r.motard && (r.status === "accepted" || r.status === "ongoing"); });
      if (mine.length) { activeRide = mine[0]; }

      var wrap = document.getElementById("gm-c-request-wrap");
      if (!wrap) return;

      if (activeRide) {
        wrap.innerHTML = '<div class="gm-cta" data-goto="course" style="background:var(--color-surface);border:1px solid var(--color-accent-700);border-radius:16px;padding:15px 17px;display:flex;align-items:center;gap:12px"><span style="width:36px;height:36px;border-radius:10px;background:rgba(145,132,217,.14);display:flex;align-items:center;justify-content:center"><i class="ph-fill ph-path" style="color:var(--color-accent-300);font-size:17px"></i></span><div style="flex:1"><div style="font-size:13px;font-weight:600;color:var(--color-text)">Course en cours</div><div style="font-size:11.5px;color:var(--color-neutral-500)">' + esc(activeRide.pickup_address || "") + " → " + esc(activeRide.dropoff_address || "") + '</div></div><i class="ph ph-caret-right" style="color:var(--color-neutral-500)"></i></div>';
        fillCourse(activeRide);
        return;
      }

      var requests = list.filter(function (r) { return r.status === "requested"; });
      if (!requests.length) {
        wrap.innerHTML = '<div style="background:var(--color-surface);border:1px solid var(--color-neutral-800);border-radius:16px;padding:18px;text-align:center;color:var(--color-neutral-500);font-size:12.5px"><i class="ph ph-path" style="font-size:22px;display:block;margin-bottom:6px"></i>Aucune demande pour le moment</div>';
      } else {
        wrap.innerHTML = requestCard(requests[0]);
      }
    }).catch(function () {});
  }

  function wireRideActions() {
    document.addEventListener("click", function (e) {
      var acc = e.target.closest && e.target.closest("[data-accept]");
      if (acc) {
        var id = acc.getAttribute("data-accept");
        window.withButtonLoading(acc, function () {
          return window.gmPostJSON("/api/v1/rides/" + id + "/accept/", {});
        }).then(function (ride) {
          activeRide = ride;
          fillCourse(ride);
          if (window.showAppToast) window.showAppToast("Course acceptée.", "success");
          loadRequests();
          go("course");
        }).catch(function () {});
        return;
      }
      var ref = e.target.closest && e.target.closest("[data-refuse]");
      if (ref) {
        var w = document.getElementById("gm-c-request-wrap");
        if (w) w.innerHTML = '<div style="background:var(--color-surface);border:1px solid var(--color-neutral-800);border-radius:16px;padding:18px;text-align:center;color:var(--color-neutral-500);font-size:12.5px">Demande ignorée</div>';
        return;
      }
    });

    var startBtn = document.getElementById("gm-course-start");
    if (startBtn) startBtn.addEventListener("click", function () {
      if (!activeRide) return;
      window.withButtonLoading(startBtn, function () {
        return window.gmPostJSON("/api/v1/rides/" + activeRide.id + "/start/", {});
      }).then(function (ride) { activeRide = ride; if (window.showAppToast) window.showAppToast("Course démarrée.", "success"); }).catch(function () {});
    });

    var doneBtn = document.getElementById("gm-course-complete");
    if (doneBtn) doneBtn.addEventListener("click", function () {
      if (!activeRide) return;
      window.withButtonLoading(doneBtn, function () {
        return window.gmPostJSON("/api/v1/rides/" + activeRide.id + "/complete/", {});
      }).then(function () {
        if (window.showAppToast) window.showAppToast("Course terminée. Bravo !", "success");
        activeRide = null;
        go("home");
        loadDashboard(); loadRequests(); loadRides();
      }).catch(function () {});
    });
  }

  function fillCourse(r) {
    setText("gm-course-client", r.client_name || "Client");
    setText("gm-course-price", r.agreed_price ? fc(r.agreed_price) : "Prix à négocier");
    setText("gm-course-pickup", r.pickup_address || "—");
    setText("gm-course-dropoff", r.dropoff_address || "—");
    var av = document.getElementById("gm-course-avatar");
    if (av) av.textContent = initials(r.client_name);
  }

  // ---------------------------------------------------------------- ma moto + contrat
  function loadMoto() {
    Promise.all([
      window.gmGetJSON("/api/v1/motorcycles/").catch(function () { return []; }),
      window.gmGetJSON("/api/v1/agreements/").catch(function () { return []; }),
    ]).then(function (res) {
      var motos = rows(res[0]);
      var agreements = rows(res[1]);
      var wrap = document.getElementById("gm-moto-wrap");
      if (!wrap) return;

      if (!motos.length) {
        wrap.innerHTML = '<div style="background:var(--color-surface);border:1px solid var(--color-neutral-800);border-radius:16px;padding:22px;text-align:center;color:var(--color-neutral-500);font-size:13px"><i class="ph ph-motorcycle" style="font-size:26px;display:block;margin-bottom:8px"></i>Aucune moto ne vous est affectée pour le moment.</div>';
        return;
      }
      var m = motos[0];
      var ag = agreements[0];

      var html = '<div style="background:var(--color-surface);border:1px solid var(--color-neutral-800);border-radius:16px;padding:18px;margin-bottom:16px">' +
        '<div style="display:flex;align-items:center;gap:13px;margin-bottom:14px"><span style="width:48px;height:48px;border-radius:13px;background:rgba(145,132,217,.14);display:flex;align-items:center;justify-content:center"><i class="ph-fill ph-motorcycle" style="color:var(--color-accent-300);font-size:24px"></i></span><div><div style="font-size:15px;font-weight:600;color:var(--color-text)">' + esc([m.brand, m.model_style].filter(Boolean).join(" ") || "Ma moto") + '</div><div style="font-size:12px;color:var(--color-neutral-500);font-family:ui-monospace,monospace">' + esc(m.plate_number || "") + (m.color ? " · " + esc(m.color) : "") + '</div></div></div>' +
        '<div style="display:flex;gap:8px;flex-wrap:wrap"><span style="font-size:11px;font-weight:600;color:var(--color-accent-200);background:rgba(145,132,217,.14);padding:4px 11px;border-radius:20px">' + esc(m.ownership_type_display || "") + '</span><span style="font-size:11px;font-weight:600;color:#8fceac;background:rgba(111,174,144,.14);padding:4px 11px;border-radius:20px">' + esc(m.status_display || "") + "</span></div></div>";

      html += '<div style="background:var(--color-surface);border:1px solid var(--color-neutral-800);border-radius:16px;padding:16px 18px;margin-bottom:16px">' +
        '<div style="font-size:13px;font-weight:600;color:var(--color-text);margin-bottom:14px">Suivi de la moto</div>' +
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px 16px">' +
        detailCell("Immatriculation", m.plate_number || "—") +
        detailCell("État général", (m.general_condition != null ? m.general_condition + " / 10" : "—")) +
        detailCell("Marque / modèle", [m.brand, m.model_style].filter(Boolean).join(" ") || "—") +
        detailCell("Acquisition", m.acquisition_date || "—") +
        "</div></div>";

      if (ag) {
        var target = Number(ag.target_total_amount || 0);
        var paid = Number(ag.amount_already_paid || 0);
        var pct = target > 0 ? Math.min(100, Math.round((paid / target) * 100)) : null;
        var rest = target > 0 ? Math.max(0, target - paid) : null;
        var isHP = ag.agreement_type === "hire_purchase";
        html += '<div style="background:linear-gradient(160deg,var(--color-accent-900),var(--color-surface));border:1px solid var(--color-accent-700);border-radius:16px;padding:18px;margin-bottom:16px">' +
          '<div style="font-size:13px;font-weight:600;color:var(--color-text);margin-bottom:4px">' + (isHP ? "Contrat d'acquisition" : "Location") + '</div>' +
          '<div style="font-size:12px;color:var(--color-neutral-400);margin-bottom:14px">' + (isHP ? "À la fin des versements, la moto vous appartient." : "Vous versez une redevance ; la moto reste au propriétaire.") + "</div>";
        if (pct !== null) {
          html += '<div style="display:flex;align-items:baseline;justify-content:space-between;margin-bottom:8px"><span style="font-size:12px;color:var(--color-neutral-400)">Progression</span><span style="font-size:13px;font-weight:700;color:var(--color-accent-200)">' + pct + '%</span></div>' +
            '<div style="height:9px;border-radius:6px;background:var(--color-neutral-800);overflow:hidden;margin-bottom:14px"><div style="width:' + pct + '%;height:100%;border-radius:6px;background:linear-gradient(90deg,var(--color-accent-400),#6fae90)"></div></div>' +
            '<div style="display:flex;justify-content:space-between"><div><div style="font-size:11px;color:var(--color-neutral-500)">Payé</div><div style="font-size:15px;font-weight:700;color:var(--color-text)">' + fc(paid) + '</div></div><div style="text-align:right"><div style="font-size:11px;color:var(--color-neutral-500)">Reste dû</div><div style="font-size:15px;font-weight:700;color:var(--color-text)">' + fc(rest) + "</div></div></div>";
        }
        html += '<div style="display:flex;justify-content:space-between;margin-top:14px;padding-top:14px;border-top:1px solid var(--color-neutral-800)"><span style="font-size:12.5px;color:var(--color-neutral-400)">Versement (' + esc(ag.frequency || "") + ')</span><span style="font-size:13px;font-weight:600;color:var(--color-text)">' + fc(ag.periodic_amount) + "</span></div></div>";
      } else {
        html += '<div style="background:var(--color-surface);border:1px solid var(--color-neutral-800);border-radius:16px;padding:16px 18px;color:var(--color-neutral-500);font-size:12.5px">Aucun contrat de location/achat enregistré pour cette moto.</div>';
      }

      wrap.innerHTML = html;
    });
  }

  function detailCell(label, value) {
    return '<div><div style="font-size:11px;color:var(--color-neutral-500);margin-bottom:2px">' + esc(label) + '</div><div style="font-size:13.5px;font-weight:600;color:var(--color-text)">' + esc(value) + "</div></div>";
  }

  // ---------------------------------------------------------------- gains (courses terminées)
  function loadRides() {
    window.gmGetJSON("/api/v1/rides/?status=completed").then(function (d) {
      var list = rows(d).filter(function (r) { return r.status === "completed"; });
      if (!list.length) {
        set("gm-c-rides", '<div style="padding:14px;color:var(--color-neutral-500);font-size:12px">Aucune course terminée.</div>');
        return;
      }
      set("gm-c-rides", list.slice(0, 15).map(function (r) {
        return '<div style="display:flex;align-items:center;gap:12px;background:var(--color-surface);border:1px solid var(--color-neutral-800);border-radius:13px;padding:12px 14px"><span style="width:34px;height:34px;border-radius:10px;background:rgba(145,132,217,.14);display:flex;align-items:center;justify-content:center"><i class="ph-fill ph-path" style="color:var(--color-accent-300);font-size:16px"></i></span><div style="flex:1"><div style="font-size:13px;font-weight:600;color:var(--color-text)">' + esc(r.pickup_address || "?") + " → " + esc(r.dropoff_address || "?") + '</div><div style="font-size:11px;color:var(--color-neutral-500)">' + hhmm(r.completed_at || r.requested_at) + '</div></div><div style="font-size:13px;font-weight:600;color:var(--color-text)">' + (r.agreed_price ? fc(r.agreed_price) : "—") + "</div></div>";
      }).join(""));
    }).catch(function () {
      set("gm-c-rides", '<div style="padding:14px;color:#d98a8a;font-size:12px">Erreur de chargement.</div>');
    });
  }

  // ---------------------------------------------------------------- notifications
  function loadNotifs() {
    window.gmGetJSON("/api/dashboard/notifications/").then(function (d) {
      var list = rows(d);
      if (!list.length) {
        set("gm-c-notifs", '<div style="padding:14px;color:var(--color-neutral-500);font-size:12px">Aucune notification.</div>');
        return;
      }
      set("gm-c-notifs", list.map(function (n) {
        return '<div style="display:flex;gap:12px;background:var(--color-surface);border:1px solid var(--color-neutral-800);border-radius:14px;padding:13px 15px"><span style="width:36px;height:36px;border-radius:10px;background:rgba(145,132,217,.14);display:flex;align-items:center;justify-content:center;flex-shrink:0"><i class="ph-fill ph-bell" style="color:var(--color-accent-300);font-size:16px"></i></span><div style="flex:1"><div style="font-size:13px;font-weight:600;color:var(--color-text)">' + esc(n.title || n.message || "Notification") + '</div><div style="font-size:11.5px;color:var(--color-neutral-500)">' + esc(n.detail || n.subtitle || "") + "</div></div></div>";
      }).join(""));
    }).catch(function () {
      set("gm-c-notifs", '<div style="padding:14px;color:var(--color-neutral-500);font-size:12px">Aucune notification.</div>');
    });
  }

  // ---------------------------------------------------------------- compte / password
  function wireAccount() {
    var save = document.getElementById("gm-c-save");
    if (save) save.addEventListener("click", function () {
      window.withButtonLoading(save, function () {
        return window.fetchWithTimeout("/api/v1/auth/me/", {
          method: "PATCH",
          headers: { "Content-Type": "application/json", "X-CSRFToken": window.gmCsrf() },
          body: JSON.stringify({
            first_name: (document.getElementById("gm-c-first") || {}).value || "",
            last_name: (document.getElementById("gm-c-last") || {}).value || "",
            email: (document.getElementById("gm-c-email") || {}).value || "",
          }),
        }).then(function (r) { if (!r.ok) throw new Error("Échec"); return r.json(); });
      }).then(function () {
        if (window.showAppToast) window.showAppToast("Compte mis à jour.", "success");
      }).catch(function () {});
    });

    var pwBtn = document.getElementById("gm-c-pw-btn");
    if (pwBtn) pwBtn.addEventListener("click", function () {
      window.gmPostJSON("/api/account/password/", {
        old_password: (document.getElementById("gm-c-pw-old") || {}).value || "",
        new_password: (document.getElementById("gm-c-pw-new") || {}).value || "",
        new_password2: (document.getElementById("gm-c-pw-new2") || {}).value || "",
      }).then(function () {
        if (window.showAppToast) window.showAppToast("Mot de passe mis à jour.", "success");
        ["gm-c-pw-old", "gm-c-pw-new", "gm-c-pw-new2"].forEach(function (id) { var e = document.getElementById(id); if (e) e.value = ""; });
      }).catch(function (err) {
        if (window.showAppToast) window.showAppToast(err.message || "Échec.", "error");
      });
    });
  }

  // ---------------------------------------------------------------- retrait
  var defaultMethod = null;

  function loadWithdrawDest() {
    window.gmGetJSON("/api/v1/payment-methods/").then(function (d) {
      var items = rows(d);
      defaultMethod = items.filter(function (m) { return m.is_default; })[0] || items[0] || null;
      var el = document.getElementById("gm-c-withdraw-dest");
      if (!el) return;
      el.textContent = defaultMethod
        ? "Vers " + (defaultMethod.label || "votre moyen par défaut")
        : "Aucun moyen de paiement — reliez-en un d'abord.";
    }).catch(function () {});
  }

  function wireWithdraw() {
    var btn = document.getElementById("gm-c-withdraw");
    if (!btn) return;
    btn.addEventListener("click", function () {
      if (!defaultMethod) {
        if (window.showAppToast) window.showAppToast("Ajoutez d'abord un moyen de paiement.", "warning");
        go("paiement");
        return;
      }
      if (window.showAppToast) {
        window.showAppToast("Demande de retrait envoyée vers " + (defaultMethod.label || "votre compte") + ". Traitement sous 24 h.", "success");
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    setupNav();
    go("home");
    wireAvail();
    wireRideActions();
    wireAccount();
    wireWithdraw();
    loadProfile();
    loadDashboard();
    loadRequests();
    loadMoto();
    loadRides();
    loadNotifs();
    loadWithdrawDest();
    setInterval(sendPosition, 10000);
  });
})();
