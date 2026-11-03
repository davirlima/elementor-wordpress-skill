# SEO with Rank Math

## 0. Fast path (copy, run, done)
```
python3 scripts/wp.py rankmath <id> --title "<Topic> | <Brand>" --description "<140-160 chars, keyword early, benefit + CTA>" --keyword "<main kw>[, secondary]" --robots index
python3 scripts/plain_content.py <page-url> /tmp/c.html --write <id>     # only if Rank Math reads 0 words
```
Several pages: loop the same command; keep one title pattern; read the values back afterwards. Facts, thresholds, routes and which KB page to consult are in `references/rankmath-docs.md` (pinned to a plugin version): read the part you need before deciding. 404 on `updateMeta` = plugin inactive (`python3 scripts/doctor.py`); 403 = firewall (see the digest §2).

## 1. Per page
Set through `POST /rankmath/v1/updateMeta` (`objectType: "post"`):
- `rank_math_title` — **one pattern for every page**: `<Topic> | <Brand>` (home: `<Main keyword> - <City/UF> | <Brand>`). Don't vary the structure per page to chase points; don't add numbers unless they are meaningful to the reader.
- `rank_math_description` — 140–160 chars, keyword early, benefit + CTA.
- `rank_math_focus_keyword` — main keyword first, optional secondary after a comma.
- `rank_math_robots` — `["index"]` for real pages; consider noindex only for thin utility pages, and ask.
- `rank_math_facebook_title/description/image(_id)` and twitter equivalents — OG image 1200×630 uploaded by the user.
- Schema via `updateSchemas`: home `AutoRental`/`LocalBusiness` subtype with address and phone, About → `AboutPage`, service/franchise → `Service`. Setting `rank_math_rich_snippet` to "off" removes the whole JSON-LD — use custom schemas instead.

Rank Math setup wizard data (site type, business name, logo) can be read/written with `/rankmath/v1/setupWizard/getStepData|updateStepData` (step `yoursite`). Don't overwrite general settings blindly — you can't read them all back.

## 2. Make Rank Math see the content
Rank Math analyzes `post_content`, which is empty for pages built outside the Elementor editor. After publishing or editing content, regenerate it: `scripts/plain_content.py <url>` → write HTML to the page's `content` field. Then the user opens the page in the editor (or Rank Math → Status & Tools → update SEO scores, if available) to recompute the score — Claude cannot trigger the browser-side analysis.

## 3. Raising the score honestly
Do the changes that also help readers:
- Keyword in the H1, early in the first paragraph, in at least one H2/H3, in a few image alt texts (when true to the image), density ≈1%.
- More words only where it genuinely helps (Rank Math's length test gives full marks above 2,500 words and only 20% at 600-1000, so don't chase it; see the digest §3) by adding useful sections (FAQ answering real questions, "what we do", process steps) using only facts the site/user already state — no invented prices, numbers or promises.
- Internal links in body text (about, services, catalog anchors); one or two relevant external dofollow links (industry association, the law text on a privacy page, official social profile).
- Short paragraphs.

Usually leave alone (explain the trade-off instead): keyword-in-URL when it requires changing established slugs; TOC on short pages; images on legal pages; "Content AI" upsell; "number in title".

## 4. Site level
- Search Console verification meta tag → Custom Code in `elementor_head`.
- Sitemap: `/sitemap_index.xml` (Rank Math). Remove "Hello world!" and other junk so it doesn't appear.
- Privacy page set in Settings → Privacy (user action).
- Rank Math 404 title and other global titles may still be in English — mention it (Titles & Meta → Misc).
