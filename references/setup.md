# Setup (connect a site) and offboarding (disconnect it)

## Contents
1. Is the site already connected?
2. Enabling the MCP in WordPress (the user does this)
3. When the user pastes the connection prompt
4. If the MCP is missing: force the connection
5. Offboarding at the end of a project

## 1. Is the site already connected?
- Elementor MCP tools exist in your tool list (`mcp__<server>__elementor-*`), or `claude mcp list` / `/mcp` shows the server as connected.
- `python3 scripts/env_from_mcp.py --list` shows the configured servers; `python3 scripts/doctor.py` checks that one belongs to this site and that its endpoint answers (401 without auth is normal). The endpoint URL comes from the generated prompt; do not guess it.
  - No server for this host, or the endpoint answers 404 → not connected or MCP turned off: step 2. Check Elementor's version first (4.3.0+).
- If `WP_URL/WP_USER/WP_APP_PASSWORD` are set or `scripts/env_from_mcp.py` works, the REST scripts already have access.

## 2. Enabling the MCP in WordPress (the user does this)
1. wp-admin → **Elementor → Elementor MCP** → turn it on.
2. Prefer a **dedicated administrator** for the integration (the application password inherits that user's permissions, and a separate user can be revoked without touching the person's own login).
3. On that same screen, use the option to **generate the connection prompt**. It contains the server URL, the username, an **application password**, the suggested server name and the exact `mcpServers` JSON for `~/.claude.json` (Windows: `%USERPROFILE%\.claude.json`).
4. Security plugins: Wordfence must not block application passwords for that user (Login Security → "Disable WordPress application passwords" off); 2FA on that user blocks REST/MCP logins.
5. The user pastes the generated prompt into Claude Code.

## 3. When the user pastes the connection prompt
The prompt is the user's own instruction to configure their client — do it, with care:

1. **Use the supported CLI** instead of hand-editing the config. It produces the same `mcpServers` entry and Claude Code owns that file:
   ```
   claude mcp add --transport http --scope user <server-name-from-prompt> <url-from-prompt> --header "Authorization: Basic <base64-from-prompt>"
   ```
   If auto mode refuses to run it, ask the user to run the same command with the `!` prefix. Edit `~/.claude.json` by hand only if the CLI is unavailable: keep a copy, keep the JSON valid, touch only `mcpServers`.
2. **Never repeat the password** in your replies and never write it to a file, memory, commit message, repo or the skill. It has now entered the history and the transcript — that is what offboarding cleans up.
3. Ask the user to run `/mcp` (or restart Claude Code) so the server connects, then verify: `elementor-list-posts` (MCP) and `scripts/wp.py whoami` (REST, after `eval "$(python3 scripts/env_from_mcp.py <exact-site-host>)"`).
4. If the server is rejected ("rejected the Authorization header") → `references/connection.md` §6 (Wordfence, revoked password).

### Codex (and other agents)
Codex has no `claude mcp add`; the same entry goes in `~/.codex/config.toml`:
```
[mcp_servers.<server-name>]
url = "https://<site>/wp-json/elementor/mcp/"
http_headers = { Authorization = "Basic <base64-from-prompt>" }
```
Restart Codex afterwards. `scripts/env_from_mcp.py` reads this file too. Codex's default sandbox blocks the network: if requests fail, see `python3 scripts/doctor.py` (it prints the `network_access` setting / escalation to use). Claude Desktop and Cursor: paste the JSON the generated prompt gives for that client.

## 4. If the MCP is missing: force the connection
The MCP is mandatory (SKILL.md, MCP gate). Do not continue with REST alone and do not offer "do it in the editor and I'll check". Say precisely what is needed and where to get it:
- wp-admin -> **Elementor -> Elementor MCP** -> **Enable MCP access** -> client tab (Claude Code / Codex / Claude Desktop / Cursor / Other) -> acknowledgment checkbox -> **Generate Prompt** -> **Copy prompt** -> paste it in the chat. (Docs digest: `references/elementor-mcp-docs.md` §2.)
- Menu missing -> Elementor or Elementor Pro older than 4.3.0, or WordPress older than 6.8: update after a backup, with the user's OK.
- Generate Prompt creates an application password automatically; the user does not need to make one by hand. Wordfence/2FA blockers: `connection.md` §6.
- The MCP server does not show up after configuring: restart the agent (Claude Code: `/mcp`), and check `python3 scripts/env_from_mcp.py --list` and `python3 scripts/doctor.py`.
What the MCP does not do (classic widgets, media, Rank Math, bulk edits) is done over REST with `WP_*` (loaded by `env_from_mcp.py`); that complements the MCP, it never replaces it. The Elementor save trigger (`elementor-update-page-settings`) only exists through the MCP, which is one more reason it is required.

## 5. Offboarding at the end of a project
Do this only when the user requests or authorizes offboarding. Finishing work alone does not authorize removing a shared connection or credentials.

1. **Remove the server:** `claude mcp remove <name> -s user` (Codex: delete the `[mcp_servers.<name>]` block from `~/.codex/config.toml`) (check `-s local` / `-s project` too with `claude mcp list`).
2. **Revoke the credential in WordPress** — the only step that really invalidates it: Users → Profile → Application Passwords → Revoke (or revoke all for the dedicated user). Via REST, with that same credential: `GET /wp/v2/users/me/application-passwords/introspect` returns the uuid of the credential in use; `DELETE /wp/v2/users/me/application-passwords/<uuid>` removes it. Only do this when the user asks or confirms: it ends your own access.
3. **Turn the MCP off** in Elementor → Elementor MCP if the site no longer needs it.
4. **Scrub the local traces** with `scripts/scrub_credentials.py`: first a dry run, then `--apply`. It finds the secrets by pattern (Basic headers, "Application password: …", `WP_APP_PASSWORD=…`) and replaces them with `[REMOVIDO]` in `~/.claude.json` backups, the prompt history, shell history and transcripts, never printing them. Files modified in the last minutes (the live session transcript, the history of the running prompt) are skipped; once Claude Code is closed, run it again with `--skip-recent 0`. Auto mode may refuse to edit history/transcripts — then the user runs the command themselves with the `!` prefix.
5. Check that no memory file, script, repo or backup folder holds a secret (site data backups are not credentials; delete them only if the user wants).

Say plainly at the end: local cleanup does not invalidate a credential that was already exposed in a chat or transcript; revoking it in WordPress does.
