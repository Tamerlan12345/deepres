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

## 2024-06-27 - [MEDIUM] Missing Input Length Constraints (DoS Risk)
**Vulnerability:** The Pydantic models `UserLogin` and `ReportCreate` in `backend/app/api.py` were missing explicit `max_length` limits on string fields (`username`, `password`, `query`). This exposes the application to resource exhaustion or denial-of-service (DoS) attacks if a malicious user submits exceptionally large strings.
**Learning:** By default, Pydantic does not enforce strict limits on the size of string fields unless explicitly specified using `Field(..., max_length=N)`. Without limits, FastAPI will attempt to parse and load massive inputs into memory before any manual validation occurs, which can be easily exploited to crash or slow down the application.
**Prevention:** Always define explicit length constraints (e.g., `max_length=50`, `max_length=1000`) on all user-facing string inputs within Pydantic models or forms to prevent unbound memory allocation and mitigate resource exhaustion risks.
