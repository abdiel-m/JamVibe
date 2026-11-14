# Design polish research for JamVibe

Researched 2026-11-14. **[G]** marks a published guideline or spec. **[P]** marks practitioner opinion. **[M]** marks something I measured. Apple HIG and Material 3 pages render with JS, so I read the HIG through Apple's JSON data endpoints and took the M3 motion tokens from the `material-web` token source.

## Recommendations for JamVibe

1. **Remove the per-tab color washes.** Keep one accent (#FF8A4C) and one neutral surface ramp. Five tinted heroes are the main source of the "gamey" feel.
2. **Swap borders for surface steps.** Delete `border: 1px solid var(--line)` from `.card`, `.chip`, `.artist-btn` and `.seg`. Separate things with 2 to 3 surface tones (for example #14131C, #1B1A24, #23222E) and with space.
3. **Replace the `ui-rounded` stack with an embedded pair.** Use **Bricolage Grotesque** (600 to 800) for display and **Instrument Sans** (400 to 600) for body. Subset both to Latin as woff2. Together they cost about 82 KB as base64.
4. **Stop using monospace for numbers.** Set `font-variant-numeric: tabular-nums` on the body face for scores, %, ranks and play counts. A monospace face used for data labels is a listed AI tell.
5. **Build one editorial header per screen.** A large left-aligned title (32 to 40px, tight tracking, `text-wrap: balance`) with one plain-language line under it, such as "Maya leads by 212 plays, 9 days left." Drop pill and eyebrow labels above headings.
6. **Lock spacing to a 4px scale.** Use 4, 8, 12, 16, 24, 32 and 48. Use 16px side gutters at 390px and 32 to 48px between sections.
7. **Make the leaderboard asymmetric.** Show the #1 row big (name, count, margin), then dense tabular rows below it.
8. **Trim the tab bar to 4 labeled tabs in a floating pill.** For example Home, Race, Match and Recap, with Challenges living inside Race or Home. Keep text labels and use one icon set (Lucide, 2px stroke, 24 grid). The active tab gets an accent pill behind it, not a scale bounce.
9. **Remove the overshoot spring (`cubic-bezier(0.3,1.5,…)`), the infinite crown animation, the glow pulse and the stagger on every screen entry.** Use ease-out 150 to 250ms, with one emphasized curve for sheets. The infinite crown also breaks WCAG 2.2.2 if it runs longer than 5 seconds.
10. **Use View Transitions for one shared element.** The avatar or row should morph from leaderboard to profile and the recap stat into its share card. Skip the transition when reduced motion is on.
11. **Turn share cards into typographic templates.** Offer 3 layouts (Big Number, Ranked List, Versus) × 4 to 6 curated palettes × the user's own top artist and stat. Keep a safe zone at the top and bottom of the 9:16 frame.
12. **Write real micro-copy.** Use specific numbers and names instead of "Great job!" or "Let's go!".

## (a) Common tells of generic AI-made UIs

- **Indigo and purple defaults [P].** Adam Wathan joked, half apologizing, in August 2025 that the indigo buttons in Tailwind UI shaped the look of AI-built interfaces ([coverage](https://news.aibase.com/news/20365), [DEV](https://dev.to/alanwest/why-every-ai-built-website-looks-the-same-blame-tailwinds-indigo-500-3h2p)). The training-data explanation is commentary, not a documented finding. JamVibe's violet Recap tab and its #14131C purple-tinted near-black lean toward this.
- **Anthropic's own frontend-design skill lists generated-page tells [P/G-ish].** They include "a near-black background with a single bright acid-green or vermilion accent", "a monospace face for small data labels", "a tracked-out ALL-CAPS eyebrow label above every heading" and "the SaaS-card kit: content chopped into identical rounded cards". It adds that these traits are fine for some briefs, and the problem is that they "appear regardless of subject" ([SKILL.md](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md)). JamVibe currently has the dark-plus-orange accent, mono numbers and card-everything. The fix is music-specific choices, not a different default.
- **Too many borders [P].** Refactoring UI: "Use fewer borders. Instead, try adding a box shadow, using contrasting background colors, or simply adding more space" ([refactoringui.com](https://refactoringui.com/)). Its Medium article adds: "If you're already using different background colors in addition to a border, try removing the border" ([Medium](https://medium.com/refactoring-ui/7-practical-tips-for-cheating-at-design-40c736799886)). JamVibe pairs #1E1D29 cards with #2C2B3A borders, a 1.2:1 contrast **[M]** that adds noise without separating anything.
- **Bouncy or over-animated motion [G].** HIG: "Don't add motion for the sake of adding motion" and "generally avoid adding motion to UI interactions that occur frequently" ([HIG Motion](https://developer.apple.com/design/human-interface-guidelines/motion)).
- **Contrast is fine.** Muted #A7A3B5 on #1E1D29 is 6.77:1 and orange on bg 7.89:1, above 4.5:1 ( [WCAG 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)) **[M]**. Any kept input border needs 3:1 ( [WCAG 1.4.11](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)).

## (b) Typography

The candidates below are all SIL OFL 1.1 and live in the `ofl/` tree of [google/fonts](https://github.com/google/fonts/tree/main/ofl), so they can be embedded. Bricolage's OFL.txt was checked directly ([repo](https://github.com/ateliertriay/bricolage)). I measured the files **[M]**: subset to Basic Latin, Latin-1, smart quotes, dashes, arrows, minus and ×, with `kern,liga,calt,tnum,lnum,case` kept, using `fonttools`.

| Face | Role | Why | woff2 (wght 400–800, other axes dropped) | base64 |
|---|---|---|---|---|
| **Bricolage Grotesque** | Display | Quirky ink-trap grotesque with optical-size and width axes. Expressive at 32px and up without being "gamer". | 33.5 KB (117.6 KB with all axes) | 44.6 KB |
| **Instrument Sans** | Body / UI | Neutral, slightly condensed. Has tabular figures. Less overused than Inter. | 28.4 KB | 37.9 KB |
| Space Grotesk | Alt display | Geometric, techy, and the smallest. Max weight is 700. | 19.3 KB | 25.7 KB |
| Inter | Safe body alt | Legible, but the most common default (opinion-level tell). | 26.5 KB | 35.3 KB |

All four have `tnum`. Base64 adds about 33% **[M]**. Embed with `@font-face { src: url(data:font/woff2;base64,…) format("woff2"); font-display: swap; }`. Subset command:

```
pyftsubset Font.ttf --unicodes="U+0020-007E,U+00A0-00FF,U+2013-2014,U+2018-201D,U+2026,U+2190-2193,U+2212,U+00D7" \
  --layout-features="kern,liga,calt,tnum,lnum,case" --flavor=woff2 --output-file=font.woff2
# optional: fonttools varLib.instancer Font.ttf wght=400:800 wdth=drop opsz=drop -o lim.ttf  (first, to cut size ~3x)
```

Keep a system fallback for non-Latin artist names.

Typesetting rules:
- Track caps 5 to 12% and never track lowercase ([Butterick, letterspacing](https://practicaltypography.com/letterspacing.html)) **[P]**.
- Keep body lines to 45 to 90 characters ([Butterick, line length](https://practicaltypography.com/line-length.html)) **[P]**.
- Use `text-wrap: balance` on headings. It only applies to blocks of 6 lines or fewer in Chromium and 10 in Firefox. Use `pretty` on paragraphs ([MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/text-wrap)) **[G]**.
- HIG asks for single-word tab labels ([HIG Tab bars](https://developer.apple.com/design/human-interface-guidelines/tab-bars)) **[G]**.

## (c) Layout

- **Hierarchy comes from contrast in size, weight and space, not from boxes [P].** Refactoring UI offers backgrounds and spacing as the alternatives to borders ([refactoringui.com](https://refactoringui.com/)). In practice: one big number per screen, muted secondary text, lists as bare rows.
- **Spacing scale [P].** Refactoring UI recommends a fixed spacing and sizing system (from the book, not re-verified). Make section gaps clearly larger than in-group gaps.
- **Dark surfaces [G].** Material 3 replaces shadows with a tonal ramp of `surface-container-lowest…highest` roles, and content uses `on-surface` / `on-surface-variant` ([material-web color docs](https://github.com/material-components/material-web/blob/main/docs/theming/color.md)). Map JamVibe's `--bg/--card/--raise` to three steps like these and drop shadows and borders.
- **Tab bar [G].** "Use a tab bar to support navigation, not to provide actions." "Include tab labels." Fewer tabs are "generally easier to navigate". Keep the bar visible except under modals ([HIG Tab bars](https://developer.apple.com/design/human-interface-guidelines/tab-bars)). iOS 26's tab bar "floats above content" on a translucent material ([same](https://developer.apple.com/design/human-interface-guidelines/tab-bars)). A floating pill inset 12px from the edges with `env(safe-area-inset-bottom)` matches current platform style. If you blur behind it, keep the blur small, because blur is expensive to paint ([web.dev](https://web.dev/articles/animations-guide)).
- **Badges [G].** "Reserve badges for critical information" ([HIG](https://developer.apple.com/design/human-interface-guidelines/tab-bars)). A single "challenge ends today" badge works. Counters on every tab do not.

## (d) Motion

- **Tokens [G]** (Material 3, [token source](https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss)):
  - standard `cubic-bezier(0.2,0,0,1)`
  - emphasized-decelerate `cubic-bezier(0.05,0.7,0.1,1)` (enter)
  - emphasized-accelerate `cubic-bezier(0.3,0,0.8,0.15)` (exit)
  - short 50–200ms, medium 250–400ms, long 450–600ms

  JamVibe set: press 100ms; tab switch 200ms standard; sheet in 350ms decelerate, out 200ms accelerate; fills at most 600ms, once.
- **Short and ease-out [P].** Emil Kowalski says animations should "usually be shorter than 300ms". Use ease-out for responsiveness. Never animate keyboard-initiated actions. Consider how often a user will see an animation ([Great animations](https://emilkowal.ski/ui/great-animations)).
- **Interruptible [G/P].** HIG: "Let people cancel motion… don't make people wait for an animation to complete" ([HIG Motion](https://developer.apple.com/design/human-interface-guidelines/motion)). Rauno Freiberg makes the same point and adds that repeated animation "start[s] to feel more like cognitive burden" ([Invisible details](https://rauno.me/craft/interaction-design)). CSS transitions can be interrupted. Keyframe stagger on every tab switch cannot, so remove it.
- **Springs do not have to bounce [P].** Josh Comeau: springs are "Not just for bouncy/springy animations". High friction gives "buttery-smooth… motion that doesn't bounce around". `linear()` can approximate a spring in CSS ([Comeau](https://www.joshwcomeau.com/animation/a-friendly-introduction-to-spring-physics/)). If you keep a spring, make it critically damped (no overshoot). JamVibe's `1.5` control point overshoots about 15 to 20%.
- **Performance [G].** Animate only `transform` and `opacity` ([web.dev](https://web.dev/articles/animations-guide)). The hero color and ring fill trigger paint: fine once, not continuously.
- **Shared elements [G].** `document.startViewTransition(update)` plus a unique `view-transition-name` on the matching element in the old and new state ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API)). Feature-detect it and call `update()` directly as the fallback. Under `prefers-reduced-motion: reduce`, set the `::view-transition-*` animations to `none` or a short crossfade (MDN does not state this rule, so treat it as my recommendation).
- **Reduced motion and auto-motion [G].** [WCAG 2.3.3](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html) (AAA) says interaction-triggered motion must be possible to disable. WCAG 2.2.2 (A) requires a pause control for auto-moving content that lasts longer than 5 seconds ([Understanding 2.2.2](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html); I could not fetch it during this session, so this is from the known SC text). Remove the infinite crown loop rather than add a control. HIG: "Make motion optional" and don't rely on motion alone to convey information ([HIG Motion](https://developer.apple.com/design/human-interface-guidelines/motion)).

## (e) Share cards

These patterns are practitioner opinion **[P]**. I found no primary guideline for them.
- **Templates beat a single fixed card.** Use a small set of layouts that are each built around *one* idea:
  - Big Number: "4,812 plays" in a 120px display face, with the artist underneath.
  - Ranked List: top 5 with tabular numbers, the #1 row oversized.
  - Versus / Compatibility: two names and one % split across the frame.
- **Curated palettes, not a free color picker.** Offer 4 to 6 contrast-tested pairs (ink on bone, orange on near-black, a duotone). The user picks stat and palette; the template enforces layout.
- **Type does the work.** Put one display size per card, set big, with tight leading and flush left. Small logo at the bottom. No borders, glows or confetti.
- **Respect the overlay chrome.** Story UIs cover the top and bottom of the frame. Third-party guides say to keep about 14% of the height clear at the top and 20 to 35% at the bottom on a 1080×1920 canvas, with about 6% on the sides ([example guide](https://adnova.ai/blogs/meta-ad-safe-zones-guide)). These figures are unverified against Meta's own docs, so design to the conservative end.
- **Render at 1080×1920** to canvas with the same embedded fonts. Wait for `document.fonts.ready` before drawing, or the card falls back to a system face.

## (f) Icons and small details

- **One icon set, one stroke [G for that set].** Lucide's spec: a 24×24 canvas, a 1px safe zone, and "2 pixel centered strokes with round caps and joins". Don't mix stroke widths. Balance icons visually rather than centering them mathematically ([Lucide design guide](https://lucide.dev/guide/design/icon-design-guide)). The license is ISC, with Feather-derived icons under MIT ([license](https://lucide.dev/license)), so the SVGs can be inlined freely. Use filled variants only for the active tab.
- **Tabular numbers** on any number that updates or sits in a column: `font-variant-numeric: tabular-nums` (all recommended faces support `tnum` **[M]**). Use proportional figures in prose.
- **Optical details [P].** Rank numbers in a fixed-width column; nudge play triangles about 1px right; align icons to cap height; use real minus (−), × and en-dashes.
- **Micro-copy [P].** Name people and numbers ("You and Sam share 14 artists; Sam is ahead on Phoebe Bridgers"), use sentence case, and give empty states a next step ("No race yet. It starts at 0 on the 1st, invite two friends"). Avoid hype words and exclamation marks.

---
*Unverified or secondary sources: the Wathan indigo story (press coverage only), the story safe-zone percentages (third-party guides), the Refactoring UI spacing-system quote (from memory of the book). The WCAG 2.2.2 page could not be fetched this session.*
