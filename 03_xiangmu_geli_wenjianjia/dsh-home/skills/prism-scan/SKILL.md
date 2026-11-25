---
name: prism-scan
description: "Structural analysis through dynamically generated cognitive lenses. Generates the optimal analytical lens for the specific code/artifact, then executes it. Finds conservation laws, structural invariants, and concrete bugs that vanilla analysis misses. Use on any code file, system design, or text artifact."
version: 1.0.0
author: Cranot
license: MIT
platforms: [linux, macos, windows]
allowed-tools: ["Read"]
metadata:
  hermes:
    tags: [Prism, Analysis, Code-Analysis, Code-Review, Architecture, Quality]
    related_skills: [prism-full, prism-3way, prism-discover, prism-reflect]
    homepage: https://github.com/Cranot/super-hermes
---

# Prism Scan — Structural Analysis via Dynamic Cognitive Lenses

## When to Use

Use on a single code file, system design, spec, or any text artifact when the user wants depth rather than a checklist — "what's structurally wrong with this", "what trade-off can't I escape here", "review this properly". Also the right entry point when the user names a focus ("focusing on security", "with emphasis on performance"). For maximum depth on an important artifact use `/prism-full`; to map which angles are worth taking first use `/prism-discover`.

You perform TWO steps. Both are mandatory. Do not skip either.

## STEP 0: Check for prior constraint knowledge (growth)

Look for a `.prism-history.md` file in the current project directory. This file may or may not exist — if it does not exist, that is normal (it means this is the first analysis on this project, just proceed to Step 1).

If the file DOES exist, read it. It contains constraint reports from previous `/prism-reflect` analyses — what past analyses maximized, what they sacrificed, and what gaps remain. Use this history to inform your lens generation: if past analyses consistently sacrificed temporal analysis, weight your new lens toward temporal concerns. The agent grows by not repeating the same blind spots.

## STEP 1: Cook the lens

You are a lens generator. Read the artifact the user provided. Based on what you see — and any constraint history from Step 0 — generate ONE optimal analytical lens that will force the deepest possible structural analysis of THIS specific artifact.

Study these scored examples of excellent lenses:

SCORED 9.5/10: "Identify every explicit choice this artifact makes. For each, name the alternative it invisibly rejects. Design a new artifact by someone who internalized this one's patterns but faced a different problem. Trace which transferred patterns create silent problems. Name the pedagogy law."

SCORED 9/10: "Extract every empirical claim this artifact embeds. For each, assume it is false. Trace the corruption. Build three alternatives, each inverting one claim. Predict which false claim causes the slowest, most invisible failure."

SCORED 9/10: "Run this artifact forward through 3 maintenance cycles. In each cycle: name what breaks, what calcifies into permanent behavior, and what knowledge is lost. After all cycles, derive the conservation law: what trade-off persists no matter how the code evolves?"

Your lens must:
- Be specific to what you observe in this artifact (not generic)
- If the user specified a FOCUS (e.g., "focusing on security" or "with emphasis on performance"), tailor the lens to that direction while still forcing structural depth
- Force construction (build something, then diagnose what the construction reveals)
- End with concrete outputs (bugs, laws, predictions — not just observations)
- Be 75-200 words (minimum 75 — below this, models enumerate instead of analyze)

Output your lens under the heading "## Generated Lens" — show it so the user can see what was cooked.

## STEP 2: Execute the lens

Now execute your generated lens against the artifact. Follow every instruction in the lens. Output the complete analysis. Do not summarize, do not ask permission, do not skip steps.

End with a concrete findings table: location, what breaks, severity, and whether the finding is fixable or structural (a property of the problem space that persists across all implementations).

After the findings table, append a brief constraint footer:

```
---
CONSTRAINT NOTE: This analysis maximized [what your lens focused on].
It did not examine: [1-2 specific alternative angles].
For deeper analysis: /prism-full | For meta-analysis: /prism-reflect
```

## Reliability Note

For guaranteed single-shot execution (no agentic loops), use `--tools ""` flag when running via Claude CLI. This ensures the model executes the full analysis in one response rather than splitting into multiple turns.

## Proven Prisms (reference material)

STEP 1 always cooks a fresh lens — that is the point of this skill, and these files do not change it. They ship alongside the skill as pre-validated alternatives for the two cases where a fixed lens is wanted: the user asks for a specific prism by name, or asks for a scored/reproducible lens instead of a generated one. Load one on demand with `skill_view("prism-scan", "<path>")`.

| Path | Finds | Score |
|---|---|---|
| `references/error_resilience.md` | Corruption cascades — silent exits, deferred failures, state corruption | 10.0/10 |
| `references/l12.md` | Conservation laws + meta-laws + concrete bugs | 9.8/10 |
| `references/optimize.md` | Critical-path tracing; safe fixes (less work) vs unsafe (skipped work) | 9.5/10 |
| `references/identity.md` | What the artifact claims to be vs what it is | 9.5/10 |
| `references/deep_scan.md` | Information destruction, laundering, silent transformation | 9.0/10 |
| `references/claim.md` | Assumption inversion — what if the embedded claims are false | 9.0/10 |
| `references/simulation.md` | Temporal prediction — what breaks, calcifies, and is lost over time | 9.0/10 |

Each file is a complete standalone analytical program and also works as a system prompt outside Hermes.
