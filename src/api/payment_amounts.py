from decimal import Decimal, InvalidOperation


class PaymentAmountValidationError(ValueError):
    def __init__(self, provider, currency, total_amount, minimum_amount=None, reason=None):
        self.provider = provider
        self.currency = currency
        self.total_amount = total_amount
        self.minimum_amount = minimum_amount
        self.reason = reason or "unsupported_amount"
        super().__init__(
            f"Payment amount rejected: provider={provider} currency={currency} "
            f"total_amount={total_amount} minimum_amount={minimum_amount} reason={self.reason}"
        )


PAYMENT_MINIMUM_AMOUNTS = {
    ("stripe", "eur"): Decimal("0.50"),
    ("paypal", "eur"): Decimal("0.01"),
}


def _to_decimal(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise PaymentAmountValidationError(None, None, value, reason="invalid_amount")
    if not amount.is_finite():
        raise PaymentAmountValidationError(None, None, value, reason="invalid_amount")
    return amount


def validate_payment_amount(provider, total_amount, currency="eur"):
    normalized_provider = str(provider or "").strip().lower()
    normalized_currency = str(currency or "").strip().lower()
    amount = _to_decimal(total_amount)
    minimum_amount = PAYMENT_MINIMUM_AMOUNTS.get((normalized_provider, normalized_currency))

    if not normalized_provider:
        raise PaymentAmountValidationError(
            normalized_provider,
            normalized_currency,
            amount,
            reason="unknown_provider",
        )

    if not normalized_currency:
        raise PaymentAmountValidationError(
            normalized_provider,
            normalized_currency,
            amount,
            reason="unknown_currency",
        )

    if amount <= Decimal("0"):
        raise PaymentAmountValidationError(
            normalized_provider,
            normalized_currency,
            amount,
            minimum_amount=minimum_amount,
            reason="non_positive_amount",
        )

    if minimum_amount is None:
        raise PaymentAmountValidationError(
            normalized_provider,
            normalized_currency,
            amount,
            reason="unsupported_provider_currency",
        )

    if amount < minimum_amount:
        raise PaymentAmountValidationError(
            normalized_provider,
            normalized_currency,
            amount,
            minimum_amount=minimum_amount,
            reason="below_provider_minimum",
        )

    return amount
