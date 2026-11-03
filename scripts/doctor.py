#!/usr/bin/env python3
"""Connectivity preflight: tells you EXACTLY why the WordPress API is (not) reachable, in one run.

Run this before claiming "I can't reach the site". Most "no access" reports are not real limits:
the variables were not exported, the sandbox blocked the network (a permission to request, not a dead end),
or the site answered with an error that has a known fix.

Usage:
    eval "$(python3 scripts/env_from_mcp.py)"   # optional: load WP_* from the MCP config
    python3 scripts/doctor.py [site-url]

Checks: credentials -> DNS/TLS/HTTP to /wp-json/ -> authenticated /users/me -> Elementor/WP versions (MCP needs
Elementor 4.3.0+) -> Elementor MCP server CONFIGURED FOR THIS SITE in the agent (mandatory) -> Rank Math route.
Exit code 0 = REST works AND the MCP is configured for this site; 4 = MCP missing (follow SKILL.md MCP gate).
"""
import base64, json, os, subprocess, sys

CURL_HINT = {
    6: 'DNS lookup failed. In a sandboxed agent this almost always means NETWORK IS BLOCKED, not that the site is down.',
    7: 'Connection refused / blocked. Sandbox network policy or firewall.',
    28: 'Timed out. Sandbox network policy, VPN or slow host; retry once before concluding.',
    35: 'TLS handshake failed (proxy/sandbox interception or old TLS on the host).',
    60: 'TLS certificate not trusted by this machine (sandbox CA store). Do NOT disable verification silently; tell the user.',
}
SANDBOX_FIX = """How to unblock a sandbox (these are settings, not walls):
  - Codex CLI/app: ask for approval to run the command outside the sandbox (escalate), or enable network for the
    workspace-write sandbox: in ~/.codex/config.toml  ->  [sandbox_workspace_write]  network_access = true
    (or run with --sandbox danger-full-access only if the user agrees).
  - Claude Code: approve the command when prompted, allow the domain in the sandbox network settings, or have the
    user run it with the `!` prefix.
  - Any other agent: request network permission for this host; if refused, the user can run `python3 scripts/doctor.py`
    and paste the output."""


def mcp_check(site):
    """The MCP must be configured in the agent for THIS site (host match); the endpoint comes from that config, never guessed."""
    here = os.path.dirname(os.path.abspath(__file__))
    out = subprocess.run([sys.executable, os.path.join(here, 'env_from_mcp.py'), '--list'], capture_output=True, text=True).stdout
    host = site.split('//')[-1].split('/')[0].lower()
    rows = [l.split() for l in out.splitlines() if l.strip()]
    mine = [r for r in rows if len(r) >= 2 and host == r[1].split('//')[-1].split('/')[0].lower()]
    if not mine:
        other = ', '.join(sorted({r[1].split('//')[-1].split('/')[0] for r in rows})) or 'none'
        say(False, f'Elementor MCP: no server configured for {host} (configured: {other}). Mandatory: connect it (SKILL.md MCP gate).')
        return False
    name, murl = mine[0][0], mine[0][1]
    code = subprocess.run(['curl', '-s', '-m', '25', '-o', '/dev/null', '-w', '%{http_code}', murl], capture_output=True, text=True).stdout
    ok = code in ('401', '200', '400', '405')
    say(ok, f'Elementor MCP server "{name}" configured for {host}; endpoint answers HTTP {code}'
        + (' (401 = wants auth, normal)' if code == '401' else '' if ok else ' (endpoint off/removed: re-generate the prompt in Elementor -> Elementor MCP)'))
    if ok: say(True, 'in the agent: restart / run /mcp so its tools load, then call a read tool (e.g. list pages) to prove the live connection')
    return ok


def say(ok, msg): print(('[ok]   ' if ok else '[FAIL] ') + msg)


def main():
    url = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get('WP_URL', '')).rstrip('/')
    user, pwd = os.environ.get('WP_USER'), os.environ.get('WP_APP_PASSWORD')
    if not url:
        say(False, 'WP_URL not set. Run: eval "$(python3 scripts/env_from_mcp.py)"  (reads the MCP config of Claude Code/Codex), '
                   'or pass the site URL as an argument.'); return 1
    have_auth = bool(user and pwd)
    say(have_auth, 'credentials in env (WP_USER / WP_APP_PASSWORD)' if have_auth else
        'WP_USER / WP_APP_PASSWORD missing: run env_from_mcp.py; if it finds nothing, ask the user ONCE (references/setup.md). '
        'Public checks below still run.')

    r = subprocess.run(['curl', '-sS', '-m', '25', '-o', '/dev/null', '-w', '%{http_code}', f'{url}/wp-json/'],
                       capture_output=True, text=True)
    if r.returncode:
        say(False, f'cannot reach {url} (curl exit {r.returncode}): {r.stderr.strip()}')
        print('       ' + CURL_HINT.get(r.returncode, 'Transport error before any HTTP answer.'))
        print(SANDBOX_FIX); return 2
    say(r.stdout.startswith(('2', '3')), f'GET /wp-json/ -> HTTP {r.stdout}'
        + ('' if r.stdout.startswith(('2', '3')) else ' (REST disabled/blocked by a security plugin or host rule, or wrong URL)'))

    if not have_auth:
        mcp_check(url)
        return 1

    tok = base64.b64encode(f'{user}:{pwd}'.encode()).decode()
    h = f'Authorization: Basic {tok}'
    r = subprocess.run(['curl', '-s', '-m', '25', '-H', h, f'{url}/wp-json/wp/v2/users/me?context=edit&_fields=id,name,roles'],
                       capture_output=True, text=True)
    try: me = json.loads(r.stdout)
    except json.JSONDecodeError: me = {}
    if me.get('id'):
        say(True, f"authenticated as {me.get('name')} (roles: {', '.join(me.get('roles', []))})")
    else:
        say(False, f"auth rejected: {r.stdout[:160]}\n       Causes in order: Wordfence 'disable application passwords' / 2FA on the user, "
                   'password revoked, host stripping Authorization. See references/connection.md §6.')
        return 3
    vers = subprocess.run(['curl', '-s', '-m', '25', '-H', h, f'{url}/wp-json/wp/v2/plugins?per_page=100&_fields=plugin,version,status'],
                          capture_output=True, text=True).stdout
    try: plugins = {x['plugin'].split('/')[0]: x for x in json.loads(vers)}
    except Exception: plugins = {}
    versions_ok = True
    for slug, label, minimum in (('elementor', 'Elementor', (4, 3, 0)), ('elementor-pro', 'Elementor Pro', (4, 3, 0))):
        pl = plugins.get(slug)
        if not pl:
            say(False, f'{label}: not found / plugins list not readable')
            versions_ok = False
            continue
        v = tuple(int(x) for x in (pl['version'].split('-')[0].split('.') + ['0', '0'])[:3] if x.isdigit())
        ok = pl['status'] == 'active' and v >= minimum
        versions_ok = versions_ok and ok
        say(ok, f"{label} {pl['version']} ({pl['status']})" + ('' if ok else f" -> the Elementor MCP needs {'.'.join(map(str, minimum))}+ and the plugin active: update (backup first, ask the user)"))
    mcp_ok = mcp_check(url)
    r = subprocess.run(['curl', '-s', '-m', '25', '-o', '/dev/null', '-w', '%{http_code}', '-H', h, f'{url}/wp-json/rankmath/v1/'],
                       capture_output=True, text=True).stdout
    say(r == '200', f'Rank Math REST namespace -> HTTP {r} ' + ('' if r == '200' else '(plugin inactive or route blocked)'))
    if not versions_ok:
        print('Plugin requirements could not be verified; check versions and activation before proceeding.')
        return 5
    if not mcp_ok:
        print('\nREST works but the Elementor MCP is NOT connected for this site. It is mandatory: follow the MCP gate in SKILL.md '
              '(references/elementor-mcp-docs.md §2) and do not start the work until it passes.'); return 4
    print('\nREST + MCP ready. Do the job with scripts/wp.py and the MCP; do not hand it back to the user.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
