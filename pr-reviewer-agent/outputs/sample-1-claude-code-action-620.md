## PR Review

Reviewed: https://github.com/anthropics/claude-code-action/pull/620
(feat: manifest-based GitHub App creation + interactive create-app.html)

### Summary
Adds a `github-app-manifest.json` with the permissions and webhook
events the action needs, plus an interactive `docs/create-app.html`
page that encodes the manifest and deep-links into GitHub's
"create app from manifest" flow. Docs-only change: no runtime code in
the action itself is touched, so blast radius is limited to the
new-user onboarding path.

### Risks
- `github-app-manifest.json` sets `redirect_url` to
  `https://github.com/settings/apps/new`. That is the app-creation
  endpoint, not a post-creation landing page — users get redirected
  back into the creation form after finishing, which is confusing and
  may read like a loop. Likely should point at the docs/setup page
  (matching `setup_url`) or be omitted.
- `hook_attributes.url` ships the literal placeholder
  `https://example.com/github/webhook`. `active` is `false` so it is
  inert today, but a user who flips it later without noticing the
  placeholder gets a silently dead webhook.
- `create-app.html` builds the manifest deep link with
  `state=${Date.now()}`. `state` is a CSRF token; a millisecond
  timestamp is predictable. Low impact for this flow, but
  `crypto.getRandomValues` is a one-line change.
- The second commit balloons `create-app.html` to ~800 changed lines
  of inline JS in a docs page. No CSP or sanitization concerns since
  it is static, but maintenance burden concentrates in one file.

### Suggestions
- Point `redirect_url` at the rendered setup doc or remove it.
- Add a comment/visible note near `hook_attributes.url` saying it is
  a placeholder to replace, or drop `hook_attributes` entirely while
  it is inactive.
- Replace `Date.now()` state with `crypto.getRandomValues(new
  Uint32Array(1))[0].toString(36)`.
- Consider linking `create-app.html` from `setup.md` prominently — it
  is the fastest path and currently reads as an aside.

### Confidence: Medium
The diff is self-contained and fully reviewable (docs + one JSON +
one static HTML), but correctness of the manifest flow depends on
GitHub's manifest API semantics, which are not verifiable from the
diff alone — the `redirect_url` concern may be intentional.
