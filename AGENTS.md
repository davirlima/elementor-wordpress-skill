# Elementor + WordPress skill (agent entry point)

This repository is an agent skill that works in Claude Code, Codex and any agent that reads `SKILL.md`.
When the task involves an Elementor / WordPress site, Rank Math, Theme Builder or the Elementor Kit, read `SKILL.md` and follow it.

Short version for agents that only load this file:
1. **MCP gate (mandatory):** the Elementor MCP of the site in question must be configured and live before any work. Check with `python3 scripts/env_from_mcp.py --list` and `python3 scripts/doctor.py`. If missing, make the user connect it: wp-admin -> Elementor -> Elementor MCP -> Enable -> pick the client -> Generate Prompt -> paste it to you (Elementor and Elementor Pro 4.3.0+, WordPress 6.8+). Details in `SKILL.md`.
2. Probe access before claiming it is blocked: a sandbox that blocks the network is a permission to request, not a dead end (`doctor.py` says how).
3. Read the pinned documentation digests before acting: `references/elementor-mcp-docs.md`, `references/wordpress-rest-docs.md`, `references/rankmath-docs.md`; each says where to re-check.
4. Use the MCP for Elementor-native work and `scripts/wp.py` (WordPress REST, curl-based) for what the MCP does not reach; Rank Math: `scripts/wp.py rankmath <id> --title --description --keyword`, then read it back.
5. Back up before writing, prefer reversible actions, verify on the live site, never write credentials into files.
