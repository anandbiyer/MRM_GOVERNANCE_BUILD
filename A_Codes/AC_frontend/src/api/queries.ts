import { useQuery, type QueryClient, type QueryKey } from "@tanstack/react-query";
import { api } from "./client";
import type { Model360, ModelMeta, ModelRiskReport, ModelRiskReportDetail } from "./types";

/**
 * Reads that are *derived* from governance records rather than owned by one screen: the server
 * recomputes them on every request, so any governance write makes all of them stale.
 *
 * Listed once, here, on purpose. They used to be named by hand at each mutation site, and nine of
 * those sites had simply never listed `["dashboard"]` — so closing a finding or changing a score
 * weight left the Command Center showing old tiles, an old score and a resolved insight for up to
 * the 30s staleTime (review finding CR-06). Add a new derived read here and every mutation picks it
 * up; a new Monitoring or Data Audit dashboard will need exactly one line.
 */
const DERIVED_FROM_GOVERNANCE: QueryKey[] = [["dashboard"], ["models"], ["completeness"], ["audit"]];

/** Call after any governance write. `also` takes the keys only that mutation affects. */
export function invalidateGovernance(qc: QueryClient, ...also: QueryKey[]): void {
  for (const queryKey of [...DERIVED_FROM_GOVERNANCE, ...also]) qc.invalidateQueries({ queryKey });
}

/**
 * A policy change moves thresholds, weights, score bands and allowed values at once, so it
 * invalidates the vocabularies as well as everything derived from them.
 */
export function invalidatePolicy(qc: QueryClient): void {
  invalidateGovernance(qc, ["policy"], ["model-meta"]);
}

/**
 * Drop every cached read, then read the identity again.
 *
 * For a role switch or a reset, everything cached was fetched as a different user or against data
 * that no longer exists, so clearing is right. Clearing *alone* was not: `["me"]` has a mounted
 * observer whose inputs do not change across a switch, so dropping the entry left `me` at its
 * previous value — the token became the new role while the application kept the old one's
 * permissions, and only a full page reload fixed it (FT-03, plan G0.21). The refetch is what makes
 * the new identity take effect.
 */
export async function resetCachesAndIdentity(qc: QueryClient): Promise<void> {
  // Invalidate rather than clear. `clear()` removes the queries outright, which leaves the mounted
  // `["me"]` observer holding its last value with nothing to refetch — a `refetchQueries` after a
  // `clear()` matches nothing at all, which is why the first attempt at this fix changed nothing.
  // Invalidation marks every cached read stale and refetches the active ones, so the identity is
  // re-read and the rest follows on next use.
  await qc.invalidateQueries();
}

export function useModelMeta() {
  return useQuery({ queryKey: ["model-meta"], queryFn: () => api<ModelMeta>("/api/models/meta"), staleTime: 60_000 });
}

export function useModel360(modelId: string | undefined) {
  return useQuery({
    queryKey: ["model", modelId],
    queryFn: () => api<Model360>(`/api/models/${modelId}`),
    enabled: !!modelId,
  });
}

/** Resolve a user id to "Full Name (U-123)" using the meta user list. */
export function userLabel(meta: ModelMeta | undefined, id: string | null | undefined): string {
  if (!id) return "—";
  const u = meta?.users.find((x) => x.user_id === id);
  return u ? `${u.full_name} (${id})` : id;
}

/**
 * Stored model risk reports (REQ-REG-10A). Not in `DERIVED_FROM_GOVERNANCE`: a stored report is a
 * record of what the portfolio looked like when it was generated, so a later governance write must
 * *not* make it stale. Only generating a new one invalidates the list.
 */
export function useModelRiskReports() {
  return useQuery({
    queryKey: ["model-risk-reports"],
    queryFn: () => api<ModelRiskReport[]>("/api/reports/model-risk"),
  });
}

export function useModelRiskReport(reportId: string | undefined) {
  return useQuery({
    queryKey: ["model-risk-report", reportId],
    queryFn: () => api<ModelRiskReportDetail>(`/api/reports/model-risk/${reportId}`),
    enabled: !!reportId,
    staleTime: Infinity,  // a stored report never changes
  });
}
