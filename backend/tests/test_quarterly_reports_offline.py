"""Isolated route-body tests: no application, provider, database or network imports.

Run directly with Python (stdlib only). This is not an HTTP integration test.
The AST loader retains the real function body but removes FastAPI decorators
and defaults so importing backend.api.deps cannot initialize production services.
"""
import ast
import asyncio
from pathlib import Path
import unittest


class RouteError(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail


def load_route(source):
    tree = ast.parse(source)
    names = {"US_MARKETS", "IN_MARKETS", "SUPPORTED_MARKETS"}
    nodes = [node for node in tree.body if isinstance(node, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id in names for t in node.targets)]
    route = next(node for node in tree.body
                 if isinstance(node, ast.AsyncFunctionDef) and node.name == "quarterly_reports")
    route.decorator_list = []
    route.args.defaults = []
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *nodes, route], type_ignores=[])
    namespace = {"HTTPException": RouteError}
    exec(compile(ast.fix_missing_locations(module), "quarterly_route_isolated", "exec"), namespace)
    return namespace["quarterly_reports"]


class QuarterlyReportsOfflineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (Path(__file__).resolve().parents[1] / "reports" / "routes.py").read_text(encoding="utf-8")

    def call_route(self, market, symbol="AAPL", limit=8):
        return asyncio.run(load_route(self.source)(market=market, symbol=symbol, limit=limit))

    def test_us_reports_never_invent_sec_filings(self):
        for market in ("NASDAQ", "NYSE", " nasdaq "):
            for limit in (1, 8, 50):
                with self.subTest(market=market, limit=limit):
                    self.assertEqual(self.call_route(market, limit=limit), {
                        "items": [], "status": "unavailable", "reason": "sec_provider_not_configured"})

    def test_india_contract_unchanged(self):
        for market in ("NSE", "BSE", " nse "):
            self.assertEqual(self.call_route(market), {"items": []})

    def test_unsupported_market_rejected(self):
        with self.assertRaises(RouteError) as caught:
            self.call_route("INVALID")
        self.assertEqual(caught.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
