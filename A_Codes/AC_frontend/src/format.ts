/**
 * Display formatting for the dates the API returns.
 *
 * The API has two kinds of date, and they must not be rendered the same way:
 *
 *   date-only   `"2026-09-30"`                  a business date — a calendar day, no time, no zone
 *   timestamp   `"2026-09-30T14:03:11.812Z"`    an instant
 *
 * `new Date("2026-09-30")` parses the **date-only** form as midnight **UTC**, so
 * `toLocaleDateString()` renders the previous calendar day anywhere behind UTC. The Command Center
 * read "as of 9/29/2026" for business date 2026-09-30, and M-0012's last validation 2026-04-16
 * showed as 4/15/2026. It is invisible in UTC, which is why CI and the parity harness never saw it
 * (review findings MP-10 / FT-06).
 *
 * `formatDate` therefore never hands a date-only string to `Date`'s parser: it reads the three
 * numbers and builds the date in **local** time, where the calendar day cannot shift. Timestamps
 * keep going through `Date`, which is correct for them — an instant genuinely does belong to a
 * different local day depending on where you are.
 *
 * Use `formatDate` for every date-only value shown to a user, including in tables that used to
 * print the raw ISO string: the serious half of MP-10 was not the offset but that the revalidation
 * timeline and Model 360 showed the same model two different due dates. One formatter, one answer.
 *
 * Do not use it for CSV export or for anything a machine reads — ISO is right there.
 */

const DATE_ONLY = /^(\d{4})-(\d{2})-(\d{2})$/;

export function formatDate(value: string | null | undefined, fallback = "—"): string {
  if (!value) return fallback;
  const m = DATE_ONLY.exec(value.slice(0, 10));
  if (!m) return value; // not a date we recognise: show it rather than guess
  const [, year, month, day] = m;
  return new Date(Number(year), Number(month) - 1, Number(day)).toLocaleDateString();
}

/** An instant, with its time. Safe through `Date` — the value carries its own zone. */
export function formatDateTime(value: string | null | undefined, fallback = "—"): string {
  return value ? new Date(value).toLocaleString() : fallback;
}
