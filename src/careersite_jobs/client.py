"""Thin client around the Apify run-sync-get-dataset-items endpoint."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field, fields
from typing import Any, Dict, Iterable, List, Optional, Union

API_BASE = "https://api.apify.com/v2"
OWNER = "appley_rhodolite"

ACTORS = {
    "ats": "ats-jobs-api",
    "greenhouse": "greenhouse-jobs-api",
    "ashby": "ashby-jobs-api",
    "lever": "lever-jobs-api",
    "workday": "workday-jobs-live",
    "hn": "hn-toolkit",
    "trends": "trends-now-multigeo",
}


class CareersiteError(Exception):
    """Base error."""


class MissingTokenError(CareersiteError):
    pass


class AuthError(CareersiteError):
    pass


class InsufficientCreditError(CareersiteError):
    pass


class RateLimitError(CareersiteError):
    pass


class ApiError(CareersiteError):
    def __init__(self, message: str, status: Optional[int] = None):
        super().__init__(message)
        self.status = status


@dataclass
class Job:
    """Optional typed view of one job item. Unknown fields land in ``extra``."""
    jobId: Optional[str] = None
    ats: Optional[str] = None
    company: Optional[str] = None
    companySlug: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    isRemote: Optional[bool] = None
    employmentType: Optional[str] = None
    postedAt: Optional[str] = None
    updatedAt: Optional[str] = None
    applyUrl: Optional[str] = None
    salary: Any = None
    sourceUrl: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Job":
        names = {f.name for f in fields(cls)} - {"extra"}
        known = {k: v for k, v in d.items() if k in names}
        return cls(**known, extra={k: v for k, v in d.items() if k not in names})


def _as_list(v: Union[None, str, Iterable[str]]) -> Optional[List[str]]:
    if v is None:
        return None
    if isinstance(v, str):
        return [v]
    return list(v)


def _clean(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


class JobsClient:
    """Client. Supply your own Apify token (``token=`` or ``APIFY_TOKEN`` env var).

    You pay Apify per result; see the actor pages for pricing.
    """

    def __init__(self, token: Optional[str] = None, timeout: int = 300,
                 api_base: str = API_BASE, owner: str = OWNER):
        self.token = token or os.environ.get("APIFY_TOKEN")
        if not self.token:
            raise MissingTokenError(
                "No Apify token found. Pass JobsClient(token=...) or set the "
                "APIFY_TOKEN environment variable. Get one at "
                "https://console.apify.com/settings/integrations")
        self.timeout = int(timeout)
        self.api_base = api_base.rstrip("/")
        self.owner = owner

    # -- low level -------------------------------------------------------
    def run_actor(self, actor: str, run_input: Dict[str, Any],
                  as_jobs: bool = False) -> List[Any]:
        """Run any actor synchronously and return its dataset items."""
        name = ACTORS.get(actor, actor)
        url = (f"{self.api_base}/acts/{self.owner}~{name}/"
               f"run-sync-get-dataset-items?format=json&timeout={self.timeout}")
        req = urllib.request.Request(
            url, data=json.dumps(run_input).encode("utf-8"), method="POST",
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.token}",
                     "User-Agent": "careersite-jobs/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout + 30) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            raise self._map_error(e.code, e.read().decode("utf-8", "replace")) from None
        except urllib.error.URLError as e:
            raise ApiError(f"Network error talking to Apify: {e.reason}") from None
        try:
            items = json.loads(body) if body.strip() else []
        except ValueError:
            raise ApiError("Apify returned a non-JSON response.") from None
        if not isinstance(items, list):
            items = [items]
        return [Job.from_dict(i) for i in items] if as_jobs else items

    @staticmethod
    def _map_error(status: int, body: str) -> CareersiteError:
        try:
            msg = json.loads(body).get("error", {}).get("message", "")
        except Exception:
            msg = body[:200]
        if status == 401:
            return AuthError("Apify rejected the token (HTTP 401). Check APIFY_TOKEN.")
        if status == 402:
            return InsufficientCreditError(
                "Apify credit exhausted or monthly usage limit reached (HTTP 402). "
                "Top up at https://console.apify.com/billing")
        if status == 429:
            return RateLimitError("Apify rate limit hit (HTTP 429). Wait and retry.")
        if status == 404:
            return ApiError("Actor not found (HTTP 404). It may not be public yet.", 404)
        return ApiError(f"Apify API error HTTP {status}: {msg}", status)

    # -- high level ------------------------------------------------------
    def search(self, keywords: Union[str, Iterable[str]], limit: int = 50, *,
               locations=None, remote_only: Optional[bool] = None, ats=None,
               exclude=None, posted_within_days: Optional[int] = None,
               keyword_match: Optional[str] = None,
               include_description: Optional[bool] = None,
               as_jobs: bool = False) -> List[Any]:
        """Keyword search across ~8,600 company boards (ats-jobs-api)."""
        return self.run_actor("ats", _clean({
            "mode": "search", "keywords": _as_list(keywords), "maxItems": limit,
            "locations": _as_list(locations), "remoteOnly": remote_only,
            "atsFilter": _as_list(ats), "excludeKeywords": _as_list(exclude),
            "postedWithinDays": posted_within_days, "keywordMatch": keyword_match,
            "includeDescription": include_description}), as_jobs)

    def _board(self, actor: str, companies, keywords, limit, per_company, locations,
               remote_only, include_description, as_jobs):
        return self.run_actor(actor, _clean({
            "mode": "companies", "companies": _as_list(companies),
            "keywords": _as_list(keywords), "maxItems": limit,
            "maxItemsPerCompany": per_company, "locations": _as_list(locations),
            "remoteOnly": remote_only, "includeDescription": include_description}), as_jobs)

    def company(self, companies, **kw):
        """Any of Greenhouse/Lever/Ashby/SmartRecruiters via ats-jobs-api (auto-detect)."""
        return self._board("ats", companies, kw.get("keywords"), kw.get("limit", 50),
                           kw.get("per_company"), kw.get("locations"), kw.get("remote_only"),
                           kw.get("include_description"), kw.get("as_jobs", False))

    def greenhouse(self, companies, keywords=None, limit: int = 50, per_company=None,
                   locations=None, remote_only=None, include_description=None,
                   as_jobs: bool = False):
        return self._board("greenhouse", companies, keywords, limit, per_company,
                           locations, remote_only, include_description, as_jobs)

    def ashby(self, companies, keywords=None, limit: int = 50, per_company=None,
              locations=None, remote_only=None, include_description=None,
              as_jobs: bool = False):
        return self._board("ashby", companies, keywords, limit, per_company,
                           locations, remote_only, include_description, as_jobs)

    def lever(self, companies, keywords=None, limit: int = 50, per_company=None,
              locations=None, remote_only=None, include_description=None,
              as_jobs: bool = False):
        return self._board("lever", companies, keywords, limit, per_company,
                           locations, remote_only, include_description, as_jobs)

    def workday(self, career_site_urls, search: Optional[str] = None, limit: int = 20,
                include_description: Optional[bool] = None, as_jobs: bool = False):
        """Live Workday career site(s) (workday-jobs-live)."""
        return self.run_actor("workday", _clean({
            "careerSiteUrls": _as_list(career_site_urls), "searchText": search,
            "maxItemsPerSite": limit, "includeDescription": include_description}), as_jobs)

    # -- not public yet --------------------------------------------------
    def hn(self, **run_input):
        """hn-toolkit. Pass actor input fields as kwargs."""
        return self.run_actor("hn", run_input)

    def trends(self, **run_input):
        """trends-now-multigeo. Pass actor input fields as kwargs."""
        return self.run_actor("trends", run_input)
