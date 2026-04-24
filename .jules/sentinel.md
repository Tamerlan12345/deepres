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

## 2025-04-24 - [Path Traversal] Insecure Path Boundary Check using startswith
**Vulnerability:** The SPA catch-all route handler (`serve_spa`) used `safe_path.startswith(frontend_dist)` to validate that the requested file resides within the intended `frontend/dist` directory. This approach is vulnerable because it performs a string prefix match without enforcing a directory boundary (i.e. a trailing slash). As a result, an attacker could request a path like `../dist-secrets/secret.txt`, which resolves to `/app/frontend/dist-secrets/secret.txt`. Since this path string starts with `/app/frontend/dist`, the validation check incorrectly passes, allowing unauthorized access to files outside the intended directory.
**Learning:** Using `startswith()` for path validation is dangerous if trailing slashes are not enforced, because it allows partial matches on directory names.
**Prevention:** Always use `os.path.commonpath` with absolute paths to verify that a resolved path is strictly contained within the intended base directory. Additionally, wrap the check in a `try-except ValueError` block to handle edge cases where paths reside on different drives (e.g. on Windows), falling back to a safe default.
