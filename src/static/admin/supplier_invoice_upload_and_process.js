(function () {
  "use strict";

  var form = document.querySelector("[data-supplier-invoice-upload-and-process]");
  if (!form) {
    return;
  }

  form.addEventListener("submit", function () {
    var submit = form.querySelector("[data-upload-and-process-submit]");
    if (submit) {
      submit.disabled = true;
      submit.textContent = "PROCESANDO...";
    }
  });
}());
