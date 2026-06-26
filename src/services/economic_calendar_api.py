"""
US economic calendar via the unofficial ForexFactory weekly feed.

Source: https://nfs.faireconomy.media/ff_calendar_thisweek.json

Known limitations of this source (read before relying on it in prod):

1. NO API KEY NEEDED. There's nothing to put in .env for this provider.
2. ONLY "THIS WEEK" IS AVAILABLE. There is no historical/forward
   date-range query — the feed always returns the current week's events.
   fetch_us_events(date_from, date_to) filters that single week's data;
   any date outside the current week will just return an empty list.
3. RATE LIMITED & FRAGILE. ForexFactory has been observed throttling the
   weekly export files (json/xml/csv/ics combined) to roughly 2 requests
   per 5 minutes per IP. Exceeding it returns an HTML "Request Denied"
   page instead of JSON, and the feed/URL has changed before without
   notice. This class caches the weekly payload and self-throttles so
   normal polling won't trip the limit, but a hard fail is still possible
   if the upstream feed changes shape or moves again.
4. "country" IS A CURRENCY CODE, not an ISO country code. US events are
   tagged "USD", not "US".
"""

import json
import logging
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

logger = logging.getLogger(__name__)

WIB = ZoneInfo("Asia/Jakarta")
UTC = ZoneInfo("UTC")

# US macro events with high market impact (ForexFactory event title matching)
US_MACRO_KEYWORDS = (
    "cpi",
    "ppi",
    "pce",
    "nonfarm",
    "non-farm",
    "payroll",
    "unemployment",
    "fomc",
    "fed ",
    "federal reserve",
    "interest rate",
    "gdp",
    "retail sales",
    "ism ",
    "pmi",
    "consumer confidence",
    "durable goods",
    "initial jobless",
    "jobless claims",
    "trade balance",
    "housing starts",
    "building permits",
    "industrial production",
    "treasury",
    "core inflation",
    "inflation rate",
    "manufacturing",
    "services pmi",
    "adp",
    "philadelphia fed",
    "michigan",
)

IMPACT_RANK = {"low": 1, "medium": 2, "high": 3}


class EconomicCalendarAPI:
    """Fetch US economic calendar events from the unofficial ForexFactory feed."""

    BASE_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

    def __init__(self, cache_ttl_seconds: int = 300, request_timeout: int = 15):
        # cache_ttl_seconds default of 300s (5 min) is chosen to stay under
        # ForexFactory's observed rate limit. Don't set this much lower.
        self.cache_ttl_seconds = cache_ttl_seconds
        self.request_timeout = request_timeout
        self._cache: list[dict] | None = None
        self._cache_fetched_at: float | None = None

    def _fetch_week_raw(self, force: bool = False) -> list[dict]:
        now_monotonic = time.monotonic()
        cache_is_fresh = (
            self._cache is not None
            and self._cache_fetched_at is not None
            and (now_monotonic - self._cache_fetched_at) < self.cache_ttl_seconds
        )
        if cache_is_fresh and not force:
            return self._cache

        try:
            response = requests.get(self.BASE_URL, timeout=self.request_timeout)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, json.JSONDecodeError, ValueError) as exc:
            # Most likely cause here: ForexFactory's rate limit kicked in and
            # returned an HTML "Request Denied" page instead of JSON, which
            # blows up response.json(). Fall back to whatever we last had.
            logger.warning(
                "[ECON CALENDAR] Fetch failed (%s); using stale cache if available.",
                exc,
            )
            return self._cache or []

        if not isinstance(payload, list):
            logger.warning("[ECON CALENDAR] Unexpected payload shape from ForexFactory feed.")
            return self._cache or []

        self._cache = payload
        self._cache_fetched_at = now_monotonic
        return payload

    @staticmethod
    def _parse_event_time(raw_date: str) -> datetime | None:
        if not raw_date:
            return None
        try:
            # ForexFactory's "date" already comes as ISO-8601 with its own
            # UTC offset attached, e.g. "2024-08-01T12:30:00-04:00".
            return datetime.fromisoformat(raw_date)
        except ValueError:
            return None

    @staticmethod
    def _to_wib(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        return dt.astimezone(WIB)

    @staticmethod
    def _is_us_macro_event(event: dict) -> bool:
        if event.get("country") != "USD":
            return False

        impact = (event.get("impact") or "").lower()
        event_name = (event.get("title") or "").lower()

        if impact in {"high", "medium"}:
            return True

        return any(keyword in event_name for keyword in US_MACRO_KEYWORDS)

    def _normalize_event(self, raw: dict) -> dict:
        dt = self._parse_event_time(raw.get("date") or "")
        dt_wib = self._to_wib(dt)
        event_name = raw.get("title") or "Unknown Event"
        time_wib = dt_wib.strftime("%H:%M WIB") if dt_wib else "TBA"
        date_wib = dt_wib.strftime("%Y-%m-%d") if dt_wib else ""

        event_id = f"{date_wib}|{time_wib}|{event_name}|US"

        actual = (raw.get("actual") or "").strip() or None
        impact = (raw.get("impact") or "low").lower()
        if impact not in IMPACT_RANK:
            impact = "low"  # covers values like "Holiday" / "Non-Economic"

        return {
            "id": event_id,
            "country": "US",
            "event": event_name,
            "impact": impact,
            "time_utc": dt.astimezone(UTC).isoformat() if dt else None,
            "time_wib": time_wib,
            "date_wib": date_wib,
            "datetime_wib": dt_wib,
            "actual": actual,
            "estimate": (raw.get("forecast") or "").strip() or None,
            "prev": (raw.get("previous") or "").strip() or None,
            "unit": None,  # ForexFactory pre-formats values, e.g. "7.4%"
            "is_released": actual is not None,
        }

    def fetch_us_events(self, date_from: str, date_to: str) -> list[dict]:
        """Filter the current week's US macro events into [date_from, date_to].

        NOTE: this source only ever holds the CURRENT WEEK's data. A range
        outside the current week will silently return [] — that's this
        feed's limitation, not a bug here.
        """
        raw_events = self._fetch_week_raw()
        normalized = [
            self._normalize_event(item)
            for item in raw_events
            if self._is_us_macro_event(item)
        ]

        try:
            start = datetime.strptime(date_from, "%Y-%m-%d").date()
            end = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            logger.warning("[ECON CALENDAR] Invalid date_from/date_to: %s / %s", date_from, date_to)
            return []

        in_range = [
            e
            for e in normalized
            if e["datetime_wib"] is not None and start <= e["datetime_wib"].date() <= end
        ]

        if not in_range and normalized:
            available_dates = sorted({e["date_wib"] for e in normalized if e["date_wib"]})
            if available_dates and (date_to < available_dates[0] or date_from > available_dates[-1]):
                logger.info(
                    "[ECON CALENDAR] Requested %s..%s is outside the current week (%s..%s) "
                    "available from this feed.",
                    date_from, date_to, available_dates[0], available_dates[-1],
                )

        in_range.sort(
            key=lambda e: (
                e["datetime_wib"] or datetime.max.replace(tzinfo=WIB),
                -IMPACT_RANK.get(e["impact"], 0),
            )
        )
        return in_range

    def get_today_events(self) -> list[dict]:
        today_wib = datetime.now(WIB).date()
        date_str = today_wib.strftime("%Y-%m-%d")
        return self.fetch_us_events(date_str, date_str)

    def get_released_events(self, events: list[dict] | None = None) -> list[dict]:
        events = events if events is not None else self.get_today_events()
        return [event for event in events if event["is_released"]]

    def get_upcoming_events(self, events: list[dict] | None = None) -> list[dict]:
        now_wib = datetime.now(WIB)
        events = events if events is not None else self.get_today_events()
        upcoming = []
        for event in events:
            if event["is_released"]:
                continue
            dt = event.get("datetime_wib")
            if dt is None or dt >= now_wib:
                upcoming.append(event)
        return upcoming

    def get_events_starting_within(self, minutes: int) -> list[dict]:
        now_wib = datetime.now(WIB)
        window_end = now_wib + timedelta(minutes=minutes)
        result = []
        for event in self.get_upcoming_events():
            dt = event.get("datetime_wib")
            if dt and now_wib <= dt <= window_end:
                result.append(event)
        return result