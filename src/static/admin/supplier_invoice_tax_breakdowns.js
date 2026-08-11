(function () {
  "use strict";

  function nextPosition(container) {
    var highest = 0;
    var inputs = container.querySelectorAll('input[name$="-position"]');

    inputs.forEach(function (input) {
      var value = Number.parseInt(input.value, 10);
      if (Number.isInteger(value) && value > highest) {
        highest = value;
      }
    });

    return highest + 1;
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-supplier-invoice-inline-add]");
    if (!button) {
      return;
    }

    event.preventDefault();
    var container = button.closest("[data-supplier-invoice-breakdowns]");
    var fieldId = button.getAttribute("data-supplier-invoice-inline-add");
    if (!container || !fieldId || !window.faForm) {
      return;
    }

    var position = nextPosition(container);
    window.faForm.addInlineField(button, fieldId);

    var positionInputs = container.querySelectorAll('input[name$="-position"]');
    var newPositionInput = positionInputs[positionInputs.length - 1];
    if (newPositionInput && !newPositionInput.value) {
      newPositionInput.value = position;
    }
  });
}());
