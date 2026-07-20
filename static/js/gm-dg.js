/* Console Direction Générale — chargement des données réelles. */
(function () {
  "use strict";

  var _dateStr = (function () {
    var s = new Date().toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
    return s.charAt(0).toUpperCase() + s.slice(1);
  })();

  var TITLES = {
    overview: ["Vue d'ensemble", _dateStr + " · Kinshasa"],
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

      // Sous-indicateurs calculés (aucune valeur inventée)
      var total = k.total_motards || 0;
      var pct = total > 0 ? Math.round(((k.active_motards || 0) / total) * 100) : null;
      set("dg-kpi-online-pct", pct === null ? "—" : pct + "% en ligne");
      set("dg-kpi-revenue-usd", "≈ $" + window.gmFmt(Math.round(k.revenue_usd || 0)));
      set("dg-network-count", total + " inscrit" + (total > 1 ? "s" : ""));

      renderActivity(d.activity || {});

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
      } else {
        set("dg-top-motards", '<div style="padding:8px 0;font-size:12px;color:var(--color-neutral-500)">Aucune course terminée aujourd\'hui.</div>');
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
      set("dg-top-motards", '<div style="padding:8px 0;font-size:12px;color:#d98a8a">Erreur de chargement.</div>');
      set("dg-network-motards", '<tr><td colspan="7" style="padding:18px;color:#d98a8a">Erreur de chargement.</td></tr>');
    });
  }

  // ── Motards (liste complète) ───────────────────────────────────────────
  var SUB_FR = { active: "Abonnement actif", trial: "En essai", expired: "Abonnement expiré", suspended: "Suspendu" };

  function renderAdhesions(list) {
    var el = document.getElementById("dg-adhesions");
    if (!el) return;
    var pending = list.filter(function (p) { return p.application_status === "pending"; });
    if (!pending.length) {
      el.innerHTML = '<div style="padding:8px 4px;font-size:12px;color:var(--color-neutral-500)">Aucune adhésion en attente d\'approbation.</div>';
      return;
    }
    el.innerHTML = pending.map(function (p) {
      var u = p.user || {};
      var name = ((u.first_name || "") + " " + (u.last_name || "")).trim() || u.phone_number || "—";
      return '<div style="flex:1;min-width:230px;border:1px solid var(--color-neutral-800);border-radius:11px;padding:13px 14px;background:var(--color-surface)">' +
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:11px"><span style="width:30px;height:30px;border-radius:50%;background:rgba(217,168,102,.18);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;color:#d9a866">' + esc(initials(name)) + '</span><div><div style="font-size:12.5px;font-weight:600;color:var(--color-text)">' + esc(name) + '</div><div style="font-size:10.5px;color:var(--color-neutral-600)">' + esc(p.commune || u.phone_number || "—") + '</div></div></div>' +
        '<div style="display:flex;gap:7px"><button class="btn btn-primary" data-approve="' + p.id + '" style="flex:1;font-size:12px;padding:5px">Approuver</button><button class="btn btn-secondary" data-reject="' + p.id + '" style="font-size:12px;padding:5px 12px">Refuser</button></div>' +
        '</div>';
    }).join("");
  }

  function loadMotards() {
    window.gmGetJSON("/api/v1/motard-profiles/").then(function (d) {
      var list = rows(d);

      // Compteurs réels des chips
      var total = list.length;
      var avail = list.filter(function (p) { return p.is_available; }).length;
      var pending = list.filter(function (p) { return p.application_status === "pending"; }).length;
      set("dg-mt-total", String(total));
      set("dg-mt-avail", String(avail));
      set("dg-mt-offline", String(total - avail));
      set("dg-mt-pending", String(pending));
      set("dg-badge-pending", String(pending));

      renderAdhesions(list);

      if (!list.length) {
        set("dg-motards-tbody", '<tr><td colspan="8" style="padding:18px;color:var(--color-neutral-500)">Aucun motard enregistré.</td></tr>');
        return;
      }
      set("dg-motards-tbody", list.map(function (p) {
        var u = p.user || {};
        var name = ((u.first_name || "") + " " + (u.last_name || "")).trim() || u.phone_number || "—";
        var subColor = p.subscription_status === "active" ? "#8fceac" : (p.subscription_status === "expired" ? "#d98a8a" : "var(--color-neutral-500)");
        return "<tr><td><div style=\"display:flex;align-items:center;gap:10px\"><span style=\"" + avatar + "\">" + esc(initials(name)) + "</span>" +
          '<span style="font-weight:600;color:var(--color-text)">' + esc(name) + "</span></div></td>" +
          '<td style="color:var(--color-neutral-400)">' + esc(p.commune || "—") + "</td>" +
          "<td>" + statusBadge(p.is_available) + "</td>" +
          '<td style="text-align:right;color:var(--color-neutral-500)">—</td>' +
          '<td style="text-align:right;color:var(--color-neutral-500)">—</td>' +
          '<td style="color:#d9a866">★ ' + Number(p.rating_average || 0).toFixed(1).replace(".", ",") + "</td>" +
          '<td style="color:var(--color-neutral-400)">' + esc(u.phone_number || "—") + "</td>" +
          '<td style="color:' + subColor + '">' + esc(SUB_FR[p.subscription_status] || p.subscription_status || "—") + "</td></tr>";
      }).join(""));
    }).catch(function () {
      set("dg-motards-tbody", '<tr><td colspan="8" style="padding:18px;color:#d98a8a">Erreur de chargement.</td></tr>');
      var el = document.getElementById("dg-adhesions");
      if (el) el.innerHTML = '<div style="padding:8px 4px;font-size:12px;color:#d98a8a">Erreur de chargement.</div>';
    });
  }

  // Boutons Approuver / Refuser des adhésions (délégation, branché une fois).
  function wireMotardActions() {
    document.addEventListener("click", function (e) {
      var a = e.target.closest && e.target.closest("[data-approve]");
      var r = e.target.closest && e.target.closest("[data-reject]");
      if (!a && !r) return;
      var btn = a || r;
      var id = btn.getAttribute(a ? "data-approve" : "data-reject");
      var url = "/api/v1/motard-profiles/" + id + "/" + (a ? "approve" : "reject") + "/";
      window.withButtonLoading(btn, function () { return window.gmPostJSON(url, {}); })
        .then(function () {
          if (window.showAppToast) window.showAppToast(a ? "Adhésion approuvée." : "Adhésion refusée.", "success");
          loadMotards();
        }).catch(function () {});
    });
  }

  // ── Clients ────────────────────────────────────────────────────────────
  function loadClients() {
    window.gmGetJSON("/api/dashboard/operator/clients/").then(function (d) {
      set("dg-clients-total", window.gmFmt(d.total || 0));
      set("dg-clients-new", window.gmFmt(d.new_today || 0));
      set("dg-clients-avg", String(d.avg_rides || 0).replace(".", ","));
      set("dg-clients-rating", d.rating ? String(d.rating).replace(".", ",") : "—");
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
    // Intitulé de la semaine courante (lundi → dimanche), calculé — pas de date figée.
    var now = new Date();
    var monday = new Date(now);
    monday.setDate(now.getDate() - ((now.getDay() + 6) % 7));
    var sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);
    var fmt = function (dt) { return dt.toLocaleDateString("fr-FR", { day: "2-digit", month: "short" }); };
    set("dg-gerants-week", "semaine du " + fmt(monday) + " au " + fmt(sunday));

    window.gmGetJSON("/api/dashboard/operator/gerants/").then(function (d) {
      set("dg-gerants-total", window.gmFmt(d.total || 0));
      var list = d.gerants || [];

      var sumMotards = 0, sumBikes = 0, sumRev = 0;
      list.forEach(function (g) {
        sumMotards += g.motards || 0;
        sumBikes += g.bikes || 0;
        sumRev += Number(g.revenue_today || 0);
      });
      set("dg-gerants-motards", window.gmFmt(sumMotards));
      set("dg-gerants-bikes", window.gmFmt(sumBikes));
      set("dg-gerants-revenue", fc(sumRev));
      set("dg-gerants-revenue-usd", "≈ $" + window.gmFmt(Math.round(sumRev / 2850)));

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

      var totComm = 0, totNet = 0;
      list.forEach(function (c) {
        totComm += (Number(c.gross_revenue || 0) - Number(c.net_to_remit || 0));
        totNet += Number(c.net_to_remit || 0);
      });
      set("dg-comm-total", fc(totComm));
      set("dg-comm-net", fc(totNet));
      set("dg-comm-owners", window.gmFmt(list.length));

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
      var pending = items.filter(function (i) { return i.type === "motard_pending"; }).length;
      set("dg-badge-notif", window.gmFmt(d.unread || 0));
      set("dg-badge-pending", window.gmFmt(pending));
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

  // ── Activité de la journée (barres = déplacements, courbe = revenus) ────
  function renderActivity(activity) {
    var barsEl = document.getElementById("dg-activity-bars");
    var lineEl = document.getElementById("dg-activity-line");
    var emptyEl = document.getElementById("dg-activity-empty");
    if (!barsEl) return;

    // Plage horaire affichée : 06h → 20h (15 barres, cohérent avec les libellés).
    var hours = [];
    for (var h = 6; h <= 20; h++) hours.push(h);

    var counts = hours.map(function (h) { return (activity[h] && activity[h].count) || 0; });
    var revenues = hours.map(function (h) { return (activity[h] && activity[h].revenue) || 0; });

    var totalCount = counts.reduce(function (a, b) { return a + b; }, 0);
    var totalRev = revenues.reduce(function (a, b) { return a + b; }, 0);

    if (emptyEl) {
      var empty = totalCount === 0 && totalRev === 0;
      emptyEl.style.display = empty ? "flex" : "none";
      if (empty) emptyEl.textContent = "Aucune activité aujourd'hui.";
    }

    var maxCount = Math.max.apply(null, counts.concat([1]));
    var idxMax = counts.indexOf(Math.max.apply(null, counts));

    barsEl.innerHTML = counts.map(function (c, i) {
      var pct = Math.round((c / maxCount) * 100);
      var grad = i === idxMax && c > 0
        ? "linear-gradient(180deg,var(--color-accent-300),var(--color-accent-600))"
        : "linear-gradient(180deg,var(--color-accent-400),var(--color-accent-700))";
      // hauteur minimale visible quand il y a au moins 1 course
      var h = c > 0 ? Math.max(4, pct) : 0;
      var title = (6 + i) + "h · " + c + " course(s)";
      return '<div title="' + title + '" style="flex:1;height:' + h + '%;background:' + grad + ';border-radius:3px 3px 0 0"></div>';
    }).join("");

    if (lineEl) {
      var maxRev = Math.max.apply(null, revenues.concat([1]));
      var n = revenues.length;
      var pts = revenues.map(function (r, i) {
        var x = 10 + (287 * i) / (n - 1);
        var y = 110 - (r / maxRev) * 100;
        return x.toFixed(0) + "," + y.toFixed(0);
      });
      lineEl.setAttribute("points", totalRev > 0 ? pts.join(" ") : "");
    }
  }

  // ── Carte temps réel (positions GPS réelles) ───────────────────────────
  // Boîte englobante approximative de Kinshasa pour projeter lat/lng en %.
  var KIN = { latN: -4.28, latS: -4.52, lngW: 15.15, lngE: 15.58 };

  function project(lat, lng) {
    var x = (lng - KIN.lngW) / (KIN.lngE - KIN.lngW) * 100;
    var y = (KIN.latN - lat) / (KIN.latN - KIN.latS) * 100;
    return { x: Math.max(2, Math.min(98, x)), y: Math.max(2, Math.min(98, y)) };
  }

  function marker(p, big) {
    var pos = project(p.latitude, p.longitude);
    var size = big ? 16 : 15;
    if (p.on_ride) {
      return '<div title="' + esc(p.name) + '" style="position:absolute;left:' + pos.x + "%;top:" + pos.y + '%;transform:translate(-50%,-50%)"><span style="position:absolute;inset:-6px;border-radius:50%;background:rgba(150,138,224,.5);animation:gmPing 2.4s infinite"></span><span style="position:relative;display:block;width:' + size + "px;height:" + size + 'px;border-radius:50%;background:var(--color-accent-500);border:2px solid #fff"></span></div>';
    }
    return '<div title="' + esc(p.name) + '" style="position:absolute;left:' + pos.x + "%;top:" + pos.y + '%;transform:translate(-50%,-50%)"><span style="display:block;width:' + (size - 2) + "px;height:" + (size - 2) + 'px;border-radius:50%;background:#6fae90;border:2px solid #fff"></span></div>';
  }

  function loadMap() {
    window.gmGetJSON("/api/v1/location-pings/fleet/").then(function (d) {
      var positions = (d && d.positions) || [];
      var onRide = positions.filter(function (p) { return p.on_ride; }).length;
      var avail = positions.length - onRide;

      // Compteurs
      set("dg-map-count", positions.length + " en ligne");
      set("dg-map2-title", String(positions.length));
      set("dg-map2-onride", String(onRide));
      set("dg-map2-avail", String(avail));

      // États vides / marqueurs
      ["dg-map-empty", "dg-map2-empty"].forEach(function (id) {
        var el = document.getElementById(id);
        if (el) {
          el.style.display = positions.length ? "none" : "flex";
          if (!positions.length) el.textContent = "Aucune position en temps réel — en attente des trackers GPS.";
        }
      });

      set("dg-map-markers", positions.map(function (p) { return marker(p, false); }).join(""));
      set("dg-map2-markers", positions.map(function (p) { return marker(p, true); }).join(""));
    }).catch(function () {
      ["dg-map-empty", "dg-map2-empty"].forEach(function (id) {
        var el = document.getElementById(id);
        if (el) { el.style.display = "flex"; el.textContent = "Positions indisponibles."; }
      });
    });
  }

  // ── Réglages / mot de passe ────────────────────────────────────────────
  function loadMe() {
    window.gmGetJSON("/api/v1/auth/me/").then(function (u) {
      var name = ((u.first_name || "") + " " + (u.last_name || "")).trim() || u.phone_number || "—";
      setVal("dg-set-name", name);
      setVal("dg-set-phone", u.phone_number || "");
      document.querySelectorAll(".dg-user-name").forEach(function (el) { el.textContent = name; });
      document.querySelectorAll(".dg-user-avatar").forEach(function (el) {
        el.textContent = (initials(name) || "—").toUpperCase();
      });
    }).catch(function () {});
  }

  function loadSupport() {
    var PRIO = {
      high: ["Haute", "#d98a8a", "rgba(207,127,127,.14)"],
      medium: ["Moyenne", "#d9a866", "rgba(217,168,102,.14)"],
      low: ["Basse", "var(--color-neutral-300)", "var(--color-neutral-800)"],
    };
    var STAT = {
      open: ["Ouvert", "#d9a866", "rgba(217,168,102,.14)"],
      in_progress: ["En cours", "var(--color-accent-200)", "rgba(145,132,217,.14)"],
      resolved: ["Résolu", "#8fceac", "rgba(111,174,144,.14)"],
    };
    window.gmGetJSON("/api/dashboard/support/").then(function (d) {
      var items = d.items || [];
      var sub = document.getElementById("dg-support-sub");
      if (sub) sub.textContent = items.length ? (d.open || 0) + " ticket(s) ouvert(s)" : "aucun ticket";
      if (!items.length) {
        set("dg-support-tbody", '<tr><td colspan="6" style="padding:18px;color:var(--color-neutral-500)">Aucun ticket support pour le moment. Les tickets créés par les motards, clients et propriétaires apparaîtront ici.</td></tr>');
        return;
      }
      set("dg-support-tbody", items.map(function (t) {
        var p = PRIO[t.priority] || PRIO.medium;
        var s = STAT[t.status] || STAT.open;
        return '<tr><td style="font-weight:600;color:var(--color-text)">' + esc(t.requester) + "</td>" +
          '<td style="color:var(--color-neutral-400)">' + esc(t.role) + "</td>" +
          '<td style="color:var(--color-neutral-300)">' + esc(t.subject) + "</td>" +
          '<td><span style="font-size:11px;font-weight:600;color:' + p[1] + ";background:" + p[2] + ';padding:3px 9px;border-radius:20px">' + p[0] + "</span></td>" +
          '<td><span style="font-size:11px;font-weight:600;color:' + s[1] + ";background:" + s[2] + ';padding:3px 9px;border-radius:20px">' + s[0] + "</span></td>" +
          '<td style="color:var(--color-neutral-400)">' + esc(t.date) + "</td></tr>";
      }).join(""));
    }).catch(function () {
      set("dg-support-tbody", '<tr><td colspan="6" style="padding:18px;color:#d98a8a">Erreur de chargement.</td></tr>');
    });
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
    loadSupport();
    loadMap();
    loadMe();
    wirePassword();
    wireMotardActions();
    // Rafraîchit les positions toutes les 20 s (temps réel léger).
    setInterval(loadMap, 20000);
  });
})();
