(function () {
  "use strict";

  var masterFieldId = "send_sent_status_email";
  var secondaryFieldIds = [
    "include_receipt_guide_in_sent_email",
    "include_installation_guide_in_sent_email",
    "include_incident_form_in_sent_email"
  ];

  function fieldGroup(field) {
    return field.closest(".form-group") || field.parentElement;
  }

  function initialize() {
    var master = document.getElementById(masterFieldId);
    if (!master || master.dataset.orderSentEmailOptionsInitialized === "true") {
      return;
    }

    var masterGroup = fieldGroup(master);
    var secondaryGroups = secondaryFieldIds
      .map(function (fieldId) {
        var field = document.getElementById(fieldId);
        return field ? { field: field, group: fieldGroup(field) } : null;
      })
      .filter(function (entry) {
        return entry && entry.group;
      });

    if (!masterGroup || secondaryGroups.length !== secondaryFieldIds.length) {
      return;
    }

    var options = document.createElement("div");
    options.className = "mw-order-sent-email-options";
    options.id = "order-sent-email-options";
    options.innerHTML = "<p class=\"mw-order-sent-email-options__title\">Incluir en este email:</p>" +
      "<p class=\"mw-order-sent-email-options__help\">Estas opciones se incluyen dentro del email de pedido enviado.</p>";

    masterGroup.insertAdjacentElement("afterend", options);
    secondaryGroups.forEach(function (entry) {
      options.appendChild(entry.group);
    });

    function syncSecondaryFields() {
      var enabled = master.checked;
      options.classList.toggle("mw-order-sent-email-options--disabled", !enabled);
      options.setAttribute("aria-disabled", String(!enabled));
      secondaryGroups.forEach(function (entry) {
        entry.field.disabled = !enabled;
      });
    }

    master.setAttribute("aria-controls", options.id);
    master.addEventListener("change", syncSecondaryFields);
    master.dataset.orderSentEmailOptionsInitialized = "true";
    syncSecondaryFields();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize);
  } else {
    initialize();
  }
}());
