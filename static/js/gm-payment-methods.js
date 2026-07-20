/*
 * gm-payment-methods.js — gestionnaire de moyens de paiement (Mobile Money / banque)
 * réutilisable dans tous les profils (propriétaire, motard…).
 *
 * Usage : window.gmPaymentMethods.mount("id-du-conteneur");
 * Requiert : gmGetJSON, gmPostJSON, gmCsrf, fetchWithTimeout (chargés par le site).
 */
(function () {
  "use strict";

  var API = "/api/v1/payment-methods/";
  var PROVIDERS = [
    ["mpesa", "M-Pesa", "#f7c948", "#1b1d29"],
    ["airtel_money", "Airtel Money", "#e8532f", "#fff"],
    ["orange_money", "Orange Money", "#ff7900", "#fff"],
  ];

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function providerBadge(p) {
    var found = PROVIDERS.filter(function (x) { return x[0] === p; })[0];
    var bg = found ? found[2] : "rgba(145,132,217,.14)";
    var fg = found ? found[3] : "var(--color-accent-300)";
    var abbr = found ? found[1].slice(0, 3) : "MM";
    return '<span style="width:38px;height:38px;border-radius:10px;background:' + bg + ';display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:800;color:' + fg + ';flex-shrink:0">' + esc(abbr) + "</span>";
  }
  function bankBadge() {
    return '<span style="width:38px;height:38px;border-radius:10px;background:rgba(145,132,217,.14);display:flex;align-items:center;justify-content:center;flex-shrink:0"><i class="ph-fill ph-bank" style="color:var(--color-accent-300);font-size:18px"></i></span>';
  }

  function methodRow(m) {
    var badge = m.kind === "bank" ? bankBadge() : providerBadge(m.provider);
    var title = m.kind === "bank"
      ? esc(m.bank_name + " · " + (m.account_number || ""))
      : esc((m.provider_display || "Mobile Money") + " · " + (m.phone_number || ""));
    var sub = m.kind === "bank" ? esc(m.account_holder || "Compte bancaire") : "Mobile Money";
    var def = m.is_default
      ? '<span style="font-size:10.5px;font-weight:600;color:var(--color-accent-200);background:rgba(145,132,217,.14);padding:3px 9px;border-radius:20px">Défaut</span>'
      : '<button class="gm-pm-def" data-pm-id="' + m.id + '" style="font-size:10.5px;font-weight:600;color:var(--color-neutral-400);background:transparent;border:1px solid var(--color-neutral-800);padding:3px 9px;border-radius:20px;cursor:pointer">Définir par défaut</button>';
    return '<div style="display:flex;align-items:center;gap:12px;background:var(--color-surface);border:1px solid ' + (m.is_default ? "var(--color-accent-700)" : "var(--color-neutral-800)") + ';border-radius:13px;padding:13px 15px">' +
      badge +
      '<div style="flex:1;min-width:0"><div style="font-size:13px;font-weight:600;color:var(--color-text)">' + title + '</div><div style="font-size:11px;color:var(--color-neutral-500)">' + sub + "</div></div>" +
      def +
      '<button class="gm-pm-del" data-pm-id="' + m.id + '" title="Supprimer" style="background:transparent;border:none;color:var(--color-neutral-500);cursor:pointer;padding:5px"><i class="ph ph-trash" style="font-size:16px"></i></button>' +
      "</div>";
  }

  function formHtml() {
    var opts = PROVIDERS.map(function (p) { return '<option value="' + p[0] + '">' + p[1] + "</option>"; }).join("");
    return '<div class="gm-pm-form" style="display:none;margin-top:12px;background:var(--color-surface);border:1px solid var(--color-neutral-800);border-radius:13px;padding:15px">' +
      '<div style="display:flex;gap:4px;padding:4px;background:var(--color-bg);border:1px solid var(--color-neutral-800);border-radius:10px;margin-bottom:14px">' +
      '<span class="gm-pm-kind" data-kind="mobile_money" style="flex:1;text-align:center;padding:8px;border-radius:7px;font-size:12.5px;font-weight:600;color:var(--color-accent-200);background:var(--color-surface);cursor:pointer">Mobile Money</span>' +
      '<span class="gm-pm-kind" data-kind="bank" style="flex:1;text-align:center;padding:8px;border-radius:7px;font-size:12.5px;font-weight:500;color:var(--color-neutral-400);cursor:pointer">Banque</span>' +
      "</div>" +
      '<div class="gm-pm-mobile">' +
      '<div class="field" style="margin-bottom:11px"><label>Opérateur</label><select class="input gm-pm-provider">' + opts + "</select></div>" +
      '<div class="field" style="margin-bottom:4px"><label>Numéro Mobile Money</label><input class="input gm-pm-phone" type="text" placeholder="+243 8XX XXX XXX"></div>' +
      "</div>" +
      '<div class="gm-pm-bank" style="display:none">' +
      '<div class="field" style="margin-bottom:11px"><label>Banque</label><input class="input gm-pm-bankname" type="text" placeholder="Ex. Rawbank"></div>' +
      '<div class="field" style="margin-bottom:11px"><label>Numéro de compte</label><input class="input gm-pm-account" type="text" placeholder="00012345678"></div>' +
      '<div class="field" style="margin-bottom:4px"><label>Titulaire du compte</label><input class="input gm-pm-holder" type="text" placeholder="Nom complet"></div>' +
      "</div>" +
      '<div style="display:flex;gap:10px;justify-content:flex-end;margin-top:14px"><button class="btn btn-secondary gm-pm-cancel" style="font-size:13px;padding:8px 14px">Annuler</button><button class="btn btn-primary gm-pm-save" style="font-size:13px;padding:8px 16px"><i class="ph ph-check"></i>Enregistrer</button></div>' +
      "</div>";
  }

  function mount(containerId) {
    var root = document.getElementById(containerId);
    if (!root) return;
    root.innerHTML =
      '<div class="gm-pm-list" style="display:flex;flex-direction:column;gap:10px"><div style="padding:12px;color:var(--color-neutral-500);font-size:12px">Chargement…</div></div>' +
      '<button class="btn btn-secondary btn-block gm-pm-add" style="font-size:13.5px;padding:11px;margin-top:12px"><i class="ph ph-plus"></i>Ajouter un moyen de paiement</button>' +
      formHtml();

    var listEl = root.querySelector(".gm-pm-list");
    var formEl = root.querySelector(".gm-pm-form");
    var kind = "mobile_money";

    function refresh() {
      window.gmGetJSON(API).then(function (d) {
        var items = (d && (d.results || d)) || [];
        if (!items.length) {
          listEl.innerHTML = '<div style="padding:14px;color:var(--color-neutral-500);font-size:12.5px;text-align:center">Aucun moyen de paiement. Reliez votre Mobile Money ou votre compte bancaire pour recevoir vos paiements.</div>';
        } else {
          listEl.innerHTML = items.map(methodRow).join("");
        }
      }).catch(function () {
        listEl.innerHTML = '<div style="padding:14px;color:#d98a8a;font-size:12.5px">Erreur de chargement.</div>';
      });
    }

    function setKind(k) {
      kind = k;
      root.querySelectorAll(".gm-pm-kind").forEach(function (s) {
        var on = s.getAttribute("data-kind") === k;
        s.style.background = on ? "var(--color-surface)" : "transparent";
        s.style.color = on ? "var(--color-accent-200)" : "var(--color-neutral-400)";
        s.style.fontWeight = on ? "600" : "500";
      });
      root.querySelector(".gm-pm-mobile").style.display = k === "mobile_money" ? "" : "none";
      root.querySelector(".gm-pm-bank").style.display = k === "bank" ? "" : "none";
    }

    function showForm(show) {
      formEl.style.display = show ? "" : "none";
      root.querySelector(".gm-pm-add").style.display = show ? "none" : "";
    }

    root.addEventListener("click", function (e) {
      var t = e.target;
      if (t.closest(".gm-pm-add")) { showForm(true); return; }
      if (t.closest(".gm-pm-cancel")) { showForm(false); return; }
      var kindBtn = t.closest(".gm-pm-kind");
      if (kindBtn) { setKind(kindBtn.getAttribute("data-kind")); return; }

      var defBtn = t.closest(".gm-pm-def");
      if (defBtn) {
        window.gmPostJSON(API + defBtn.getAttribute("data-pm-id") + "/set_default/", {})
          .then(refresh).catch(function () {});
        return;
      }
      var delBtn = t.closest(".gm-pm-del");
      if (delBtn) {
        window.fetchWithTimeout(API + delBtn.getAttribute("data-pm-id") + "/", {
          method: "DELETE", headers: { "X-CSRFToken": window.gmCsrf() },
        }).then(function () { refresh(); }).catch(function () {});
        return;
      }
      if (t.closest(".gm-pm-save")) {
        var body = { kind: kind };
        if (kind === "mobile_money") {
          body.provider = root.querySelector(".gm-pm-provider").value;
          body.phone_number = root.querySelector(".gm-pm-phone").value.trim();
        } else {
          body.bank_name = root.querySelector(".gm-pm-bankname").value.trim();
          body.account_number = root.querySelector(".gm-pm-account").value.trim();
          body.account_holder = root.querySelector(".gm-pm-holder").value.trim();
        }
        var saveBtn = t.closest(".gm-pm-save");
        window.withButtonLoading(saveBtn, function () { return window.gmPostJSON(API, body); })
          .then(function () {
            if (window.showAppToast) window.showAppToast("Moyen de paiement ajouté.", "success");
            root.querySelectorAll(".gm-pm-phone,.gm-pm-bankname,.gm-pm-account,.gm-pm-holder").forEach(function (i) { i.value = ""; });
            showForm(false);
            refresh();
          }).catch(function (err) {
            if (window.showAppToast) window.showAppToast(err.message || "Vérifiez les champs.", "error");
          });
        return;
      }
    });

    refresh();
  }

  window.gmPaymentMethods = { mount: mount };
})();
