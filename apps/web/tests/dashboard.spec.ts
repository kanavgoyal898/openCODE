import { expect, test } from "@playwright/test";

const match = {
  id: "clone-1", category: "type1", evidence_state: "verified", detector_id: "exact-clone-detector", algorithm_version: "fp-v1",
  left: { repository_id: "repo", revision_id: "r1", fragment_id: "one.py", start_line: 1, end_line: 2 },
  right: { repository_id: "repo", revision_id: "r2", fragment_id: "two.py", start_line: 1, end_line: 2 },
  scores: { fingerprint_jaccard: 1, query_coverage: 1, candidate_coverage: 1, token_jaccard: 1 },
  evidence: { explanation_codes: ["CANONICAL_TOKEN_EQUALITY"] }, limitations: ["NOT_PLAGIARISM_PROOF"],
};

test("scans, filters, and shows accessible evidence from API responses", async ({ page }) => {
  await page.route("http://localhost:8000/api/v1/**", async route => {
    const url = route.request().url();
    if (url.endsWith("/repositories")) return route.fulfill({ json: { items: [{ id: "repo", name: "Fixture", originRedacted: "/fixture", createdAt: "2026-01-01" }] } });
    if (url.endsWith("/scans") && route.request().method() === "POST") return route.fulfill({ json: { id: "scan", repositoryId: "repo", status: "queued", counts: {} } });
    if (url.endsWith("/scans/scan")) return route.fulfill({ json: { id: "scan", repositoryId: "repo", status: "completed", counts: { files: 2, clones: 1 } } });
    if (url.includes("/clones?")) return route.fulfill({ json: { items: [match] } });
    if (url.endsWith("/clones/clone-1")) return route.fulfill({ json: { ...match, leftSource: "def same():\n  return 1", rightSource: "def same():\n  return 1" } });
    return route.fulfill({ status: 404, json: {} });
  });
  await page.goto("/");
  await expect(page.getByLabel("Repository")).toHaveValue("repo");
  await page.getByRole("button", { name: "Start scan" }).click();
  await expect(page.getByText("completed", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "type1" }).click();
  await expect(page.getByLabel("Selected clone evidence")).toBeVisible();
  await expect(page.getByText("CANONICAL_TOKEN_EQUALITY")).toBeVisible();
  await expect(page.locator(".matched")).toHaveCount(4);
  await page.getByLabel("Language").selectOption("java");
  await expect(page.getByText("No clone results for the active filters.")).toBeVisible();
  await page.keyboard.press("Tab");
  await expect(page.locator(":focus")).toBeVisible();
});
