/* Console opérateur (deux layouts) — tous les indicateurs branchés sur l'API. */
(function () {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function initials(name) {
    var p = String(name || "").trim().split(/\s+/);
    return (((p[0] || "")[0] || "") + ((p[1] || "")[0] || "")).toUpperCase() || "—";
  }
  function fc(n) { return window.gmFmt(Math.round(n || 0)) + " FC"; }
  function usd(fcAmount) { return "≈ $" + window.gmFmt(Math.round((fcAmount || 0) / 2850)); }
  function set(id, html) { var el = document.getElementById(id); if (el) el.innerHTML = html; }
  function setText(id, v) { var el = document.getElementById(id); if (el) el.textContent = v; }
  function setAll(cls, v) {
    document.querySelectorAll("." + cls).forEach(function (el) { el.textContent = v; });
  }
  var avatar = 'width:28px;height:28px;border-radius:50%;background:var(--color-neutral-800);display:flex;align-items:center;justify-content:center;font-size:10.5px;font-weight:600;color:var(--color-neutral-200)';

  // Barres + étiquettes d'activité horaire (06h → 20h) dans un conteneur donné.
  function renderActivity(barsId, labelsId, activity) {
    var bars = document.getElementById(barsId);
    if (!bars) return;
    var hours = [];
    for (var h = 6; h <= 20; h++) hours.push(h);
    var max = 1;
    hours.forEach(function (h) {
      var a = activity[h] || activity[String(h)] || { count: 0 };
      if (a.count > max) max = a.count;
    });
    bars.innerHTML = hours.map(function (h) {
      var a = activity[h] || activity[String(h)] || { count: 0, revenue: 0 };
      var pct = Math.max(3, Math.round((a.count / max) * 100));
      return '<div style="flex:1;height:' + pct + '%;background:linear-gradient(180deg,var(--color-accent-400),var(--color-accent-700));border-radius:3px 3px 0 0" title="' +
        (h < 10 ? "0" : "") + h + "h · " + a.count + " courses · " + window.gmFmt(Math.round(a.revenue || 0)) + ' FC"></div>';
    }).join("");
    var labels = document.getElementById(labelsId);
    if (labels) {
      labels.innerHTML = [6, 9, 12, 15, 18, 20].map(function (h) {
        return "<span>" + (h < 10 ? "0" : "") + h + "h</span>";
      }).join("");
    }
  }

  function loadOperator() {
    window.gmGetJSON("/api/dashboard/operator/").then(function (d) {
      var k = d.kpis || {};
      var pct = k.total_motards ? Math.round(100 * (k.active_motards || 0) / k.total_motards) : 0;
      var motardsHtml = (k.active_motards || 0) +
        '<span style="font-size:15px;color:var(--color-neutral-600);font-weight:500"> / ' + (k.total_motards || 0) + "</span>";

      // Layout A — bandeau KPI
      set("cn-kpi-rides", window.gmFmt(k.total_rides || 0));
      set("cn-kpi-motards", motardsHtml);
      set("cn-kpi-revenue", window.gmFmt(k.revenue_fc || 0) + ' <span style="font-size:15px;color:var(--color-neutral-600);font-weight:500">FC</span>');
      setText("cn-kpi-online-pct", pct + "% en ligne");
      setText("cn-kpi-usd", usd(k.revenue_fc));
      set("cn-kpi-rating", Number(k.avg_rating || 0).toFixed(1).replace(".", ",") +
        '<span style="font-size:15px;color:var(--color-neutral-600);font-weight:500"> / 5</span>');
      setText("cn-kpi-reviews", window.gmFmt(k.total_ratings || 0) + " avis");

      // Layout B — panneau vitré
      setText("cn2-rides", window.gmFmt(k.total_rides || 0));
      set("cn2-motards", motardsHtml);
      setText("cn2-online-pct", pct + "%");
      set("cn2-revenue", window.gmFmt(k.revenue_fc || 0) + ' <span style="font-size:12px;color:var(--color-neutral-600);font-weight:500">FC</span>');
      setText("cn2-usd", usd(k.revenue_fc));
      setText("cn2-rating", Number(k.avg_rating || 0).toFixed(1).replace(".", ",") + " / 5");
      setText("cn2-reviews", window.gmFmt(k.total_ratings || 0));

      // Graphiques d'activité (les deux layouts)
      renderActivity("cn-activity", "cn-activity-labels", d.activity || {});
      renderActivity("cn2-activity", "cn2-activity-labels", d.activity || {});

      // Top motards du jour
      var top = d.top_motards || [];
      var box = document.getElementById("cn-top-motards");
      if (box) {
        box.innerHTML = top.length ? top.map(function (m, i) {
          return '<div style="display:flex;align-items:center;gap:11px">' +
            '<span style="font-size:12px;font-weight:700;color:' + (i < 3 ? "var(--color-accent-300)" : "var(--color-neutral-500)") + ';width:16px">' + (i + 1) + "</span>" +
            '<span style="width:30px;height:30px;border-radius:50%;background:var(--color-neutral-800);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;color:var(--color-neutral-200)">' + esc(initials(m.name)) + "</span>" +
            '<div style="flex:1;min-width:0"><div style="font-size:12.5px;font-weight:600;color:var(--color-text)">' + esc(m.name) + "</div>" +
            '<div style="font-size:10.5px;color:var(--color-neutral-600)">' + esc(m.pillar || "—") + " · " + (m.rides || 0) + " courses</div></div>" +
            '<div style="text-align:right"><div style="font-size:12px;font-weight:600;color:var(--color-text)">' + fc(m.revenue) + "</div>" +
            '<div style="font-size:10.5px;color:#d9a866">★ ' + Number(m.rating || 0).toFixed(1).replace(".", ",") + "</div></div></div>";
        }).join("") : '<div style="font-size:12px;color:var(--color-neutral-500)">Aucune course terminée aujourd\'hui.</div>';
      }

      // Table réseau (layout A)
      if (!top.length) {
        set("cn-network-motards", '<tr><td colspan="8" style="padding:18px;color:var(--color-neutral-500)">Aucune course terminée aujourd\'hui.</td></tr>');
      } else {
        set("cn-network-motards", top.map(function (m) {
          return "<tr><td><div style=\"display:flex;align-items:center;gap:10px\"><span style=\"" + avatar + "\">" + esc(initials(m.name)) + "</span>" +
            '<span style="font-weight:600;color:var(--color-text)">' + esc(m.name) + "</span></div></td>" +
            '<td style="color:var(--color-neutral-400)">' + esc(m.commune || "—") + "</td>" +
            '<td><span style="font-size:11px;font-weight:600;color:#8fceac;background:rgba(111,174,144,.15);padding:3px 9px;border-radius:20px">Disponible</span></td>' +
            '<td style="text-align:right;color:var(--color-neutral-300)">' + (m.rides || 0) + "</td>" +
            '<td style="text-align:right;color:var(--color-text);font-weight:600">' + fc(m.revenue) + "</td>" +
            '<td style="color:#d9a866">★ ' + Number(m.rating || 0).toFixed(1).replace(".", ",") + "</td>" +
            '<td style="color:var(--color-neutral-400)">' + esc(m.pillar || "—") + "</td><td></td></tr>";
        }).join(""));
      }
      var sub = document.getElementById("cn-network-sub");
      if (sub) sub.textContent = window.gmFmt(k.total_motards || 0) + " inscrits";
    }).catch(function () {
      set("cn-network-motards", '<tr><td colspan="8" style="padding:18px;color:#d98a8a">Erreur de chargement.</td></tr>');
    });
  }

  function loadNotifications() {
    window.gmGetJSON("/api/dashboard/notifications/").then(function (d) {
      var items = d.items || [];
      var pending = items.filter(function (i) { return i.type === "motard_pending"; }).length;
      setAll("cn-badge-notif", window.gmFmt(d.unread || 0));
      setAll("cn-badge-pending", window.gmFmt(pending));
      setAll("cn-pending-chip", window.gmFmt(pending));
      setText("cn-map-pending", window.gmFmt(pending));
      var sub = document.getElementById("cn-network-sub");
      if (sub && pending) sub.textContent += " · " + pending + " à valider";
    }).catch(function () {});
  }

  function loadCommissions() {
    window.gmGetJSON("/api/dashboard/operator/commissions/").then(function (d) {
      var list = (d && (d.commissions || d)) || [];
      if (!Array.isArray(list)) list = [];
      var box = document.getElementById("cn-commissions");
      if (box) {
        box.innerHTML = list.length ? list.map(function (f) {
          return '<div style="border:1px solid var(--color-neutral-800);border-radius:11px;padding:12px 13px">' +
            '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">' +
            '<span style="font-size:13px;font-weight:600;color:var(--color-text)">' + esc(f.owner_name || "—") + "</span>" +
            '<span style="font-size:11px;color:var(--color-neutral-500)">' + (f.bike_count || 0) + " motos</span></div>" +
            '<div style="display:flex;align-items:baseline;justify-content:space-between">' +
            '<span style="font-size:11px;color:var(--color-neutral-500)">Revenu ' + fc(f.gross_revenue) + " · comm. " + Number(f.commission_rate || 0).toFixed(0) + "%</span>" +
            '<span style="font-size:13px;font-weight:700;color:var(--color-accent-200)">à reverser ' + fc(f.net_to_remit) + "</span></div></div>";
        }).join("") : '<div style="font-size:12px;color:var(--color-neutral-500)">Aucune flotte en gérance.</div>';
      }
      var total = 0;
      list.forEach(function (f) { total += (f.gross_revenue || 0) - (f.net_to_remit || 0); });
      set("cn-commission-total", fc(total) + ' <span style="font-size:12px;color:var(--color-neutral-600);font-weight:500">· ' + usd(total).replace("≈ ", "") + "</span>");
    }).catch(function () {
      var box = document.getElementById("cn-commissions");
      if (box) box.innerHTML = '<div style="font-size:12px;color:#d98a8a">Erreur de chargement.</div>';
    });
  }

  function loadStats() {
    window.gmGetJSON("/api/dashboard/owner/").then(function (d) {
      var k = d.kpis || d || {};
      setText("cn-stat-fleets", window.gmFmt(k.total_fleets || 0));
      setText("cn-stat-bikes", window.gmFmt(k.total_bikes || 0));
      setText("cn-stat-subs", window.gmFmt(k.paid_subscriptions || 0));
      setText("cn-stat-alerts", window.gmFmt(k.open_alerts || 0));
    }).catch(function () {});
    window.gmGetJSON("/api/dashboard/operator/clients/").then(function (d) {
      setText("cn-stat-clients", window.gmFmt(d.total || 0));
    }).catch(function () {});
  }

  function loadMe() {
    window.gmGetJSON("/api/v1/auth/me/").then(function (u) {
      var name = ((u.first_name || "") + " " + (u.last_name || "")).trim() || u.phone_number || "—";
      setAll("cn-user-name", name);
      setAll("cn-user-avatar", initials(name));
    }).catch(function () {});
  }

  document.addEventListener("DOMContentLoaded", function () {
    loadOperator();
    loadNotifications();
    loadCommissions();
    loadStats();
    loadMe();
  });
})();
