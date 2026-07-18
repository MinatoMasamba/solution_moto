/* Console Gérant de flotte — chargement des données réelles (sa zone). */
(function () {
  "use strict";

  var TITLES = {
    overview: ["Vue d'ensemble", "Ma zone"],
    map: ["Carte de ma zone", "Positions de mes motards"],
    motards: ["Mes motards", "Motards supervisés"],
    inscription: ["Inscrire un motard", "Soumis au DG pour approbation"],
    courses: ["Courses du jour", "Ma zone · temps réel"],
    rapport: ["Rapport chauffeur", "Transmis au DG"],
    reglages: ["Réglages", "Mon compte gérant"],
    motdepasse: ["Sécurité", "Changer mon mot de passe"],
    reversements: ["Reversements", "Argent à envoyer aux propriétaires"],
    rendement: ["Mon rendement", "7 derniers jours"],
    support: ["Support", "Demandes de mes motards"],
  };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function initials(name) {
    var p = String(name || "").trim().split(/\s+/);
    return ((p[0] || "")[0] || "") + ((p[1] || "")[0] || "");
  }
  function fc(n) { return window.gmFmt(Math.round(n || 0)) + " FC"; }
  function rows(data) { return (data && (data.results || data)) || []; }
  function set(id, html) { var el = document.getElementById(id); if (el) el.innerHTML = html; }
  function setVal(id, v) { var el = document.getElementById(id); if (el) el.value = v; }
  var avatar = 'width:28px;height:28px;border-radius:50%;background:var(--color-neutral-800);display:flex;align-items:center;justify-content:center;font-size:10.5px;font-weight:600;color:var(--color-neutral-200)';
  function statusBadge(av) {
    return av
      ? '<span style="font-size:11px;font-weight:600;color:#8fceac;background:rgba(111,174,144,.15);padding:3px 9px;border-radius:20px">Disponible</span>'
      : '<span style="font-size:11px;font-weight:600;color:var(--color-neutral-400);background:var(--color-neutral-800);padding:3px 9px;border-radius:20px">Hors ligne</span>';
  }
  var STATUS_FR = { requested: "Demandée", accepted: "Acceptée", ongoing: "En cours", completed: "Terminée", cancelled: "Annulée" };

  function loadOverview() {
    window.gmGetJSON("/api/dashboard/fleet-manager/").then(function (d) {
      var k = d.kpis || {};
      set("gr-kpi-motards", window.gmFmt(k.motards_supervised || 0));
      set("gr-kpi-revenue", window.gmFmt(k.today_revenue || 0) + ' <span style="font-size:15px;color:var(--color-neutral-600);font-weight:500">FC</span>');

      var fleet = (d.fleet || []).filter(function (b) { return b.motard_name; });
      if (!fleet.length) {
        set("gr-overview-motards", '<tr><td colspan="5" style="padding:18px;color:var(--color-neutral-500)">Aucun motard assigné.</td></tr>');
        return;
      }
      set("gr-overview-motards", fleet.map(function (b) {
        return "<tr><td><div style=\"display:flex;align-items:center;gap:10px\"><span style=\"" + avatar + "\">" + esc(initials(b.motard_name)) + "</span>" +
          '<span style="font-weight:600;color:var(--color-text)">' + esc(b.motard_name) + "</span></div></td>" +
          "<td>" + statusBadge(b.status === "assigned" || b.status === "available") + "</td>" +
          '<td style="text-align:right;color:var(--color-neutral-500)">—</td>' +
          '<td style="text-align:right;color:var(--color-text);font-weight:600">' + fc(b.revenue_today) + "</td>" +
          '<td style="color:var(--color-neutral-500)">—</td></tr>';
      }).join(""));
    }).catch(function () {
      set("gr-overview-motards", '<tr><td colspan="5" style="padding:18px;color:#d98a8a">Erreur de chargement.</td></tr>');
    });
  }

  function loadMotards() {
    window.gmGetJSON("/api/v1/motard-profiles/").then(function (d) {
      var list = rows(d);
      if (!list.length) {
        set("gr-motards-tbody", '<tr><td colspan="7" style="padding:18px;color:var(--color-neutral-500)">Aucun motard dans votre flotte.</td></tr>');
        return;
      }
      set("gr-motards-tbody", list.map(function (p) {
        var u = p.user || {};
        var name = ((u.first_name || "") + " " + (u.last_name || "")).trim() || u.phone_number || "—";
        return "<tr><td><div style=\"display:flex;align-items:center;gap:10px\"><span style=\"" + avatar + "\">" + esc(initials(name)) + "</span>" +
          '<span style="font-weight:600;color:var(--color-text)">' + esc(name) + "</span></div></td>" +
          '<td style="color:var(--color-neutral-400)">' + esc(u.phone_number || "—") + "</td>" +
          "<td>" + statusBadge(p.is_available) + "</td>" +
          '<td style="text-align:right;color:var(--color-neutral-500)">—</td>' +
          '<td style="text-align:right;color:var(--color-neutral-500)">—</td>' +
          '<td style="color:#d9a866">★ ' + Number(p.rating_average || 0).toFixed(1).replace(".", ",") + "</td>" +
          '<td style="color:var(--color-neutral-400)">' + esc(p.subscription_status || "—") + "</td></tr>";
      }).join(""));
    }).catch(function () {
      set("gr-motards-tbody", '<tr><td colspan="7" style="padding:18px;color:#d98a8a">Erreur de chargement.</td></tr>');
    });
  }

  function loadCourses() {
    window.gmGetJSON("/api/v1/rides/").then(function (d) {
      var list = rows(d);
      if (!list.length) {
        set("gr-courses-tbody", '<tr><td colspan="6" style="padding:18px;color:var(--color-neutral-500)">Aucune course.</td></tr>');
        return;
      }
      set("gr-courses-tbody", list.slice(0, 40).map(function (r) {
        var t = r.requested_at ? new Date(r.requested_at).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" }) : "—";
        return '<tr><td style="color:var(--color-neutral-400)">' + t + "</td>" +
          '<td style="color:var(--color-neutral-300)">' + esc(r.client_name || "—") + "</td>" +
          '<td style="color:var(--color-neutral-300)">' + esc(r.motard_name || "—") + "</td>" +
          '<td style="color:var(--color-neutral-400)">' + esc(r.pickup_address || "?") + " → " + esc(r.dropoff_address || "?") + "</td>" +
          '<td style="text-align:right;color:var(--color-text);font-weight:600">' + (r.agreed_price ? fc(r.agreed_price) : "—") + "</td>" +
          '<td><span style="font-size:11px;font-weight:600;color:var(--color-neutral-300);background:var(--color-neutral-800);padding:3px 9px;border-radius:20px">' + esc(STATUS_FR[r.status] || r.status) + "</span></td></tr>";
      }).join(""));
    }).catch(function () {
      set("gr-courses-tbody", '<tr><td colspan="6" style="padding:18px;color:#d98a8a">Erreur de chargement.</td></tr>');
    });
  }

  function loadReversements() {
    window.gmGetJSON("/api/v1/fleet-remittances/").then(function (d) {
      var list = rows(d);
      if (!list.length) {
        set("gr-reversements-tbody", '<tr><td colspan="7" style="padding:18px;color:var(--color-neutral-500)">Aucun reversement.</td></tr>');
        return;
      }
      set("gr-reversements-tbody", list.map(function (r) {
        return '<tr><td style="font-weight:600;color:var(--color-text);font-family:ui-monospace,monospace;font-size:12.5px">' + esc(r.plate_number || "—") + "</td>" +
          '<td style="color:var(--color-neutral-300)">' + esc(r.motard_name || "—") + "</td>" +
          '<td style="color:var(--color-neutral-400)">' + esc(r.owner_name || "—") + "</td>" +
          '<td style="text-align:right;color:var(--color-text);font-weight:600">' + fc(r.gross_revenue) + "</td>" +
          '<td style="text-align:right;color:var(--color-neutral-300)">' + fc(r.net_amount) + "</td>" +
          '<td><span style="font-size:11px;font-weight:600;color:#d9a866;background:rgba(217,168,102,.14);padding:3px 9px;border-radius:20px">À envoyer</span></td><td></td></tr>';
      }).join(""));
    }).catch(function () {
      set("gr-reversements-tbody", '<tr><td colspan="7" style="padding:18px;color:#d98a8a">Erreur de chargement.</td></tr>');
    });
  }

  function loadMe() {
    window.gmGetJSON("/api/v1/auth/me/").then(function (u) {
      setVal("gr-set-name", ((u.first_name || "") + " " + (u.last_name || "")).trim());
      setVal("gr-set-phone", u.phone_number || "");
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
    loadOverview();
    loadMotards();
    loadCourses();
    loadReversements();
    loadMe();
    wirePassword();
  });
})();
