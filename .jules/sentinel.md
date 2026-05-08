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

## 2026-02-25 - Path Traversal in Catch-all SPA Route
**Vulnerability:** A path traversal vulnerability existed in the SPA static file serving route (`/{full_path:path}`). The backend used `startswith` to validate that paths were within the allowed directory. By using `../` segments, an attacker could request files outside the `frontend/dist` directory because `os.path.normpath` resolved the directory traversal without preventing the `startswith` condition if the prefix matched.
**Learning:** `startswith` string matching is insufficient for path boundary validation. `os.path.normpath` removes `../` but string-based validation doesn't reliably check if the final resolved absolute path is actually within the target directory. Additionally, testing this via `TestClient` can mask the vulnerability due to automatic client-side path normalization.
**Prevention:** Replaced `startswith` with `os.path.commonpath` on absolute paths to securely ensure that the requested path boundary remains strictly within the intended target directory. Bypassed `TestClient` path normalization during testing by extracting and executing the route endpoint directly.
