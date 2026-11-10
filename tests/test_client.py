import io
import json
import os
import unittest
import urllib.error
from unittest import mock

from careersite_jobs import (JobsClient, Job, MissingTokenError, AuthError,
                             InsufficientCreditError, RateLimitError)


class FakeResp:
    def __init__(self, data):
        self._d = json.dumps(data).encode()
    def read(self):
        return self._d
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False


def http_err(code):
    return urllib.error.HTTPError("u", code, "x", {}, io.BytesIO(b'{"error":{"message":"m"}}'))


class T(unittest.TestCase):
    def test_missing_token(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(MissingTokenError):
                JobsClient()

    def test_search_payload(self):
        with mock.patch("urllib.request.urlopen", return_value=FakeResp([{"title": "a", "foo": 1}])) as m:
            out = JobsClient(token="t").search("rust", limit=5, remote_only=True)
        req = m.call_args[0][0]
        self.assertIn("appley_rhodolite~ats-jobs-api/run-sync-get-dataset-items", req.full_url)
        self.assertNotIn("token", req.full_url.lower())
        self.assertEqual(req.get_header("Authorization"), "Bearer t")
        body = json.loads(req.data)
        self.assertEqual(body, {"mode": "search", "keywords": ["rust"], "maxItems": 5, "remoteOnly": True})
        self.assertEqual(out[0]["title"], "a")

    def test_workday_and_jobs(self):
        with mock.patch("urllib.request.urlopen", return_value=FakeResp([{"title": "x", "zzz": 2}])) as m:
            out = JobsClient(token="t").workday("https://a.wd5.myworkdayjobs.com/X", search="eng", as_jobs=True)
        self.assertEqual(json.loads(m.call_args[0][0].data)["careerSiteUrls"], ["https://a.wd5.myworkdayjobs.com/X"])
        self.assertIsInstance(out[0], Job)
        self.assertEqual(out[0].extra, {"zzz": 2})

    def test_errors(self):
        for code, exc in ((401, AuthError), (402, InsufficientCreditError), (429, RateLimitError)):
            with mock.patch("urllib.request.urlopen", side_effect=http_err(code)):
                with self.assertRaises(exc):
                    JobsClient(token="t").search("x")


@unittest.skipUnless(os.environ.get("CAREERSITE_LIVE") and os.environ.get("APIFY_TOKEN"),
                     "set CAREERSITE_LIVE=1 and APIFY_TOKEN for the live smoke test (~US$0.01)")
class Live(unittest.TestCase):
    def test_live_search(self):
        jobs = JobsClient().search("engineer", limit=5)
        self.assertTrue(0 < len(jobs) <= 5)
        self.assertIn("title", jobs[0])


if __name__ == "__main__":
    unittest.main()

