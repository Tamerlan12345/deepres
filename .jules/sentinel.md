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

## 2026-02-24 - Async Event Loop Blocking via Synchronous File I/O
**Vulnerability:** The catch-all SPA endpoint (`/{full_path:path}`) was using synchronous file system functions (`os.path.exists`, `os.path.isfile`) directly within an `async def` FastAPI route. This blocked the asyncio event loop for all requests.
**Learning:** In asynchronous frameworks like FastAPI, any synchronous, blocking operation (like file I/O or CPU-bound tasks) can severely degrade performance and potentially cause DoS if attacked with slow operations.
**Prevention:** Always wrap synchronous file system calls in a thread pool (e.g., `starlette.concurrency.run_in_threadpool`) or use an async file system library (like `aiofiles`) when operating inside an `async def` route.

## 2026-02-24 - Insecure Path Boundary Validation
**Vulnerability:** Path traversal protection in the catch-all route was incorrectly implemented using string prefix matching (`safe_path.startswith(frontend_dist)`). An attacker could bypass this by creating a sibling directory like `/app/frontend/dist_attack`.
**Learning:** String comparisons are not safe for file path validation.
**Prevention:** Use `os.path.commonpath([os.path.abspath(safe_path), os.path.abspath(base_dir)]) == os.path.abspath(base_dir)` to enforce strict path boundaries, and carefully handle cross-drive exceptions (`ValueError`) on Windows.
