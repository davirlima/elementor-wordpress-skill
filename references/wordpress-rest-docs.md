# WordPress REST API: documentation digest (pinned) and where to re-check

**Verified on 2026-11-03** (WordPress plugin directory shows current WP at 7.1.x). Sources: developer.wordpress.org REST API Handbook and Reference, and the Make/Core "Application Passwords: Integration Guide". Core behavior is stable, but the handbook pages are thin in places; the notes marked *(core, not on the page)* come from WordPress core code and field experience. When the site runs a WordPress major newer than this, skim the pages below.

| Need | Open | Look for |
|---|---|---|
| Auth (app passwords, cookies/nonce) | https://developer.wordpress.org/rest-api/using-the-rest-api/authentication/ | HTTPS requirement, nonce rules |
| App password availability / filters | https://make.wordpress.org/core/2020/11/05/application-passwords-integration-guide/ | `wp_is_application_passwords_available*` filters, discovery |
| Global parameters | https://developer.wordpress.org/rest-api/using-the-rest-api/global-parameters/ | `_fields`, `_embed`, `_method` |
| Pagination | https://developer.wordpress.org/rest-api/using-the-rest-api/pagination/ | `per_page` cap, `X-WP-Total*` headers |
| Pages / Posts | https://developer.wordpress.org/rest-api/reference/pages/ | create/update args, `force` on delete |
| Media | https://developer.wordpress.org/rest-api/reference/media/ | `alt_text`, `title`, delete |
| Plugins / Settings / Users | https://developer.wordpress.org/rest-api/reference/ | list the resource in the sidebar |

## 1. Authentication
- **Application Passwords** (WP 5.6+): `Authorization: Basic base64("user:password")`, spaces in the password are optional. **HTTPS only** by default; without SSL the feature is off unless forced on.
- Availability can be turned off site-wide (`wp_is_application_passwords_available` returns false) or per user (`..._for_user`), which is what security plugins do. Discovery: the `authentication` key of `GET /wp-json/` is empty when unavailable, and holds `application-passwords` when on.
- **Do not send session cookies together with the Basic header**: cookie auth runs first and, without a nonce, the request becomes user 0 (`rest_forbidden`). curl without a cookie jar is fine.
- Cookie auth needs the `wp_rest` nonce (`X-WP-Nonce` header or `_wpnonce`); only for code running inside a logged-in WordPress session.
- `POST /wp/v2/users/me/application-passwords` creates one. *(core, not on the page)* `GET /wp/v2/users/me/application-passwords/introspect` returns the credential in use and `DELETE /wp/v2/users/me/application-passwords/<uuid>` revokes it (used by offboarding).

## 2. Requests and responses
- Resources: `GET /wp/v2/pages|posts|media|users|plugins|settings`; Elementor/Rank Math add their own namespaces.
- `context`: `view` (default), `embed`, `edit`. Fields like raw title/content, `meta`, `password` only appear with `context=edit` and an authorized user.
- Collections: `per_page` **max 100**, `page`, `offset`; totals in headers `X-WP-Total` and `X-WP-TotalPages`. Loop until a page returns empty/error (`rest_post_invalid_page_number` *(core)*) or use the headers.
- `_fields=id,title,meta` trims payloads (nested meta supported, WP 5.3+). `_embed` inlines linked resources. `?_method=DELETE` on a POST (or `X-HTTP-Method-Override`) for clients that cannot send DELETE.
- Create/update: `POST /wp/v2/pages[/<id>]` with `title, content, slug, status (publish|future|draft|pending|private), parent, template, meta, featured_media, menu_order...`. Update also by POST.
- `DELETE` moves to the trash; `?force=true` bypasses it. **Media has no trash**: deletion of an attachment is permanent *(core, matches the skill's rule)*; the Reference lists `force` but does not spell this out.
- Media upload `POST /wp/v2/media`: the Reference page does not document the upload transport. In practice send **multipart** (`-F file=@x.webp -F alt_text=... -F title=...`), which is what `scripts/wp.py upload` does and what ModSecurity accepts; raw binary with `Content-Disposition` can be rejected (HTTP 406).
- Settings (`/wp/v2/settings`) only exposes registered options (`page_on_front`, `show_on_front`, `site_logo`, `site_icon`...). The active Elementor Kit is not one of them.

## 3. Reading failures
| Response | Meaning | Do |
|---|---|---|
| 401 `rest_not_logged_in` / `incorrect_password` | credential missing/revoked, or app passwords disabled, or cookies sent | `connection.md` §6 |
| 403 `rest_forbidden` / `rest_cannot_*` | authenticated but the user's role lacks the capability, or a firewall | use an administrator integration user; firewall rule |
| 404 `rest_no_route` | plugin inactive or route absent (e.g. Rank Math) | `doctor.py` |
| 406 / HTML error page | ModSecurity/host rule | use curl, multipart; `gotchas.md` |
| 200 with HTML | wrong URL, redirect to login, or pretty permalinks off: try `?rest_route=/wp/v2/...` *(core)* | check `WP_URL` and https |

## 4. Procedure
1. Before the first write on a site, `python3 scripts/doctor.py` (REST + auth + versions).
2. Prefer `scripts/wp.py` (curl-based, `context=edit`, backups) to ad-hoc requests; for anything new, read the Reference page of that resource first (table above) and test with a read before writing.
3. After a write, read it back.
