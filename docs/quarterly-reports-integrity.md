# Quarterly reports data integrity

The US quarterly reports route has no configured SEC filings provider. It now
returns `items: []`, `status: unavailable`, and
`reason: sec_provider_not_configured` for NASDAQ and NYSE rather than generating
calendar-based filings. A quarter end does not establish a company's fiscal
period, filing type, publication date, or existence of a filing. An EDGAR search
URL is not a PDF filing. India retains the existing empty-items contract.

No SEC integration or network access is added. Consumers that only read `items`
continue to receive an empty list. A future provider must supply verified filing
metadata before returning report rows.

Offline check (from repository root):

    python -B backend/tests/test_quarterly_reports_offline.py -v

The stdlib-only tests compile the actual route body and market constants from
its AST without importing the application, FastAPI, provider dependencies or
backend test conftest. They check both US markets, normalized market input,
limits, the unchanged India response and invalid-market rejection. They are
not HTTP integration tests and do not validate FastAPI query validation or
frontend rendering. All function arguments are passed explicitly.
