# Elementor MCP: documentation digest (pinned) and where to re-check

**Verified on 2026-11-03.** Sources: Elementor Help Center, "How to Connect Elementor to an AI Tool Using MCP" (last update 2026-09-18) and "How to Build and Edit Your Site Using Elementor MCP" (last update 2026-09-30); Elementor blog "MCP for WordPress" and the Webgate agency case study. The MCP shipped with Elementor **4.3.0** (changelog 2026-09-22); earlier beta posts mention enabling a beta-tester feature first, which no longer applies on 4.3+. The Help Center articles are dated: when their "Last Update" is newer than the dates above, or the site runs a newer Elementor, re-read them and update this file.

Re-check list:
| Need | Open | Look for |
|---|---|---|
| Connect / disconnect / requirements | https://elementor.com/help/how-to-connect-elementor-to-an-ai-tool-using-mcp/ | requirements, client tabs, revoke steps |
| What the MCP can build | https://elementor.com/help/how-to-build-and-edit-your-site-using-elementor-mcp/ | capability list, concurrency (Force Save/Reload) |
| Real agency workflow with Codex/Claude | https://elementor.com/blog/mcp-webgate-case-study/ | MCP = hands, browser = eyes; drafts, human review |
| Which MCP/plugin is which | https://elementor.com/blog/mcp-for-wordpress-what-each-option-is-and-what-to-install/ | Elementor MCP vs Angie vs generic WP MCP |
| Live tool list for THIS site | the agent's own MCP tool list + each tool's description/schema | tool names and arguments, which can differ by Elementor version |

The Help Center pages are large and wrapped in site navigation; fetch the HTML with `curl` and strip tags if a fetch tool returns only the menu.

## 1. Requirements (from the docs)
- WordPress **6.8+** (Tools -> Site Health -> Info).
- **Elementor Core 4.3.0+**; **Elementor Pro 4.3.0+** for the advanced tools (forms, popups, loops, ecommerce widgets, components, dynamic content, headers/footers). **Angie** (free plugin) adds custom widgets/apps, wp-admin customization, bulk content actions, other plugins through the WordPress Abilities API.
- The connection runs on a WordPress **Application Password**; the AI inherits **exactly the permissions of that user's role**. Application passwords need HTTPS (see `wordpress-rest-docs.md` §1).
- If the site has an older Elementor, the MCP is not there: updating Elementor (back up first, ask the user) is the way forward, not a workaround.

## 2. Connecting (what the user does, where the data comes from)
1. wp-admin -> **Elementor -> Elementor MCP** (also under Elementor -> Editor -> Elementor MCP).
2. Click **Enable MCP access**.
3. Pick the client tab: **Claude Code, Claude Desktop, Codex, Cursor** or **Other**.
4. Tick the acknowledgment ("clicking Generate Prompt will create an application password for this site").
5. **Generate Prompt**, then **Copy prompt**; paste it into the agent. The prompt carries the **server URL, the user, the application password and the exact configuration for that client**: it is the only source of truth for the endpoint. Do not guess the URL.
6. Restart the agent / reload MCP servers, then verify with a real MCP call (see SKILL.md, MCP gate).

Per-client details the prompt generates: Claude Code -> `claude mcp add ...`; Codex -> an entry in `~/.codex/config.toml`; Claude Desktop/Cursor -> their JSON MCP config; Other -> generic HTTP MCP settings.

## 3. What the MCP does (from the docs)
Works through **WordPress AI Abilities**. It can: create/read pages (title, slug, template); build **V4 Atomic** layouts (flexbox/grid containers, text, accordions, background video, loop grids); manage global classes, variables (colors, fonts, spacing) and default HTML-tag styles; build Theme Builder headers, footers, single, archive, 404 and popups with display conditions; bind dynamic data; create/reuse Components; read the DOM tree; save drafts or **publish**; detect concurrent edits (the human sees Force Save / Reload).

Tips from the docs and case study: ask in stages (outline, content, styling/responsive); the MCP saves drafts, review before publishing; do not hand an agent unrestricted production redesigns; keep humans on IA, accessibility, performance and publishing; use the browser for visual QA.

## 4. What the docs do NOT say (our field experience, separate from the docs)
- Classic (V3) widgets (button, icon list, social icons, text editor, heading) often come back empty through the MCP; `_elementor_data` is read/written over REST (`scripts/wp.py`) and the MCP is used for the save trigger `elementor-update-page-settings`, previews and Atomic/Theme Builder/design-system work. Re-test on each site: if the MCP now handles a widget, prefer the MCP.
- Popups and Kits: the save trigger replaces settings, send the full object (`gotchas.md`).
- Tool names seen: `elementor-list-posts`, `elementor-get-page-structure`, `elementor-update-page-settings`, `elementor-create-preview-link`, `build-composition`, `manage-elements`, `get-widget-schema`. Treat the live tool list as authoritative.

## 5. Disconnect (from the docs)
Per client: Users -> Profile -> Application Passwords -> **Revoke** the entry (named like "Elementor MCP - Claude Code"). Site-wide: Elementor -> Elementor MCP -> **Turn off MCP access** (red button, confirm): blocks every connected agent immediately.
