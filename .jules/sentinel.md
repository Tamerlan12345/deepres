## 2026-02-22 - Hidden IDOR in Unused Endpoint
**Vulnerability:** IDOR in `/reports/{report_id}/pdf` endpoint allowed unauthenticated access to any report PDF.
**Learning:** The endpoint was not used by the frontend (which uses `window.print()`), making it a 'shadow API' that was easily overlooked during security reviews.
**Prevention:** Regularly audit all exposed API endpoints, even those not actively used by the frontend. Use automated tools to enumerate and test all defined routes.

## 2026-02-23 - Stored XSS in PDF Generation
**Vulnerability:** User input (query, summary, analysis) was directly injected into HTML during PDF generation without escaping, allowing for Stored XSS / HTML Injection.
**Learning:** PDF generation from HTML strings requires careful handling of user input, just like web pages. Always escape user input before embedding in HTML templates.
**Prevention:** Used `html.escape()` to sanitize inputs. Future improvements could use a templating engine like Jinja2 with auto-escaping.

## 2026-02-23 - Information Leakage via Database Errors
**Vulnerability:** The `/reports` endpoint exposed raw database error messages (`str(e)`) to the client, potentially revealing internal schema details and implementation specifics.
**Learning:** Default exception handlers in some frameworks (or manual overrides like here) can accidentally prioritize debugging convenience over security by returning stack traces or raw errors.
**Prevention:** Always catch exceptions in API endpoints and return generic error messages to the client (e.g., "Internal Server Error"), while logging the full details server-side.

## 2026-02-24 - Hardcoded Admin Credentials in Startup Logic
**Vulnerability:** The application automatically created a default admin user with hardcoded credentials (`admin:admin`) during startup if it didn't exist.
**Learning:** Seeding logic in `on_event("startup")` can be a hidden source of critical vulnerabilities if it uses insecure defaults that persist into production.
**Prevention:** Ensure all seeding logic uses environment variables for sensitive data or generates secure random values if not provided. Log warnings for generated credentials.
## 2024-04-06 - Path Traversal via Prefix Matching Flaw

**Vulnerability:** A critical path traversal vulnerability was present in the static file serving route (`/{full_path:path}`). The implementation used `safe_path.startswith(frontend_dist)` to verify that the requested file remained within the frontend distribution directory. This string prefix check is inherently insecure: for a base directory `/app/frontend/dist`, an attacker requesting `../dist_secrets/keys.txt` yields the normalized path `/app/frontend/dist_secrets/keys.txt`, which starts with `/app/frontend/dist`, successfully bypassing the check and exposing arbitrary files matching the prefix.
**Learning:** Checking directory boundaries using basic string `startswith` operations is insufficient and vulnerable if a directory on the same level begins with the target directory's name. It effectively conflates a file path prefix with a strict directory containment structure.
**Prevention:** Always validate path boundaries using `os.path.commonpath([base_path, target_path]) == base_path`. This safely and explicitly verifies that the common directory ancestor between the paths is exactly the intended base directory. Furthermore, always utilize `os.path.abspath` before the comparison to ensure paths are fully resolved and absolute, and catch `ValueError` during `commonpath` execution to gracefully handle paths originating from different drives.
