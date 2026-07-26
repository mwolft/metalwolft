export type DeliveryEstimate = {
  start_date: string;
  end_date: string;
  is_active: true;
};

type CivilDate = {
  year: number;
  month: number;
  day: number;
};

type FetchDeliveryEstimateOptions = {
  apiBaseUrl?: string | null;
  fetcher?: typeof fetch;
};

const LOCAL_API_URL = "http://127.0.0.1:3001";
const ISO_CIVIL_DATE = /^(\d{4})-(\d{2})-(\d{2})$/;
const MONTHS_ES = [
  "enero",
  "febrero",
  "marzo",
  "abril",
  "mayo",
  "junio",
  "julio",
  "agosto",
  "septiembre",
  "octubre",
  "noviembre",
  "diciembre"
] as const;

function configuredApiBaseUrl() {
  const candidates = [
    process.env.API_URL,
    process.env.NEXT_PUBLIC_API_URL,
    process.env.REACT_APP_BACKEND_URL,
    LOCAL_API_URL
  ];
  const configured = candidates.find(
    (value) => typeof value === "string" && value.trim().length > 0
  );

  return configured!.trim().replace(/\/$/, "");
}

export function parseCivilDate(value: unknown): CivilDate | null {
  if (typeof value !== "string") {
    return null;
  }

  const match = ISO_CIVIL_DATE.exec(value);
  if (!match) {
    return null;
  }

  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const utcDate = new Date(Date.UTC(year, month - 1, day));

  if (
    utcDate.getUTCFullYear() !== year ||
    utcDate.getUTCMonth() !== month - 1 ||
    utcDate.getUTCDate() !== day
  ) {
    return null;
  }

  return { year, month, day };
}

function civilDateKey(value: CivilDate) {
  return value.year * 10_000 + value.month * 100 + value.day;
}

export function parseDeliveryEstimate(payload: unknown): DeliveryEstimate | null {
  if (typeof payload !== "object" || payload === null) {
    return null;
  }

  const candidate = payload as Record<string, unknown>;
  if (candidate.is_active !== true) {
    return null;
  }

  const startDate = parseCivilDate(candidate.start_date);
  const endDate = parseCivilDate(candidate.end_date);
  if (!startDate || !endDate || civilDateKey(startDate) > civilDateKey(endDate)) {
    return null;
  }

  return {
    start_date: candidate.start_date as string,
    end_date: candidate.end_date as string,
    is_active: true
  };
}

export function formatCivilDateEs(value: string) {
  const date = parseCivilDate(value);
  if (!date) {
    return null;
  }

  return `${date.day} de ${MONTHS_ES[date.month - 1]} de ${date.year}`;
}

export function formatCivilDateRangeEs(startValue: string, endValue: string) {
  const startDate = parseCivilDate(startValue);
  const endDate = parseCivilDate(endValue);

  if (!startDate || !endDate || civilDateKey(startDate) > civilDateKey(endDate)) {
    return null;
  }

  if (startDate.year === endDate.year && startDate.month === endDate.month) {
    return `Del ${startDate.day} al ${endDate.day} de ${MONTHS_ES[endDate.month - 1]} de ${endDate.year}`;
  }

  if (startDate.year === endDate.year) {
    return `Del ${startDate.day} de ${MONTHS_ES[startDate.month - 1]} al ${endDate.day} de ${MONTHS_ES[endDate.month - 1]} de ${endDate.year}`;
  }

  return `Del ${formatCivilDateEs(startValue)} al ${formatCivilDateEs(endValue)}`;
}

export async function fetchDeliveryEstimate(
  options: FetchDeliveryEstimateOptions = {}
): Promise<DeliveryEstimate | null> {
  const apiBaseUrl = options.apiBaseUrl === undefined ? configuredApiBaseUrl() : options.apiBaseUrl;
  if (!apiBaseUrl) {
    return null;
  }

  try {
    const response = await (options.fetcher ?? fetch)(
      `${apiBaseUrl.replace(/\/$/, "")}/api/delivery-estimate`,
      { next: { revalidate: 300 } }
    );

    if (!response.ok) {
      return null;
    }

    return parseDeliveryEstimate(await response.json());
  } catch {
    return null;
  }
}
