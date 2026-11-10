"""Tiny CLI: python -m careersite_jobs search "rust engineer" --limit 20 --json"""
import argparse
import json
import sys

from .client import JobsClient, CareersiteError


def _table(items):
    for j in items:
        print(f"{(j.get('company') or '')[:24]:24} | {(j.get('title') or '')[:50]:50} | "
              f"{(j.get('location') or '')[:25]:25} | {j.get('applyUrl') or ''}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="careersite-jobs")
    p.add_argument("--token", help="Apify token (default: APIFY_TOKEN env var)")
    p.add_argument("--json", action="store_true", help="print raw JSON")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search", help="keyword search across ~8,600 boards")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=20)
    s.add_argument("--location", action="append")
    s.add_argument("--remote", action="store_true")
    for name in ("greenhouse", "ashby", "lever"):
        b = sub.add_parser(name, help=f"jobs from {name} board(s)")
        b.add_argument("company", nargs="+")
        b.add_argument("--keyword", action="append")
        b.add_argument("--limit", type=int, default=20)
    w = sub.add_parser("workday", help="live Workday career site")
    w.add_argument("url")
    w.add_argument("--search")
    w.add_argument("--limit", type=int, default=20)
    a = p.parse_args(argv)
    try:
        c = JobsClient(token=a.token)
        if a.cmd == "search":
            items = c.search(a.query, limit=a.limit, locations=a.location,
                             remote_only=True if a.remote else None)
        elif a.cmd == "workday":
            items = c.workday(a.url, search=a.search, limit=a.limit)
        else:
            items = getattr(c, a.cmd)(a.company, keywords=a.keyword, limit=a.limit)
    except CareersiteError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if a.json:
        json.dump(items, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        _table(items)
        print(f"{len(items)} jobs", file=sys.stderr)
    return 0
