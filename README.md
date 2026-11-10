# careersite-jobs

Search job listings from **Greenhouse, Lever, Ashby, SmartRecruiters and Workday** career sites from Python or the command line. A zero-dependency wrapper around public [Apify](https://apify.com) actors that return clean, unified JSON.

- Keyword search across ~8,600 company job boards in one call
- Pull every open job from a single company board
- Live Workday career sites
- Pure standard library, Python 3.9+, no dependencies

## Install

```bash
pip install careersite-jobs
export APIFY_TOKEN=your_apify_token   # https://console.apify.com/settings/integrations
```

You bring your own Apify token. **Pricing:** you pay Apify per result; see each actor page for current prices.

## Examples

```python
from careersite_jobs import JobsClient

c = JobsClient()  # reads APIFY_TOKEN

# 1. Keyword search across thousands of boards
jobs = c.search("rust engineer", limit=50, remote_only=True)

# 2. A single company board
jobs = c.greenhouse("stripe", keywords="engineer", limit=20)

# 3. A live Workday career site
jobs = c.workday("https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
                 search="engineer", limit=20)

print(jobs[0]["title"], jobs[0]["applyUrl"])
```

Pass `as_jobs=True` to get typed `Job` dataclasses instead of dicts.

### CLI

```bash
python -m careersite_jobs search "rust engineer" --limit 20 --json
careersite-jobs greenhouse stripe --limit 10
careersite-jobs workday https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite --search engineer
```

### Errors

Clear exceptions: `MissingTokenError`, `AuthError` (401), `InsufficientCreditError` (402, Apify credit exhausted), `RateLimitError` (429), `ApiError`.

## Actors wrapped

| Method | Actor |
|---|---|
| `search()` | [ats-jobs-api](https://apify.com/appley_rhodolite/ats-jobs-api) |
| `greenhouse()` | [greenhouse-jobs-api](https://apify.com/appley_rhodolite/greenhouse-jobs-api) |
| `ashby()` | [ashby-jobs-api](https://apify.com/appley_rhodolite/ashby-jobs-api) |
| `lever()` | [lever-jobs-api](https://apify.com/appley_rhodolite/lever-jobs-api) |
| `workday()` | [workday-jobs-live](https://apify.com/appley_rhodolite/workday-jobs-live) |
| `hn()` | [hn-toolkit](https://apify.com/appley_rhodolite/hn-toolkit) |
| `trends()` | [trends-now-multigeo](https://apify.com/appley_rhodolite/trends-now-multigeo) |

## Links

- Browse the open job index: https://open-career-index.printfilestudio.workers.dev/
- No Apify account? Free REST API over the same index: https://career-index-api.printfilestudio.workers.dev/
- Source and issues: https://github.com/twdatatools/careersite-jobs

## License

MIT. Copyright TW Data Tools.

Not affiliated with, endorsed by, or sponsored by Greenhouse, Lever, Ashby, SmartRecruiters, Workday, Google or Y Combinator. All trademarks belong to their owners.
