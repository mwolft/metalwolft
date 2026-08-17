(function () {
  "use strict";

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-manual-invoice-inline-add]");
    if (!button) {
      return;
    }

    event.preventDefault();
    var fieldId = button.getAttribute("data-manual-invoice-inline-add");
    if (!fieldId || !window.faForm) {
      return;
    }

    window.faForm.addInlineField(button, fieldId);
  });
}());
