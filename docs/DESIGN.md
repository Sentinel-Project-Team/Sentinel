# Sentinel Design Rules (binding for every UI in this repo)

## Identity
Security tooling: dense, calm, precise. Think terminal or ops console,
not marketing site.

## Banned (these are the slop tells)
- Purple-to-blue gradients, glassmorphism, glowing neon, gradient text
- Emoji used as icons or in headings
- Generic hero sections, floating blobs, decorative illustrations
- Cards inside cards; every element rounded-2xl with a shadow
- Lorem ipsum or invented numbers. Charts must use real data or show an
  empty state
- Fake loading animations, bouncy transitions, auto-playing motion
- The default Inter-on-white-with-indigo-button look

## Required
- All colors, spacing, radii, and fonts come from tokens in ui/tokens.css.
  No raw hex values or magic pixel numbers inside components.
- One UI typeface family (distinctive but readable) plus one monospace
  font for prompts, responses, canaries, and rule files.
- Dark theme by default. A light theme is optional and must work through
  tokens only.
- Semantic colors are reserved: red = leak or blocked, green = allowed or
  safe, amber = warning or cleaned. Never use them decoratively.
- Use tables, not cards, for log data. Prompts and responses are always in
  monospace, with canary matches highlighted.
- Every screen needs an empty state, a loading state, and an error state.
- Spacing on a 4px scale. Maximum 2 font weights. Minimum 4.5:1 text
  contrast.
- Charts: before and after always share the same axis, with labeled units.
  No 3D. No pie charts for comparisons.
- Copy is plain and specific ("Leaked 3 of 12 canaries"), never hype
  ("Supercharge your AI security!").
