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
## 2025-02-28 - [CRITICAL] Fixed Path Traversal Bypass via `startswith` in SPA serving
**Vulnerability:** The SPA file serving endpoint (`serve_spa` in `backend/app/main.py`) attempted to prevent path traversal by validating that the requested path string started with the frontend distribution directory path string (`safe_path.startswith(frontend_dist)`). This is vulnerable to a bypass if an attacker requests a directory that shares the same prefix (e.g., if `frontend_dist` is `/app/frontend/dist`, an attacker could request `/app/frontend/dist-secret/file.txt` via `../dist-secret/file.txt`).
**Learning:** String prefix checks (`startswith`) are insecure for validating file paths because they don't respect directory boundaries. They only verify that one string begins with another.
**Prevention:** Always use `os.path.commonpath([base_path, target_path]) == base_path` on absolute paths (`os.path.abspath`) to ensure the resolved path strictly resides within the intended directory boundaries. Additionally, catch `ValueError` to handle cases where paths reside on different drives (e.g., in Windows environments).
