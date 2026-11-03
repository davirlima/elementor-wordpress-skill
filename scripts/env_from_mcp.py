#!/usr/bin/env python3
"""Print `export WP_URL=... WP_USER=... WP_APP_PASSWORD=...` from the Elementor MCP server the user already configured.

Why: the MCP server's Authorization header IS the credential the user handed over for this site, so there is
no reason to stop and ask them to export variables again. The scripts need REST access because the Elementor
MCP cannot read or edit classic (V3) widgets such as buttons, icon lists and social icons.

Usage (the password is never printed to the terminal):
    eval "$(python3 env_from_mcp.py [site-substring])"

`--list` prints "<server-name> <mcp-url> <user>" for each configured Elementor MCP server (never the password); the
doctor and the SKILL.md MCP gate use it to check that a server for THIS site is configured.

With several Elementor MCP servers configured, pass the exact site host to pick one.
Looks in ~/.claude.json (user + per-project entries), ./.mcp.json and Codex's ~/.codex/config.toml
([mcp_servers.<name>] with http_headers / headers).
"""
import base64, json, os, sys
from urllib.parse import urlsplit

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
LIST = '--list' in sys.argv
NEEDLE = ARGS[0] if ARGS else ''


def servers():
    for path in (os.path.expanduser('~/.claude.json'), os.path.join(os.getcwd(), '.mcp.json')):
        try: data = json.load(open(path))
        except (OSError, json.JSONDecodeError): continue
        stack = [data]
        while stack:
            o = stack.pop()
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == 'mcpServers' and isinstance(v, dict):
                        for name, s in v.items():
                            if isinstance(s, dict): yield name, s
                    else: stack.append(v)
            elif isinstance(o, list): stack.extend(o)


def codex_servers():
    path = os.path.join(os.environ.get('CODEX_HOME', os.path.expanduser('~/.codex')), 'config.toml')
    try:
        import tomllib
        data = tomllib.load(open(path, 'rb'))
    except Exception: return
    for name, s in (data.get('mcp_servers') or {}).items():
        if isinstance(s, dict):
            hdr = s.get('http_headers') or s.get('headers') or {}
            yield name, {'url': s.get('url', ''), 'headers': hdr}


matches = []
for name, s in list(servers()) + list(codex_servers()):
    url = s.get('url', '')
    if '/wp-json/elementor/mcp' not in url: continue
    host = (urlsplit(url).hostname or '').lower()
    wanted = (urlsplit(NEEDLE if '://' in NEEDLE else '//' + NEEDLE).hostname or '').lower()
    if NEEDLE and host != wanted: continue
    auth = next((v for k, v in (s.get('headers') or {}).items() if k.lower() == 'authorization' and isinstance(v, str)), '')
    user, pwd = '', ''
    if auth.lower().startswith('basic '):
        try: user, pwd = base64.b64decode(auth.split(None, 1)[1]).decode().split(':', 1)
        except Exception: pass
    if LIST:
        print(name, url, user or '(credentials unavailable)')
    else:
        matches.append((name, url, user, pwd))

if LIST: sys.exit(0)
if len(matches) != 1:
    sys.stderr.write('Expected exactly one MCP server for the site; specify its exact host and resolve duplicate entries.\n')
    sys.exit(1)
name, url, user, pwd = matches[0]
if not user or not pwd:
    sys.stderr.write('MCP credentials are not available as a Basic header; configure REST credentials separately.\n')
    sys.exit(1)
site = url.split('/wp-json/')[0]
q = lambda x: "'" + x.replace("'", "'\\''") + "'"
print(f'export WP_URL={q(site)} WP_USER={q(user)} WP_APP_PASSWORD={q(pwd)}')
sys.stderr.write(f'credentials taken from MCP server "{name}" ({site}), user {user}\n')
