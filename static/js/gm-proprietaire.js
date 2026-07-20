/* Console Propriétaire de motos — chargement des données réelles (sa flotte). */
(function () {
  "use strict";

  var TITLES = {
    overview: ["Vue d'ensemble", "Ma flotte · Kinshasa"],
    motos: ["Mes motos", "Toutes mes motos"],
    motards: ["Mes chauffeurs", "Chauffeurs affectés à mes motos"],
    revenus: ["Revenus & reversements", "Net reçu et historique"],
    contrats: ["Contrats & formules", "Location & contrat d'achat"],
    support: ["Support", "Aide et contact"],
    reglages: ["Réglages", "Mon compte propriétaire"],
    motdepasse: ["Sécurité", "Changer mon mot de passe"],
  };

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
  function setText(id, txt) { var el = document.getElementById(id); if (el) el.textContent = txt; }
  function setVal(id, v) { var el = document.getElementById(id); if (el) el.value = v; }

  var avatar = 'width:24px;height:24px;border-radius:50%;background:var(--color-neutral-800);display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:600;color:var(--color-neutral-200)';

  function statusBadge(statusDisplay, status) {
    var map = {
      available: ["#8fceac", "rgba(111,174,144,.14)"],
      assigned: ["var(--color-accent-200)", "rgba(145,132,217,.14)"],
      maintenance: ["#d9a866", "rgba(217,168,102,.14)"],
      retired: ["var(--color-neutral-400)", "var(--color-neutral-800)"],
    };
    var c = map[status] || ["var(--color-neutral-300)", "var(--color-neutral-800)"];
    return '<span style="font-size:11px;font-weight:600;color:' + c[0] + ';background:' + c[1] + ';padding:3px 9px;border-radius:20px">' + esc(statusDisplay || status || "—") + "</span>";
  }

  // ---- KPIs + reversements (dashboard owner) ----
  function loadDashboard() {
    window.gmGetJSON("/api/dashboard/owner/").then(function (d) {
      var k = d.kpis || {};
      setText("gr-kpi-bikes", window.gmFmt(k.total_bikes || 0));
      setText("gr-kpi-motards", window.gmFmt(k.active_motards || 0));

      var comm = d.commissions || [];
      var gross = 0, net = 0;
      comm.forEach(function (c) { gross += Number(c.gross_revenue || 0); net += Number(c.net_to_remit || 0); });
      setText("gr-kpi-gross", fc(gross));
      setText("gr-kpi-net", fc(net));
      setText("gr-rev-net", fc(net));
      setText("gr-rev-gross", fc(gross));
    }).catch(function () {
      ["gr-kpi-bikes", "gr-kpi-gross", "gr-kpi-net", "gr-kpi-motards"].forEach(function (id) { setText(id, "—"); });
    });
  }

  // ---- Motos (overview table + cards) ----
  function motoCard(m) {
    var name = m.assigned_motard_name;
    var driver = name
      ? '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px"><span style="' + avatar + '">' + esc(initials(name)) + '</span><span style="font-size:12px;color:var(--color-neutral-300)">' + esc(name) + "</span></div>"
      : '<div style="display:flex;align-items:center;gap:8px;color:var(--color-neutral-500);font-size:12px;margin-bottom:6px"><i class="ph ph-user"></i>Non affectée</div>';
    var descBits = [m.brand, m.model_style, m.color].filter(Boolean).join(" · ") || "—";
    return '<div class="gm-card" style="background:var(--color-surface);border:1px solid var(--color-neutral-800);border-radius:16px;padding:18px">' +
      '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px"><span style="font-family:ui-monospace,monospace;font-size:14px;font-weight:700;color:var(--color-text)">' + esc(m.plate_number || "—") + "</span>" +
      statusBadge(m.status_display, m.status) + "</div>" +
      '<div style="font-size:12.5px;color:var(--color-neutral-400);margin-bottom:12px">' + esc(descBits) + "</div>" +
      driver +
      '<div style="display:flex;justify-content:space-between;margin-top:12px;padding-top:12px;border-top:1px solid var(--color-neutral-800)"><span style="font-size:11px;color:var(--color-neutral-500)">' + esc(m.ownership_type_display || "Formule") + '</span><span style="font-size:12.5px;font-weight:600;color:var(--color-text)">' + window.gmFmt(m.commission_rate || 0) + "% comm.</span></div></div>";
  }

  function loadMotos() {
    window.gmGetJSON("/api/v1/motorcycles/").then(function (d) {
      var list = rows(d);
      var badge = document.getElementById("gr-badge-motos");
      if (badge) badge.textContent = list.length;

      if (!list.length) {
        set("gr-top-motos", '<tr><td colspan="5" style="padding:18px;color:var(--color-neutral-500)">Aucune moto enregistrée.</td></tr>');
        set("gr-motos-grid", '<div style="grid-column:1 / -1;padding:18px;color:var(--color-neutral-500)">Aucune moto enregistrée dans votre flotte.</div>');
        set("gr-chauffeurs-tbody", '<tr><td colspan="5" style="padding:18px;color:var(--color-neutral-500)">Aucun chauffeur affecté.</td></tr>');
        return;
      }

      // Overview table
      set("gr-top-motos", list.slice(0, 8).map(function (m) {
        var name = m.assigned_motard_name;
        return '<tr><td style="font-weight:600;color:var(--color-text);font-family:ui-monospace,monospace;font-size:12.5px">' + esc(m.plate_number || "—") + "</td>" +
          '<td style="color:' + (name ? "var(--color-neutral-300)" : "var(--color-neutral-500)") + '">' + esc(name || "— non affectée") + "</td>" +
          '<td style="color:var(--color-neutral-400)">' + esc(m.ownership_type_display || "—") + "</td>" +
          '<td style="color:var(--color-neutral-400)">' + esc([m.brand, m.model_style].filter(Boolean).join(" ") || "—") + "</td>" +
          "<td>" + statusBadge(m.status_display, m.status) + "</td></tr>";
      }).join(""));

      // Cards
      set("gr-motos-grid", list.map(motoCard).join(""));

      // Chauffeurs (bikes with an assigned motard)
      var withDriver = list.filter(function (m) { return m.assigned_motard_name; });
      if (!withDriver.length) {
        set("gr-chauffeurs-tbody", '<tr><td colspan="5" style="padding:18px;color:var(--color-neutral-500)">Aucun chauffeur affecté pour le moment.</td></tr>');
      } else {
        set("gr-chauffeurs-tbody", withDriver.map(function (m) {
          var name = m.assigned_motard_name;
          return "<tr><td><div style=\"display:flex;align-items:center;gap:10px\"><span style=\"" + avatar + "\">" + esc(initials(name)) + "</span>" +
            '<span style="font-weight:600;color:var(--color-text)">' + esc(name) + "</span></div></td>" +
            '<td style="color:var(--color-neutral-400);font-family:ui-monospace,monospace;font-size:12.5px">' + esc(m.plate_number || "—") + "</td>" +
            '<td style="color:var(--color-neutral-400)">' + esc(m.ownership_type_display || "—") + "</td>" +
            "<td>" + statusBadge(m.status_display, m.status) + "</td>" +
            '<td style="color:var(--color-neutral-300)">' + window.gmFmt(m.commission_rate || 0) + "%</td></tr>";
        }).join(""));
      }
    }).catch(function () {
      set("gr-top-motos", '<tr><td colspan="5" style="padding:18px;color:#d98a8a">Erreur de chargement.</td></tr>');
      set("gr-motos-grid", '<div style="grid-column:1 / -1;padding:18px;color:#d98a8a">Erreur de chargement.</div>');
      set("gr-chauffeurs-tbody", '<tr><td colspan="5" style="padding:18px;color:#d98a8a">Erreur de chargement.</td></tr>');
    });
  }

  // ---- Reversements (fleet-remittances) ----
  function loadRemittances() {
    window.gmGetJSON("/api/v1/fleet-remittances/").then(function (d) {
      var list = rows(d);
      if (!list.length) {
        set("gr-revenus-tbody", '<tr><td colspan="6" style="padding:18px;color:var(--color-neutral-500)">Aucun reversement pour le moment.</td></tr>');
        return;
      }
      set("gr-revenus-tbody", list.map(function (r) {
        var period = r.period_end || r.period_start || (r.created_at ? r.created_at.slice(0, 10) : "—");
        return '<tr><td style="color:var(--color-neutral-300)">' + esc(period) + "</td>" +
          '<td style="color:var(--color-neutral-400);font-family:ui-monospace,monospace;font-size:12.5px">' + esc(r.plate_number || "—") + "</td>" +
          '<td style="color:var(--color-neutral-300)">' + esc(r.motard_name || "—") + "</td>" +
          '<td style="text-align:right;color:var(--color-neutral-300)">' + fc(r.gross_revenue) + "</td>" +
          '<td style="text-align:right;color:var(--color-neutral-400)">' + fc(r.commission_amount) + "</td>" +
          '<td style="text-align:right;color:var(--color-text);font-weight:600">' + fc(r.net_amount) + "</td></tr>";
      }).join(""));
    }).catch(function () {
      set("gr-revenus-tbody", '<tr><td colspan="6" style="padding:18px;color:#d98a8a">Erreur de chargement.</td></tr>');
    });
  }

  // ---- Contrats (agreements) ----
  var FREQ_FR = { daily: "Journalier", weekly: "Hebdomadaire", monthly: "Mensuel" };
  var AGR_FR = { rental: "Location", hire_purchase: "Contrat (achat)" };
  function loadAgreements() {
    window.gmGetJSON("/api/v1/agreements/").then(function (d) {
      var list = rows(d);
      if (!list.length) {
        set("gr-contrats-tbody", '<tr><td colspan="6" style="padding:18px;color:var(--color-neutral-500)">Aucun contrat en cours.</td></tr>');
        return;
      }
      set("gr-contrats-tbody", list.map(function (a) {
        var target = Number(a.target_total_amount || 0);
        var paid = Number(a.amount_already_paid || 0);
        var pct = target > 0 ? Math.min(100, Math.round((paid / target) * 100)) : null;
        var rest = target > 0 ? Math.max(0, target - paid) : null;
        return '<tr><td style="font-weight:600;color:var(--color-text);font-family:ui-monospace,monospace;font-size:12.5px">#' + esc(a.motorcycle) + "</td>" +
          '<td style="color:var(--color-neutral-300)">#' + esc(a.motard) + "</td>" +
          '<td style="color:var(--color-neutral-400)">' + esc(AGR_FR[a.agreement_type] || a.agreement_type) + "</td>" +
          '<td style="color:var(--color-neutral-400)">' + esc(FREQ_FR[a.frequency] || a.frequency) + "</td>" +
          '<td style="text-align:right;color:var(--color-accent-200);font-weight:600">' + (pct === null ? "—" : pct + "%") + "</td>" +
          '<td style="text-align:right;color:var(--color-text)">' + (rest === null ? "—" : fc(rest)) + "</td></tr>";
      }).join(""));
    }).catch(function () {
      set("gr-contrats-tbody", '<tr><td colspan="6" style="padding:18px;color:#d98a8a">Erreur de chargement.</td></tr>');
    });
  }

  function loadMe() {
    window.gmGetJSON("/api/v1/auth/me/").then(function (u) {
      var name = ((u.first_name || "") + " " + (u.last_name || "")).trim();
      if (name) setVal("gr-set-name", name);
      if (u.phone_number) setVal("gr-set-phone", u.phone_number);
    }).catch(function () {});
  }

  function wirePassword() {
    var span = document.getElementById("gr-pw-submit");
    if (!span) return;
    var btn = span.closest("button");
    (btn || span).addEventListener("click", function () {
      window.gmPostJSON("/api/account/password/", {
        old_password: (document.getElementById("gr-pw-old") || {}).value || "",
        new_password: (document.getElementById("gr-pw-new") || {}).value || "",
        new_password2: (document.getElementById("gr-pw-new2") || {}).value || "",
      }).then(function () {
        if (window.showAppToast) window.showAppToast("Mot de passe mis à jour.", "success");
        ["gr-pw-old", "gr-pw-new", "gr-pw-new2"].forEach(function (id) { var e = document.getElementById(id); if (e) e.value = ""; });
      }).catch(function (err) {
        if (window.showAppToast) window.showAppToast(err.message || "Échec de la mise à jour.", "error");
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    window.gmSetupNav(TITLES, "overview");
    loadDashboard();
    loadMotos();
    loadRemittances();
    loadAgreements();
    loadMe();
    wirePassword();
  });
})();
