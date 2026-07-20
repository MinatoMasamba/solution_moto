/* App mobile Propriétaire — navigation par onglets + données réelles (sa flotte). */
(function () {
  "use strict";

  var ICONS = { home: "ph-house", motos: "ph-motorcycle", revenus: "ph-hand-coins", profil: "ph-user" };
  var TABS = ["home", "motos", "revenus", "profil"];

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
  function dset(cls, v) { var el = document.querySelector("." + cls); if (el) el.textContent = v; }

  var MOTOS = {};   // plaque -> data
  var avatar = 'width:32px;height:32px;border-radius:50%;background:var(--color-neutral-800);display:flex;align-items:center;justify-content:center;font-size:10.5px;font-weight:600;color:var(--color-neutral-100)';

  var STATUS_COLOR = {
    available: ["#8fceac", "rgba(111,174,144,.14)"],
    assigned: ["var(--color-accent-200)", "rgba(145,132,217,.14)"],
    maintenance: ["#d9a866", "rgba(217,168,102,.14)"],
    retired: ["var(--color-neutral-400)", "var(--color-neutral-800)"],
  };
  function badge(statusDisplay, status) {
    var c = STATUS_COLOR[status] || ["var(--color-neutral-300)", "var(--color-neutral-800)"];
    return '<span style="font-size:10.5px;font-weight:600;color:' + c[0] + ';background:' + c[1] + ';padding:3px 9px;border-radius:20px">' + esc(statusDisplay || status || "—") + "</span>";
  }

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
      var moto = e.target.closest && e.target.closest("[data-moto]");
      if (moto) { openMoto(moto.getAttribute("data-moto")); return; }
      var tab = e.target.closest && e.target.closest(".gm-navi[data-view]");
      if (tab) { go(tab.getAttribute("data-view")); return; }
      var goto = e.target.closest && e.target.closest("[data-goto]");
      if (goto) { go(goto.getAttribute("data-goto")); return; }
    });
  }

  // ---------------------------------------------------------------- détail moto
  function openMoto(plaque) {
    var m = MOTOS[plaque];
    if (!m) return;
    dset("gm-d-plaque", m.plate_number || "—");
    dset("gm-d-moto", [m.brand, m.model_style, m.color].filter(Boolean).join(" · ") || "—");
    dset("gm-d-formule", m.ownership_type_display || "—");
    dset("gm-d-chauf", m.assigned_motard_name || "Non affectée");
    dset("gm-d-statut", m.status_display || "—");
    dset("gm-d-comm", window.gmFmt(m.commission_rate || 0) + " %");
    dset("gm-d-color", m.color || "—");
    dset("gm-d-brand", [m.brand, m.model_style].filter(Boolean).join(" ") || "—");
    dset("gm-d-cond", (m.general_condition != null ? m.general_condition + " / 10" : "—"));
    dset("gm-d-acq", m.acquisition_date || "—");
    dset("gm-d-imei", m.device_id || "—");
    go("motodetail");
  }

  // ---------------------------------------------------------------- data
  function loadDashboard() {
    window.gmGetJSON("/api/dashboard/owner/").then(function (d) {
      var k = d.kpis || {};
      setText("gm-m-bikes", window.gmFmt(k.total_bikes || 0));
      var comm = d.commissions || [];
      var gross = 0, net = 0;
      comm.forEach(function (c) { gross += Number(c.gross_revenue || 0); net += Number(c.net_to_remit || 0); });
      setText("gm-m-gross", fc(gross));
      setText("gm-m-net", fc(net));
      setText("gm-m-revnet", fc(net));
    }).catch(function () {
      ["gm-m-bikes", "gm-m-gross", "gm-m-net", "gm-m-revnet"].forEach(function (id) { setText(id, "—"); });
    });
  }

  function motoCard(m) {
    var name = m.assigned_motard_name;
    var driver = name
      ? '<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px"><span style="width:26px;height:26px;border-radius:50%;background:var(--color-neutral-800);display:flex;align-items:center;justify-content:center;font-size:9.5px;font-weight:600;color:var(--color-neutral-200)">' + esc(initials(name)) + '</span><span style="font-size:12px;color:var(--color-neutral-300)">' + esc(name) + "</span></div>"
      : '<div style="display:flex;align-items:center;gap:7px;font-size:12px;color:var(--color-neutral-500);margin-bottom:12px"><i class="ph ph-user"></i>Non affectée</div>';
    return '<div class="gm-cta" data-moto="' + esc(m.plate_number) + '" style="background:var(--color-surface);border:1px solid var(--color-neutral-800);border-radius:15px;padding:16px">' +
      '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px"><span style="font-family:ui-monospace,monospace;font-size:14px;font-weight:700;color:var(--color-text)">' + esc(m.plate_number || "—") + "</span>" + badge(m.status_display, m.status) + "</div>" +
      '<div style="font-size:12px;color:var(--color-neutral-400);margin-bottom:10px">' + esc([m.brand, m.model_style, m.color].filter(Boolean).join(" · ") || "—") + "</div>" +
      driver +
      '<div style="display:flex;justify-content:space-between;padding-top:11px;border-top:1px solid var(--color-neutral-800)"><span style="font-size:11.5px;color:var(--color-neutral-500)">' + esc(m.ownership_type_display || "Formule") + '</span><span style="font-size:12.5px;font-weight:600;color:var(--color-text)">' + window.gmFmt(m.commission_rate || 0) + "% comm.</span></div></div>";
  }

  function loadMotos() {
    window.gmGetJSON("/api/v1/motorcycles/").then(function (d) {
      var list = rows(d);
      MOTOS = {};
      list.forEach(function (m) { if (m.plate_number) MOTOS[m.plate_number] = m; });

      if (!list.length) {
        set("gm-m-motos", '<div style="padding:18px;color:var(--color-neutral-500);font-size:13px">Aucune moto dans votre flotte.</div>');
      } else {
        set("gm-m-motos", list.map(motoCard).join(""));
      }

      // Par chauffeur (motos affectées)
      var withDriver = list.filter(function (m) { return m.assigned_motard_name; });
      if (!withDriver.length) {
        set("gm-m-perchauf", '<div style="padding:14px;color:var(--color-neutral-500);font-size:12px">Aucun chauffeur affecté.</div>');
      } else {
        set("gm-m-perchauf", withDriver.map(function (m) {
          var name = m.assigned_motard_name;
          return '<div style="background:var(--color-surface);border:1px solid var(--color-neutral-800);border-radius:13px;padding:13px 15px"><div style="display:flex;align-items:center;gap:11px"><span style="' + avatar + '">' + esc(initials(name)) + '</span><div style="flex:1"><div style="font-size:13px;font-weight:600;color:var(--color-text)">' + esc(name) + '</div><div style="font-size:11px;color:var(--color-neutral-500);font-family:ui-monospace,monospace">' + esc(m.plate_number) + " · " + esc(m.ownership_type_display || "") + '</div></div><span style="font-size:11px;font-weight:600;color:var(--color-accent-200);background:rgba(145,132,217,.14);padding:3px 9px;border-radius:20px">' + window.gmFmt(m.commission_rate || 0) + "%</span></div></div>";
        }).join(""));
      }
    }).catch(function () {
      set("gm-m-motos", '<div style="padding:18px;color:#d98a8a;font-size:13px">Erreur de chargement.</div>');
      set("gm-m-perchauf", '<div style="padding:14px;color:#d98a8a;font-size:12px">Erreur de chargement.</div>');
    });
  }

  function loadHistory() {
    window.gmGetJSON("/api/v1/fleet-remittances/").then(function (d) {
      var list = rows(d);
      if (!list.length) {
        set("gm-m-history", '<div style="padding:14px;color:var(--color-neutral-500);font-size:12px">Aucun reversement pour le moment.</div>');
        return;
      }
      set("gm-m-history", list.map(function (r) {
        var period = r.period_end || r.period_start || (r.created_at ? r.created_at.slice(0, 10) : "—");
        return '<div style="display:flex;align-items:center;gap:12px;background:var(--color-surface);border:1px solid var(--color-neutral-800);border-radius:13px;padding:12px 14px"><span style="width:34px;height:34px;border-radius:10px;background:rgba(111,174,144,.14);display:flex;align-items:center;justify-content:center"><i class="ph-fill ph-check-circle" style="color:#8fceac;font-size:16px"></i></span><div style="flex:1"><div style="font-size:13px;font-weight:600;color:var(--color-text)">' + esc(period) + '</div><div style="font-size:11px;color:var(--color-neutral-500)">' + esc(r.plate_number || "") + " · brut " + fc(r.gross_revenue) + '</div></div><div style="text-align:right"><div style="font-size:13px;font-weight:700;color:var(--color-text)">' + fc(r.net_amount) + "</div></div></div>";
      }).join(""));
    }).catch(function () {
      set("gm-m-history", '<div style="padding:14px;color:#d98a8a;font-size:12px">Erreur de chargement.</div>');
    });
  }

  function loadMe() {
    window.gmGetJSON("/api/v1/auth/me/").then(function (u) {
      var name = ((u.first_name || "") + " " + (u.last_name || "")).trim();
      if (name) setVal("gm-m-set-name", name);
      if (u.phone_number) setVal("gm-m-set-phone", u.phone_number);
      if (u.email) setVal("gm-m-set-email", u.email);
    }).catch(function () {});
  }

  function wirePassword() {
    var btn = document.getElementById("gm-m-pw-btn");
    if (!btn) return;
    btn.addEventListener("click", function () {
      window.gmPostJSON("/api/account/password/", {
        old_password: (document.getElementById("gm-m-pw-old") || {}).value || "",
        new_password: (document.getElementById("gm-m-pw-new") || {}).value || "",
        new_password2: (document.getElementById("gm-m-pw-new2") || {}).value || "",
      }).then(function () {
        if (window.showAppToast) window.showAppToast("Mot de passe mis à jour.", "success");
        ["gm-m-pw-old", "gm-m-pw-new", "gm-m-pw-new2"].forEach(function (id) { var e = document.getElementById(id); if (e) e.value = ""; });
      }).catch(function (err) {
        if (window.showAppToast) window.showAppToast(err.message || "Échec de la mise à jour.", "error");
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    setupNav();
    go("home");
    loadDashboard();
    loadMotos();
    loadHistory();
    loadMe();
    wirePassword();
  });
})();
