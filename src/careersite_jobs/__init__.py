"""careersite-jobs: Python client for public Apify job-board actors (zero dependencies)."""
from .client import (
    JobsClient,
    Job,
    CareersiteError,
    MissingTokenError,
    AuthError,
    InsufficientCreditError,
    RateLimitError,
    ApiError,
)

__version__ = "0.1.0"
__all__ = [
    "JobsClient", "Job", "CareersiteError", "MissingTokenError", "AuthError",
    "InsufficientCreditError", "RateLimitError", "ApiError", "__version__",
]
