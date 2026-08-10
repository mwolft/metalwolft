export const DEFAULT_SCREW_OPTION = "standard";
export const NOT_APPLICABLE_SCREW_OPTION = "not_applicable";

const AMOUNT_FORMATTER = new Intl.NumberFormat("es-ES", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
});

export type ScrewConfiguration = {
  screw_option?: string | null;
  screw_length_mm?: number | null;
  screw_supplement?: number | string | null;
};

export function selectCompatibleScrewOption(
  current: string,
  options: ReadonlyArray<{ value: string }>,
  preferred = DEFAULT_SCREW_OPTION
) {
  if (options.some((option) => option.value === current)) {
    return current;
  }
  return (
    options.find((option) => option.value === preferred)?.value ??
    options[0]?.value ??
    DEFAULT_SCREW_OPTION
  );
}

export function formatScrewConfiguration(configuration: ScrewConfiguration) {
  const length = Number(configuration.screw_length_mm);
  if (!Number.isFinite(length) || length <= 0) {
    return null;
  }

  const supplement = Number(configuration.screw_supplement ?? 0);
  if (Number.isFinite(supplement) && supplement > 0) {
    return `${length.toLocaleString("es-ES")} mm (+${AMOUNT_FORMATTER.format(supplement)} €)`;
  }

  return `${length.toLocaleString("es-ES")} mm incluidos`;
}
