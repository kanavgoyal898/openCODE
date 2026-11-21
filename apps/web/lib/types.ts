export type Repository = { id: string; name: string; originRedacted: string | null; createdAt: string };
export type Scan = {
  id: string;
  repositoryId: string;
  status: "queued" | "running" | "completed" | "partial" | "failed" | "cancelled";
  counts: Record<string, number>;
};
export type SourceRange = {
  repository_id: string;
  revision_id: string;
  fragment_id: string;
  start_line: number;
  end_line: number;
};
export type CloneMatch = {
  id: string;
  category: "type1" | "type2" | "type3" | "type4";
  evidence_state: "verified" | "candidate" | "rejected";
  detector_id: string;
  algorithm_version: string;
  left: SourceRange;
  right: SourceRange;
  leftSource?: string;
  rightSource?: string;
  scores: { fingerprint_jaccard: number | null; query_coverage: number; candidate_coverage: number; token_jaccard: number };
  evidence: { explanation_codes: string[] };
  limitations: string[];
};
