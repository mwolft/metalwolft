(function () {
  "use strict";

  var statusFieldId = "order_status";
  var optionGroups = [
    {
      status: "enviado",
      masterFieldId: "send_sent_status_email",
      secondaryFieldIds: [
        "include_receipt_guide_in_sent_email",
        "include_installation_guide_in_sent_email",
        "include_incident_form_in_sent_email"
      ]
    },
    {
      status: "entregado",
      masterFieldId: "send_delivered_status_email",
      secondaryFieldIds: [
        "include_installation_guide_in_delivered_email",
        "include_maintenance_guide_in_delivered_email"
      ]
    }
  ];

  function fieldGroup(field) {
    return field.closest(".form-group") || field.parentElement;
  }

  function createOptionGroup(config) {
    var master = document.getElementById(config.masterFieldId);
    if (!master) {
      return null;
    }

    var masterGroup = fieldGroup(master);
    var secondaryGroups = config.secondaryFieldIds
      .map(function (fieldId) {
        var field = document.getElementById(fieldId);
        return field ? { field: field, group: fieldGroup(field) } : null;
      })
      .filter(function (entry) {
        return entry && entry.group;
      });

    if (!masterGroup || secondaryGroups.length !== config.secondaryFieldIds.length) {
      return null;
    }

    var container = document.createElement("div");
    container.className = "mw-order-status-email-options";
    container.dataset.orderStatus = config.status;
    masterGroup.parentNode.insertBefore(container, masterGroup);
    container.appendChild(masterGroup);

    var options = document.createElement("div");
    options.className = "mw-order-status-email-options__nested";
    options.id = "order-status-email-options-" + config.status;
    options.innerHTML = "<p class=\"mw-order-status-email-options__title\">Incluir en este email:</p>" +
      "<p class=\"mw-order-status-email-options__help\">Estas opciones se incluyen dentro del email de pedido " +
      config.status + ".</p>";
    container.appendChild(options);
    secondaryGroups.forEach(function (entry) {
      options.appendChild(entry.group);
    });

    function syncSecondaryFields() {
      var enabled = master.checked;
      options.classList.toggle("mw-order-status-email-options__nested--disabled", !enabled);
      options.setAttribute("aria-disabled", String(!enabled));
      secondaryGroups.forEach(function (entry) {
        entry.field.disabled = !enabled;
      });
    }

    master.setAttribute("aria-controls", options.id);
    master.addEventListener("change", syncSecondaryFields);
    syncSecondaryFields();
    return container;
  }

  function initialize() {
    var statusField = document.getElementById(statusFieldId);
    if (!statusField || statusField.dataset.orderStatusEmailOptionsInitialized === "true") {
      return;
    }

    var containers = optionGroups
      .map(createOptionGroup)
      .filter(function (container) {
        return container;
      });

    if (!containers.length) {
      return;
    }

    function syncVisibleGroup() {
      containers.forEach(function (container) {
        container.hidden = container.dataset.orderStatus !== statusField.value;
      });
    }

    statusField.addEventListener("change", syncVisibleGroup);
    statusField.dataset.orderStatusEmailOptionsInitialized = "true";
    syncVisibleGroup();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize);
  } else {
    initialize();
  }
}());
