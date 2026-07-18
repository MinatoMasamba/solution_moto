/* Console Direction Générale — chargement des données réelles. */
(function () {
  "use strict";

  var TITLES = {
    overview: ["Vue d'ensemble", "Réseau moto · Kinshasa"],
    map: ["Carte temps réel", "Positions des motards · Kinshasa"],
    motards: ["Motards", "Réseau des motards"],
    clients: ["Clients", "Clients de la plateforme"],
    fleets: ["Gérants", "Supervision du réseau motards"],
    commissions: ["Commissions & reversements", "Période courante · Kinshasa"],
    notifications: ["Notifications", "Alertes du réseau"],
    support: ["Support", "Demandes d'assistance"],
    reglages: ["Réglages", "Mon compte · Directeur Général"],
    motdepasse: ["Sécurité", "Changer mon mot de passe"],
  };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function initials(name) {
    var parts = String(name || "").trim().split(/\s+/);
    return ((parts[0] || "")[0] || "") + ((parts[1] || "")[0] || "");
  }
  function fc(n) { return window.gmFmt(Math.round(n || 0)) + " FC"; }
  function rows(data) { return (data && (data.results || data)) || []; }
  function set(id, html) { var el = document.getElementById(id); if (el) el.innerHTML = html; }
  function setVal(id, v) { var el = document.getElementById(id); if (el) el.value = v; }

  var avatar =
    'width:28px;height:28px;border-radius:50%;background:var(--color-neutral-800);display:flex;align-items:center;justify-content:center;font-size:10.5px;font-weight:600;color:var(--color-neutral-200)';

  function statusBadge(available) {
    if (available)
      return '<span style="font-size:11px;font-weight:600;color:#8fceac;background:rgba(111,174,144,.15);padding:3px 9px;border-radius:20px">Disponible</span>';
    return '<span style="font-size:11px;font-weight:600;color:var(--color-neutral-400);background:var(--color-neutral-800);padding:3px 9px;border-radius:20px">Hors ligne</span>';
  }

  // ── Overview ───────────────────────────────────────────────────────────
  function loadOverview() {
    window.gmGetJSON("/api/dashboard/operator/").then(function (d) {
      var k = d.kpis || {};
      set("dg-kpi-rides", window.gmFmt(k.total_rides || 0));
      set("dg-kpi-motards",
        (k.active_motards || 0) +
        '<span style="font-size:15px;color:var(--color-neutral-600);font-weight:500"> / ' + (k.total_motards || 0) + "</span>");
      set("dg-kpi-revenue",
        window.gmFmt(k.revenue_fc || 0) +
        ' <span style="font-size:15px;color:var(--color-neutral-600);font-weight:500">FC</span>');
      set("dg-kpi-rating",
        (Number(k.avg_rating || 0).toFixed(1)).replace(".", ",") +
        '<span style="font-size:15px;color:var(--color-neutral-600);font-weight:500"> / 5</span>');

      var top = d.top_motards || [];
      if (top.length) {
        set("dg-top-motards", top.map(function (m, i) {
          return '<div style="display:flex;align-items:center;gap:11px">' +
            '<span style="font-size:12px;font-weight:700;color:var(--color-accent-300);width:16px">' + (i + 1) + "</span>" +
            '<span style="width:30px;height:30px;border-radius:50%;background:var(--color-neutral-800);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;color:var(--color-neutral-200)">' + esc(initials(m.name)) + "</span>" +
            '<div style="flex:1;min-width:0"><div style="font-size:12.5px;font-weight:600;color:var(--color-text)">' + esc(m.name) + "</div>" +
            '<div style="font-size:10.5px;color:var(--color-neutral-600)">' + esc(m.commune || "—") + " · " + (m.rides || 0) + " courses</div></div>" +
            '<div style="text-align:right"><div style="font-size:12px;font-weight:600;color:var(--color-text)">' + fc(m.revenue) + "</div>" +
            '<div style="font-size:10.5px;color:#d9a866">★ ' + Number(m.rating || 0).toFixed(1).replace(".", ",") + "</div></div></div>";
        }).join(""));
      }

      if (top.length) {
        set("dg-network-motards", top.map(function (m) {
          return "<tr><td><div style=\"display:flex;align-items:center;gap:10px\"><span style=\"" + avatar + "\">" + esc(initials(m.name)) + "</span>" +
            '<span style="font-weight:600;color:var(--color-text)">' + esc(m.name) + "</span></div></td>" +
            '<td style="color:var(--color-neutral-400)">' + esc(m.commune || "—") + "</td>" +
            "<td>" + statusBadge(true) + "</td>" +
            '<td style="text-align:right;color:var(--color-neutral-300)">' + (m.rides || 0) + "</td>" +
            '<td style="text-align:right;color:var(--color-text);font-weight:600">' + fc(m.revenue) + "</td>" +
            '<td style="color:#d9a866">★ ' + Number(m.rating || 0).toFixed(1).replace(".", ",") + "</td>" +
            '<td style="color:var(--color-neutral-400)">' + esc(m.pillar || "—") + "</td></tr>";
        }).join(""));
      } else {
        set("dg-network-motards", '<tr><td colspan="7" style="padding:18px;color:var(--color-neutral-500)">Aucune course terminée aujourd\'hui.</td></tr>');
      }
    }).catch(function () {
      set("dg-network-motards", '<tr><td colspan="7" style="padding:18px;color:#d98a8a">Erreur de chargement.</td></tr>');
    });
  }

  // ── Motards (liste complète) ───────────────────────────────────────────
  function loadMotards() {
    window.gmGetJSON("/api/v1/motard-profiles/").then(function (d) {
      var list = rows(d);
      if (!list.length) {
        set("dg-motards-tbody", '<tr><td colspan="8" style="padding:18px;color:var(--color-neutral-500)">Aucun motard enregistré.</td></tr>');
        return;
      }
      set("dg-motards-tbody", list.map(function (p) {
        var u = p.user || {};
        var name = ((u.first_name || "") + " " + (u.last_name || "")).trim() || u.phone_number || "—";
        return "<tr><td><div style=\"display:flex;align-items:center;gap:10px\"><span style=\"" + avatar + "\">" + esc(initials(name)) + "</span>" +
          '<span style="font-weight:600;color:var(--color-text)">' + esc(name) + "</span></div></td>" +
          '<td style="color:var(--color-neutral-400)">' + esc(u.phone_number || "—") + "</td>" +
          "<td>" + statusBadge(p.is_available) + "</td>" +
          '<td style="text-align:right;color:var(--color-neutral-500)">—</td>' +
          '<td style="text-align:right;color:var(--color-neutral-500)">—</td>' +
          '<td style="color:#d9a866">★ ' + Number(p.rating_average || 0).toFixed(1).replace(".", ",") + "</td>" +
          '<td style="color:var(--color-neutral-400)">' + esc(p.subscription_status || "—") + "</td>" +
          '<td style="color:var(--color-neutral-500)">—</td></tr>';
      }).join(""));
    }).catch(function () {
      set("dg-motards-tbody", '<tr><td colspan="8" style="padding:18px;color:#d98a8a">Erreur de chargement.</td></tr>');
    });
  }

  // ── Clients ────────────────────────────────────────────────────────────
  function loadClients() {
    window.gmGetJSON("/api/dashboard/operator/clients/").then(function (d) {
      set("dg-clients-total", window.gmFmt(d.total || 0));
      var list = d.clients || [];
      if (!list.length) {
        set("dg-clients-tbody", '<tr><td colspan="6" style="padding:18px;color:var(--color-neutral-500)">Aucun client.</td></tr>');
        return;
      }
      set("dg-clients-tbody", list.map(function (c) {
        return "<tr><td><div style=\"display:flex;align-items:center;gap:10px\"><span style=\"" + avatar + "\">" + esc(initials(c.name)) + "</span>" +
          '<span style="font-weight:600;color:var(--color-text)">' + esc(c.name) + "</span></div></td>" +
          '<td style="color:var(--color-neutral-400)">' + esc(c.phone_number || "—") + "</td>" +
          '<td style="text-align:right;color:var(--color-neutral-300)">' + (c.rides || 0) + "</td>" +
          '<td style="text-align:right;color:var(--color-text);font-weight:600">' + fc(c.total_spent) + "</td>" +
          '<td style="color:var(--color-neutral-400)">' + esc(c.date_joined || "—") + "</td>" +
          '<td><span style="font-size:11px;font-weight:600;color:var(--color-neutral-300);background:var(--color-neutral-800);padding:3px 9px;border-radius:20px">Client</span></td></tr>';
      }).join(""));
    }).catch(function () {
      set("dg-clients-tbody", '<tr><td colspan="6" style="padding:18px;color:#d98a8a">Erreur de chargement.</td></tr>');
    });
  }

  // ── Gérants ────────────────────────────────────────────────────────────
  function loadGerants() {
    window.gmGetJSON("/api/dashboard/operator/gerants/").then(function (d) {
      set("dg-gerants-total", window.gmFmt(d.total || 0));
      var list = d.gerants || [];
      if (!list.length) {
        set("dg-gerants-tbody", '<tr><td colspan="6" style="padding:18px;color:var(--color-neutral-500)">Aucun gérant.</td></tr>');
        return;
      }
      set("dg-gerants-tbody", list.map(function (g) {
        return "<tr><td><div style=\"display:flex;align-items:center;gap:10px\"><span style=\"width:30px;height:30px;border-radius:9px;background:linear-gradient(140deg,var(--color-accent-500),var(--color-accent-800));display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;color:#fff\">" + esc(initials(g.name)) + "</span>" +
          '<div><div style="font-weight:600;color:var(--color-text)">' + esc(g.name) + '</div><div style="font-size:11px;color:var(--color-neutral-600)">' + esc(g.phone_number || "") + "</div></div></div></td>" +
          '<td style="color:var(--color-neutral-400)">—</td>' +
          '<td style="text-align:right;color:var(--color-neutral-300)">' + (g.motards || 0) + "</td>" +
          '<td style="color:var(--color-neutral-300)">' + (g.bikes || 0) + " motos</td>" +
          '<td style="color:var(--color-neutral-500)">—</td>' +
          '<td style="text-align:right;color:var(--color-text);font-weight:600">' + fc(g.revenue_today) + "</td></tr>";
      }).join(""));
    }).catch(function () {
      set("dg-gerants-tbody", '<tr><td colspan="6" style="padding:18px;color:#d98a8a">Erreur de chargement.</td></tr>');
    });
  }

  // ── Commissions ────────────────────────────────────────────────────────
  function loadCommissions() {
    window.gmGetJSON("/api/dashboard/operator/commissions/").then(function (d) {
      var list = d.commissions || [];
      if (!list.length) {
        set("dg-commissions-tbody", '<tr><td colspan="7" style="padding:18px;color:var(--color-neutral-500)">Aucune commission cette période.</td></tr>');
        return;
      }
      set("dg-commissions-tbody", list.map(function (c) {
        var commission = (c.gross_revenue || 0) - (c.net_to_remit || 0);
        return '<tr><td style="color:var(--color-neutral-400)">' + (c.bike_count || 0) + " motos</td>" +
          '<td style="color:var(--color-neutral-500)">—</td>' +
          '<td style="color:var(--color-neutral-300)">' + esc(c.owner_name) + "</td>" +
          '<td style="text-align:right;color:var(--color-text);font-weight:600">' + fc(c.gross_revenue) + "</td>" +
          '<td style="text-align:right;color:var(--color-accent-200)">' + fc(commission) + " (" + Number(c.commission_rate || 0).toFixed(0) + "%)</td>" +
          '<td style="text-align:right;color:var(--color-neutral-300)">' + fc(c.net_to_remit) + "</td>" +
          '<td><span style="font-size:11px;font-weight:600;color:#d9a866;background:rgba(217,168,102,.14);padding:3px 9px;border-radius:20px">À traiter</span></td></tr>';
      }).join(""));
    }).catch(function () {
      set("dg-commissions-tbody", '<tr><td colspan="7" style="padding:18px;color:#d98a8a">Erreur de chargement.</td></tr>');
    });
  }

  // ── Notifications ──────────────────────────────────────────────────────
  function loadNotifications() {
    window.gmGetJSON("/api/dashboard/notifications/").then(function (d) {
      var items = d.items || [];
      if (!items.length) {
        set("dg-notifications", '<div style="padding:22px 8px;font-size:13px;color:var(--color-neutral-500)">Aucune notification.</div>');
        return;
      }
      var tone = { danger: ["rgba(207,127,127,.14)", "#d98a8a"], warning: ["rgba(217,168,102,.14)", "#d9a866"], info: ["rgba(145,132,217,.14)", "var(--color-accent-300)"] };
      set("dg-notifications", items.map(function (n, i) {
        var t = tone[n.level] || tone.info;
        var border = i < items.length - 1 ? "border-bottom:1px solid var(--color-neutral-900)" : "";
        return '<div style="display:flex;align-items:center;gap:12px;padding:14px 0;' + border + '">' +
          '<span style="width:36px;height:36px;border-radius:10px;background:' + t[0] + ';display:flex;align-items:center;justify-content:center;flex-shrink:0"><i class="ph-fill ' + esc(n.icon || "ph-bell") + '" style="color:' + t[1] + ';font-size:17px"></i></span>' +
          '<div style="flex:1"><div style="font-size:13px;font-weight:600;color:var(--color-text)">' + esc(n.title) + "</div>" +
          '<div style="font-size:11.5px;color:var(--color-neutral-500)">' + esc(n.detail) + "</div></div></div>";
      }).join(""));
    }).catch(function () {
      set("dg-notifications", '<div style="padding:22px 8px;font-size:13px;color:#d98a8a">Erreur de chargement.</div>');
    });
  }

  // ── Réglages / mot de passe ────────────────────────────────────────────
  function loadMe() {
    window.gmGetJSON("/api/v1/auth/me/").then(function (u) {
      var name = ((u.first_name || "") + " " + (u.last_name || "")).trim();
      setVal("dg-set-name", name);
      setVal("dg-set-phone", u.phone_number || "");
    }).catch(function () {});
  }

  function wirePassword() {
    var span = document.getElementById("dg-pw-submit");
    if (!span) return;
    var btn = span.closest("button");
    (btn || span).addEventListener("click", function () {
      var payload = {
        old_password: (document.getElementById("dg-pw-old") || {}).value || "",
        new_password: (document.getElementById("dg-pw-new") || {}).value || "",
        new_password2: (document.getElementById("dg-pw-new2") || {}).value || "",
      };
      window.gmPostJSON("/api/account/password/", payload).then(function () {
        if (window.showAppToast) window.showAppToast("Mot de passe mis à jour.", "success");
        ["dg-pw-old", "dg-pw-new", "dg-pw-new2"].forEach(function (id) { var e = document.getElementById(id); if (e) e.value = ""; });
      }).catch(function (err) {
        if (window.showAppToast) window.showAppToast(err.message || "Échec de la mise à jour.", "error");
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    window.gmSetupNav(TITLES, "overview");
    loadOverview();
    loadMotards();
    loadClients();
    loadGerants();
    loadCommissions();
    loadNotifications();
    loadMe();
    wirePassword();
  });
})();
