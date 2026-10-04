// Presentation-only colour mapping for status values. No business rules here:
// every status shown is calculated by the server, and the score band boundaries are read from policy.
import { useModelMeta } from "../api/queries";

const TONES: Record<string, string> = {
  High: "p-bad", Medium: "p-warn", Low: "p-good",
  Critical: "p-bad",
  Overdue: "p-bad", "Due Soon": "p-warn", Scheduled: "p-info",
  Approved: "p-good", Conditional: "p-warn", Rejected: "p-bad", "In Progress": "p-info",
  Open: "p-warn", Closed: "p-mute", Deferred: "p-mute", "Accepted Risk": "p-mute", Met: "p-good",
};

export function Pill({ value, tone }: { value: string | null | undefined; tone?: string }) {
  if (!value) return <span style={{ color: "var(--faint)" }}>—</span>;
  return <span className={`pill ${tone ?? TONES[value] ?? "p-mute"}`}>{value}</span>;
}

export function SeverityPill({ value }: { value: string }) {
  return <Pill value={value} tone={value === "Low" ? "p-info" : undefined} />;
}

export function ScoreValue({ value }: { value: string | null }) {
  // The band boundaries are policy settings (CR-01), so they are read rather than restated here.
  // Until meta arrives the number is shown in the default colour instead of a guessed band.
  const meta = useModelMeta();
  if (value === null) return <span style={{ color: "var(--faint)" }}>n/a</span>;
  const n = Number(value);
  const warn = meta.data?.score_band_warn_min;
  const good = meta.data?.score_band_good_min;
  const colour = good !== undefined && n >= good ? "var(--good)"
    : warn !== undefined && n >= warn ? "var(--warn)"
    : warn !== undefined ? "var(--bad)" : undefined;
  return <span className="mono" style={{ color: colour, fontWeight: 600 }}>{Number(value).toFixed(1)}</span>;
}

export function DaysToDue({ days }: { days: number | null }) {
  if (days === null) return <span style={{ color: "var(--faint)" }}>—</span>;
  if (days < 0) return <span className="mono" style={{ color: "var(--bad)" }}>{-days}d overdue</span>;
  return <span className="mono">{days}d</span>;
}
