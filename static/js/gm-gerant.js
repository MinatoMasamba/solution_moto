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

  function setText(id, v) { var el = document.getElementById(id); if (el) el.textContent = v; }
  function setBar(id, pct) {
    var el = document.getElementById(id);
    if (el) el.style.width = Math.max(0, Math.min(100, pct)) + "%";
  }
  function usd(fcAmount) { return "≈ $" + window.gmFmt(Math.round((fcAmount || 0) / 2850)); }
  function star(n) { return "★ " + Number(n || 0).toFixed(1).replace(".", ","); }

  function loadOverview() {
    window.gmGetJSON("/api/dashboard/fleet-manager/").then(function (d) {
      var k = d.kpis || {};
      set("gr-kpi-motards", window.gmFmt(k.motards_supervised || 0));
      set("gr-kpi-revenue", window.gmFmt(k.today_revenue || 0) + ' <span style="font-size:15px;color:var(--color-neutral-600);font-weight:500">FC</span>');
      setText("gr-badge-motards", window.gmFmt(k.motards_supervised || 0));
      setText("gr-kpi-online", window.gmFmt(k.online_motards || 0));
      setText("gr-kpi-courses", window.gmFmt(k.today_rides || 0));
      setText("gr-kpi-usd", usd(k.today_revenue));
      var dispo = k.motards_supervised ? Math.round(100 * (k.online_motards || 0) / k.motards_supervised) : 0;
      setText("gr-kpi-rendement", dispo + "%");
      setText("gr-kpi-rating", Number(k.avg_rating || 0).toFixed(1).replace(".", ","));

      // Reversements (tuiles)
      var rm = d.remittances || {};
      setText("gr-rev-tosend", window.gmFmt(Math.round(rm.to_send || 0)) + " FC");
      setText("gr-rev-sent", window.gmFmt(Math.round(rm.sent_week || 0)) + " FC");
      setText("gr-rev-pending", window.gmFmt(rm.pending_owners || 0));

      // Rendement (tuiles liées aux KPIs)
      setText("gr-perf-pct", dispo + "%");
      setBar("gr-perf-bar", dispo);
      setText("gr-perf-score", star(k.avg_rating));
      setText("gr-obj-active", window.gmFmt(k.online_motards || 0) + " / " + window.gmFmt(k.motards_supervised || 0));
      setBar("gr-obj-active-bar", dispo);
      setText("gr-obj-rating", star(k.avg_rating) + (Number(k.avg_rating || 0) >= 4.5 ? " ✓" : ""));
      setBar("gr-obj-rating-bar", (Number(k.avg_rating || 0) / 5) * 100);
      setText("gr-obj-trials", window.gmFmt(k.ongoing_trials || 0));
      setBar("gr-obj-trials-bar", Math.min(100, (k.ongoing_trials || 0) * 20));

      // Motards à suivre
      var watch = d.watch || [];
      var box = document.getElementById("gr-watch");
      if (box) {
        if (!watch.length) {
          box.innerHTML = '<div style="font-size:12px;color:var(--color-neutral-500)">Rien à signaler — tous vos motards sont en règle.</div>';
        } else {
          box.innerHTML = watch.map(function (w) {
            var danger = w.action === "relancer" || w.action === "à appeler";
            return '<div style="display:flex;align-items:center;gap:10px"><span style="' + avatar + '">' + esc(initials(w.name)) + "</span>" +
              '<div style="flex:1;min-width:0"><div style="font-size:12.5px;font-weight:600;color:var(--color-text)">' + esc(w.name) + "</div>" +
              '<div style="font-size:10.5px;color:var(--color-neutral-600)">' + esc(w.reason) + "</div></div>" +
              '<span style="font-size:10.5px;color:' + (danger ? "#d98a8a" : "#d9a866") + '">' + esc(w.action) + "</span></div>";
          }).join("");
        }
      }

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
      var ongoing = list.filter(function (r) { return r.status === "ongoing" || r.status === "accepted"; }).length;
      setText("gr-courses-sub", window.gmFmt(list.length) + " courses · " + window.gmFmt(ongoing) + " en cours");
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

  function loadPerformance() {
    window.gmGetJSON("/api/dashboard/fleet-manager/performance/").then(function (p) {
      var days = p.days || [];
      var max = 1;
      days.forEach(function (d) { if (d.revenue > max) max = d.revenue; });

      // Grand graphique (panneau « Mon rendement »)
      var chart = document.getElementById("gr-perf-chart");
      if (chart) {
        chart.innerHTML = days.map(function (d) {
          var h = Math.max(3, Math.round((d.revenue / max) * 100));
          return '<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:8px">' +
            '<div style="width:100%;height:120px;display:flex;align-items:flex-end" title="' + window.gmFmt(Math.round(d.revenue)) + ' FC · ' + d.count + ' courses">' +
            '<div style="width:100%;height:' + h + '%;background:linear-gradient(180deg,var(--color-accent-400),var(--color-accent-800));border-radius:5px 5px 0 0"></div></div>' +
            '<span style="font-size:11px;color:var(--color-neutral-600)">' + esc(d.date) + "</span></div>";
        }).join("");
      }

      // Mini graphique de la vue d'ensemble (« Courses de ma zone »)
      var maxC = 1;
      days.forEach(function (d) { if (d.count > maxC) maxC = d.count; });
      var zone = document.getElementById("gr-chart-zone");
      if (zone) {
        zone.innerHTML = days.map(function (d) {
          var h = Math.max(4, Math.round((d.count / maxC) * 100));
          return '<div style="flex:1;height:' + h + '%;background:linear-gradient(180deg,var(--color-accent-400),var(--color-accent-700));border-radius:3px 3px 0 0" title="' + d.count + ' courses"></div>';
        }).join("");
      }
      var labels = document.getElementById("gr-chart-zone-labels");
      if (labels) {
        labels.innerHTML = days.map(function (d) {
          return "<span>" + esc(String(d.date).split(" ")[0]) + "</span>";
        }).join("");
      }

      setText("gr-perf-revenue", window.gmFmt(Math.round(p.total_revenue || 0)) + " FC");
      setText("gr-perf-usd", usd(p.total_revenue));
      setText("gr-obj-rides", window.gmFmt(p.total_rides || 0));
      setBar("gr-obj-rides-bar", Math.min(100, (p.total_rides || 0)));
    }).catch(function () {
      var chart = document.getElementById("gr-perf-chart");
      if (chart) chart.innerHTML = '<div style="font-size:12px;color:#d98a8a">Erreur de chargement.</div>';
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
    loadPerformance();
    loadMe();
    wirePassword();
  });
})();
