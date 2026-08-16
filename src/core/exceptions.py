"""Stable, user-safe error codes for provider and job failures."""

from __future__ import annotations

USER_MESSAGES: dict[str, str] = {
    "YOUTUBE_INVALID_URL": "That YouTube URL is not a supported playlist or channel link.",
    "YOUTUBE_NOT_FOUND": "The YouTube playlist or channel could not be found.",
    "YOUTUBE_QUOTA_EXCEEDED": "YouTube quota was exhausted. Try again later.",
    "YOUTUBE_PAGINATION_FAILED": "YouTube stopped returning pages before the playlist finished.",
    "SPOTIFY_RATE_LIMITED": "Spotify rate-limited this job. It will resume automatically if possible.",
    "SPOTIFY_REVOKED": "Spotify access was revoked. Reconnect your account.",
    "SPOTIFY_PARTIAL_BATCH": "Some Spotify tracks could not be added. Review the job and retry.",
    "SPOTIFY_UNAVAILABLE": "Spotify is temporarily unavailable.",
    "AI_TIMEOUT": "The classifier timed out. Progress was saved.",
    "AI_INVALID_SCHEMA": "The classifier returned an invalid result. That video was sent to review.",
    "AI_REFUSAL": "The classifier refused to process a title. That video was skipped.",
    "AI_RATE_LIMITED": "The classifier was rate-limited. The job will resume if retries remain.",
    "BUDGET_EXCEEDED": "This job hit a size, time, request or cost budget.",
    "JOB_TIMEOUT": "This job exceeded the time budget.",
    "JOB_CANCELLED": "This job was cancelled.",
    "NOT_FOUND": "The requested job was not found.",
    "FORBIDDEN": "You do not have access to this job.",
    "INTERNAL_ERROR": "Something went wrong. The failure was recorded without exposing internals.",
}


class SyncError(Exception):
    code = "INTERNAL_ERROR"
    retryable = False

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        request_id: str | None = None,
        retryable: bool | None = None,
    ) -> None:
        self.code = code or self.code
        self.request_id = request_id
        if retryable is not None:
            self.retryable = retryable
        super().__init__(message or USER_MESSAGES.get(self.code, USER_MESSAGES["INTERNAL_ERROR"]))

    @property
    def user_message(self) -> str:
        return USER_MESSAGES.get(self.code, USER_MESSAGES["INTERNAL_ERROR"])


class TransientSyncError(SyncError):
    retryable = True


class YoutubeInvalidUrl(SyncError):
    code = "YOUTUBE_INVALID_URL"


class YoutubeNotFound(SyncError):
    code = "YOUTUBE_NOT_FOUND"


class YoutubeQuotaExceeded(TransientSyncError):
    code = "YOUTUBE_QUOTA_EXCEEDED"


class YoutubePaginationFailed(TransientSyncError):
    code = "YOUTUBE_PAGINATION_FAILED"


class SpotifyRateLimited(TransientSyncError):
    code = "SPOTIFY_RATE_LIMITED"


class SpotifyRevoked(SyncError):
    code = "SPOTIFY_REVOKED"


class SpotifyPartialBatch(SyncError):
    code = "SPOTIFY_PARTIAL_BATCH"


class SpotifyUnavailable(TransientSyncError):
    code = "SPOTIFY_UNAVAILABLE"


class AITimeout(TransientSyncError):
    code = "AI_TIMEOUT"


class AIInvalidSchema(SyncError):
    code = "AI_INVALID_SCHEMA"


class AIRefusal(SyncError):
    code = "AI_REFUSAL"


class AIRateLimited(TransientSyncError):
    code = "AI_RATE_LIMITED"


class BudgetExceeded(SyncError):
    code = "BUDGET_EXCEEDED"


class JobTimeout(SyncError):
    code = "JOB_TIMEOUT"


class JobCancelled(SyncError):
    code = "JOB_CANCELLED"
