"use client";

import type { FormEvent } from "react";

type CheckoutDiscountFormProps = {
  appliedCode: string | null;
  feedback: { type: "error" | "success"; message: string } | null;
  inputValue: string;
  isApplying: boolean;
  onApply: (event: FormEvent<HTMLFormElement>) => void;
  onChange: (value: string) => void;
  onRemove: () => void;
};

export function CheckoutDiscountForm({
  appliedCode,
  feedback,
  inputValue,
  isApplying,
  onApply,
  onChange,
  onRemove
}: CheckoutDiscountFormProps) {
  const hasAppliedCode = Boolean(appliedCode);

  return (
    <form className="mw-discount-form" onSubmit={onApply}>
      <label className="mw-field" htmlFor="checkout-discount-code">
        <span>Codigo de descuento</span>
        <input
          autoComplete="off"
          id="checkout-discount-code"
          inputMode="text"
          name="discount_code"
          onChange={(event) => onChange(event.target.value)}
          placeholder="Introduce tu codigo"
          type="text"
          value={inputValue}
        />
      </label>

      <div className="mw-discount-form__actions">
        <button className="mw-button mw-button--secondary" disabled={isApplying} type="submit">
          {isApplying ? "Validando..." : hasAppliedCode ? "Actualizar codigo" : "Aplicar codigo"}
        </button>
        {hasAppliedCode ? (
          <button
            className="mw-discount-form__remove"
            disabled={isApplying}
            onClick={onRemove}
            type="button"
          >
            Retirar
          </button>
        ) : null}
      </div>

      {feedback ? (
        <p
          aria-live="polite"
          className={`mw-discount-form__message ${
            feedback.type === "error" ? "is-error" : "is-success"
          }`}
        >
          {feedback.message}
        </p>
      ) : null}
    </form>
  );
}
