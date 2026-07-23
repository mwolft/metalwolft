type MetalSpinnerVariant = "inline" | "block" | "page";

type MetalSpinnerProps = {
  variant?: MetalSpinnerVariant;
  label?: string;
  className?: string;
};

export function MetalSpinner({
  variant = "inline",
  label = "Cargando",
  className
}: MetalSpinnerProps) {
  const classes = ["mw-metal-spinner", `mw-metal-spinner--${variant}`, className]
    .filter(Boolean)
    .join(" ");

  return (
    <span className={classes} role="status" aria-live="polite">
      <svg viewBox="0 0 48 48" aria-hidden="true" focusable="false">
        <circle className="mw-metal-spinner__track" cx="24" cy="24" r="18" />
        <circle className="mw-metal-spinner__arc" cx="24" cy="24" r="18" />
        <circle className="mw-metal-spinner__spark" cx="39" cy="14" r="2.5" />
      </svg>
      <span className="mw-visually-hidden">{label}</span>
    </span>
  );
}
