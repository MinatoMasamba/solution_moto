/* Console dispatch (opérateur) — KPIs et table motards en direct. */
(function () {
  "use strict";
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
  function set(id, html) { var el = document.getElementById(id); if (el) el.innerHTML = html; }
  var avatar = 'width:28px;height:28px;border-radius:50%;background:var(--color-neutral-800);display:flex;align-items:center;justify-content:center;font-size:10.5px;font-weight:600;color:var(--color-neutral-200)';

  document.addEventListener("DOMContentLoaded", function () {
    window.gmGetJSON("/api/dashboard/operator/").then(function (d) {
      var k = d.kpis || {};
      set("cn-kpi-rides", window.gmFmt(k.total_rides || 0));
      set("cn-kpi-motards", (k.active_motards || 0) + '<span style="font-size:15px;color:var(--color-neutral-600);font-weight:500"> / ' + (k.total_motards || 0) + "</span>");
      set("cn-kpi-revenue", window.gmFmt(k.revenue_fc || 0) + ' <span style="font-size:15px;color:var(--color-neutral-600);font-weight:500">FC</span>');

      var top = d.top_motards || [];
      if (!top.length) {
        set("cn-network-motards", '<tr><td colspan="8" style="padding:18px;color:var(--color-neutral-500)">Aucune course terminée aujourd\'hui.</td></tr>');
        return;
      }
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
    }).catch(function () {
      set("cn-network-motards", '<tr><td colspan="8" style="padding:18px;color:#d98a8a">Erreur de chargement.</td></tr>');
    });
  });
})();
