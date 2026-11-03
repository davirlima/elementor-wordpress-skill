# Rank Math: documentation digest (pinned) and where to re-check

**Verified on 2026-11-03 against Rank Math SEO (free) 1.0.281** (wordpress.org plugin page: tested up to WP 7.1.4, PHP 7.4+). Sources are Rank Math's own Knowledge Base, listed per section. Docs and behavior drift: before relying on a threshold in a deliverable, check that the plugin version on the site (`GET /wp/v2/plugins`, slug `seo-by-rank-math/rank-math`) is not much newer than this, and re-open the linked page when it is. If you find a difference, update this file (date and version included) instead of working around it silently.

## 1. What to read, and what to look for
| Need | Read | Look for |
|---|---|---|
| Which tests exist and their thresholds | https://rankmath.com/kb/score-100-in-tests/ | the four tables (Basic, Additional, Title Readability, Content Readability); thresholds in §3 below |
| Meta not saving / HTTP 403 on writes | https://rankmath.com/kb/meta-data-not-saving/ | list of REST routes to whitelist, Wordfence/Cloudflare steps |
| Score shows N/A or is stale | https://rankmath.com/kb/seo-score-not-available/ | Status & Tools -> Database Tools -> *Update SEO Scores* |
| Headless / REST-only pages | https://rankmath.com/kb/headless-cms-support/ | `getHead` route |
| SEO score vs Content AI score | https://rankmath.com/kb/seo-score-vs-content-ai-score/ | Content AI is a separate, paid-credit feature |
| Schema problems | https://rankmath.com/kb/fix-schema-issues/ | types and validation |

## 2. REST routes (the ones this skill uses)
Namespace `rankmath/v1`. The plugin itself uses these from the editor: `updateMeta`, `updateSchemas`, `updateRedirection`, `getFeaturedImageId`, `getHead` (the last only for headless). **They are the plugin's internal routes, not a documented public API**: Rank Math support has told users there is no dedicated API for setting titles/descriptions and points to the post meta keys `rank_math_*` (stored in `wp_postmeta`). Consequences:
- The payload used here (`{"objectType":"post","objectID":<id>,"meta":{"rank_math_title":...}}`) is what the editor sends and works in practice, but is not a contract. After every write, read the value back (the front-end `<title>` / meta description, or the page source) to confirm it stuck.
- Route 404 -> plugin inactive. 403 with the user authenticated -> firewall rule: whitelist the routes above (Wordfence learning mode / Cloudflare rule) or ask the host. Source: meta-data-not-saving.
- Keys set by this skill: `rank_math_title`, `rank_math_description`, `rank_math_focus_keyword`, `rank_math_robots`, `rank_math_facebook_*`, `rank_math_twitter_*`.

## 3. Score tests and thresholds (from score-100-in-tests)
The SEO score is a pass/fail tally of tests out of 100, computed **in the browser when the post is opened**; N/A appears without a focus keyword or when the post is noindex.

Basic: keyword in SEO title (keep within the first 50 chars); in meta description (first 120-160 chars; without one Rank Math tests a generated description); in the URL (not tested for plain/numeric permalinks); in the first 10% of the content; in the content. **Content length: full marks above 2,500 words**; tiers 2000-2500=70%, 1500-2000=60%, 1000-1500=40%, 600-1000=20%, under 600=0%.
Additional: keyword in a subheading (H2/H3...); in an image alt; density 1-1.5% (warning above 2.5%); full URL (with domain) <= 75 chars; external links (and at least one dofollow); internal links; focus keyword not reused on another post.
Title readability: keyword in the first half of the title; a sentiment word; a power word; a number.
Content readability: table of contents; no paragraph over 120 words; media (1+ image/video, 4+ for full marks).

How the skill uses this: the tests that are cheap and also help readers are done (keyword placement, short paragraphs, real internal/external links, alt text); length, TOC, "number/power/sentiment in title" and rewriting slugs are trade-offs to explain, not to chase (`references/seo-rankmath.md` §3). Do not promise 100: >2,500 words is rarely right for an institutional page.

## 4. Elementor specifics
- Rank Math analyzes `post_content`. Pages built over REST have it empty, hence "0 words" -> `scripts/plain_content.py`. The KB says scores can differ on page builders because they render shortcodes, and to trust the score shown inside the builder; it says nothing else about Elementor detection, so this behavior comes from our own experience, not the docs.
- Recomputing scores: open the post once in the editor, or Status & Tools -> Database Tools -> **Update SEO Scores** (needs Advanced Mode; rescored posts must have a focus keyword). The KB advises not clicking Update with no changes just to refresh a date. Whether the bulk tool handles builder content is not documented: check one page after running it.
- Free vs PRO: Content AI, product schema and review tests are PRO/Content AI features; ignore them on free installs.

## 5. Procedure that follows from this
1. Read only the row of §1 that matches the task (usually none: §2-§4 already hold the facts). Check plugin version against the pin at the top.
2. Write with `scripts/wp.py rankmath ...`; read it back.
3. Regenerate `post_content` if the analyzer sees nothing; have the user open the page or run Update SEO Scores.
4. Report the real score only if the user read it from the editor; never invent one.
