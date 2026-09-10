(function () {
  "use strict";

  function selectedUserProfile(select) {
    return select && select.options[select.selectedIndex];
  }

  function updateUserProfile(select) {
    var form = select.closest("form");
    var emailField = form && form.querySelector("[data-manual-order-customer-email]");
    var option = selectedUserProfile(select);
    if (emailField) {
      emailField.value = option ? option.getAttribute("data-email") || "" : "";
    }

    if (!form || !option) {
      return;
    }
    [
      "firstname",
      "lastname",
      "phone",
      "legal_name",
      "tax_id",
      "billing_address",
      "billing_postal_code",
      "billing_city",
      "shipping_address",
      "shipping_postal_code",
      "shipping_city"
    ].forEach(function (fieldName) {
      var field = form.querySelector("[name='" + fieldName + "']");
      var profileValue = option.getAttribute("data-" + fieldName.replace(/_/g, "-")) || "";
      if (field && !field.value && profileValue) {
        field.value = profileValue;
      }
    });
  }

  function syncCustomerMode(editor) {
    var customerMode = editor.querySelector("[data-manual-order-customer-mode]");
    var registeredFields = editor.querySelector("[data-manual-order-registered-user-fields]");
    var userSelect = editor.querySelector("[data-manual-order-user-select]");
    var emailField = editor.querySelector("[data-manual-order-customer-email]");
    if (!customerMode) {
      return;
    }

    var isRegistered = customerMode.value === "registered_user";
    if (registeredFields) {
      registeredFields.hidden = !isRegistered;
    }
    if (userSelect) {
      userSelect.disabled = !isRegistered;
    }
    if (emailField) {
      emailField.readOnly = isRegistered;
      emailField.setAttribute("aria-readonly", isRegistered ? "true" : "false");
    }
    if (isRegistered && userSelect) {
      updateUserProfile(userSelect);
    }
  }

  function syncShippingFields(editor) {
    var checkbox = editor.querySelector("[data-manual-order-shipping-same]");
    var fields = editor.querySelector("[data-manual-order-shipping-fields]");
    if (!checkbox || !fields) {
      return;
    }
    fields.classList.toggle("mw-manual-order-draft__shipping-fields--inactive", checkbox.checked);
    Array.prototype.forEach.call(fields.querySelectorAll("input"), function (input) {
      input.disabled = checkbox.checked;
    });
  }

  function updatePaymentHelp(editor) {
    var select = editor.querySelector("select[name='payment_method']");
    var help = editor.querySelector("[data-manual-order-payment-help]");
    if (!select || !help) {
      return;
    }
    var messages = {
      bank_transfer: "Transferencia bancaria: requiere referencia bancaria real y fecha de confirmación.",
      cash: "Efectivo: requiere fecha de confirmación y una nota interna de evidencia.",
      external_other: "Otro pago externo: requiere fecha y una referencia o nota de evidencia.",
    };
    help.textContent = messages[select.value] || "Selecciona un método para ver la evidencia requerida al confirmar.";
  }

  function lineContainer(editor) {
    return editor.querySelector("[data-manual-order-lines]");
  }

  function addLine(editor) {
    var template = editor.querySelector("template[data-manual-order-line-template]");
    var container = lineContainer(editor);
    if (!template || !container) {
      return;
    }
    container.appendChild(template.content.cloneNode(true));
  }

  function moveLine(line, direction) {
    var sibling = direction === "up" ? line.previousElementSibling : line.nextElementSibling;
    if (!sibling || !sibling.hasAttribute("data-manual-order-line")) {
      return;
    }
    if (direction === "up") {
      line.parentNode.insertBefore(line, sibling);
    } else {
      line.parentNode.insertBefore(sibling, line);
    }
  }

  function initializeEditor(editor) {
    syncCustomerMode(editor);
    syncShippingFields(editor);
    updatePaymentHelp(editor);

    var userSelect = editor.querySelector("[data-manual-order-user-select]");
    if (userSelect) {
      userSelect.addEventListener("change", function () {
        updateUserProfile(userSelect);
      });
    }

    var customerMode = editor.querySelector("[data-manual-order-customer-mode]");
    if (customerMode) {
      customerMode.addEventListener("change", function () {
        syncCustomerMode(editor);
      });
    }

    var shippingCheckbox = editor.querySelector("[data-manual-order-shipping-same]");
    if (shippingCheckbox) {
      shippingCheckbox.addEventListener("change", function () {
        syncShippingFields(editor);
      });
    }

    var paymentSelect = editor.querySelector("select[name='payment_method']");
    if (paymentSelect) {
      paymentSelect.addEventListener("change", function () {
        updatePaymentHelp(editor);
      });
    }

    editor.addEventListener("click", function (event) {
      var control = event.target.closest("[data-manual-order-line-action]");
      if (!control) {
        return;
      }
      var action = control.getAttribute("data-manual-order-line-action");
      if (action === "add") {
        event.preventDefault();
        addLine(editor);
        return;
      }
      var line = control.closest("[data-manual-order-line]");
      if (!line) {
        return;
      }
      event.preventDefault();
      if (action === "remove") {
        line.remove();
      } else if (action === "up" || action === "down") {
        moveLine(line, action);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-manual-order-draft-editor]"),
      initializeEditor
    );
  });
}());
