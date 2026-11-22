# Web application

The M9 Next.js/TypeScript evidence console renders only versioned REST API responses. It compares two ephemeral snippets, registers allowlisted repositories, starts and follows scans, filters clone results, and displays detector/version metadata, explanation codes, limitations, and exact source ranges. The responsive layout stacks code editors on narrow screens and presents them side by side when space permits. The UI deliberately states that similarity is not proof of plagiarism, authorship, or semantic equivalence.

## Development

```sh
npm ci
npm run lint
npm run typecheck
npm run build
npx playwright install chromium
npm run test:e2e
```

Set `NEXT_PUBLIC_API_BASE_URL` to the API's `/api/v1` base. It defaults to `http://localhost:8000/api/v1`. The browser test intercepts that contract with deterministic fixtures; production code contains no demo clone data.
