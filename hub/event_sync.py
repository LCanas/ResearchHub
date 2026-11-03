"""Import events from external calendars (config.EVENT_FEEDS) into the hub.

Each feed is a WordPress site with "The Events Calendar" plugin, read through
its public REST API. Imported events are stored as normal Event rows tagged
with ``external_source`` / ``external_id``, so they appear on the Events page,
the home page and the newsletter. Running the sync again updates them, and
removes ones that were deleted at the source.

Runs on boot (init_db.py), at most every EVENT_SYNC_MINUTES while people browse
the Events or home page, and on demand: `python manage.py sync-events`.
"""
import html
import json
import logging
import re
import threading
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

from .config import EVENT_FEEDS, EVENT_SYNC_MINUTES, EVENT_SYNC_PAST_DAYS, EVENT_TYPES
from .extensions import db
from .models import Event

log = logging.getLogger(__name__)
TIMEOUT = 15
_last_sync = 0.0
_lock = threading.Lock()


def _get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "CollaborationHub/1.0",
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.load(resp)


def fetch(feed, since):
    """All events from ``since`` onwards, following the API's pages."""
    query = urllib.parse.urlencode({"start_date": since.isoformat(), "per_page": 50})
    url = f"{feed['url'].rstrip('/')}/wp-json/tribe/events/v1/events?{query}"
    events = []
    while url and len(events) < 1000:
        data = _get_json(url)
        events += data.get("events", [])
        url = data.get("next_rest_url")
    return events


def html_to_text(raw):
    """Turn the event's HTML description into readable plain text."""
    text = re.sub(r"(?i)<br\s*/?>", "\n", raw or "")
    text = re.sub(r"(?i)</(p|div|li|h[1-6]|blockquote|tr)>", "\n", text)
    text = re.sub(r"(?i)<li[^>]*>", "• ", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _parse_dt(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return None


def _event_type(item):
    names = [c.get("name", "") for c in item.get("categories") or []]
    for name in names:
        for t in EVENT_TYPES:
            if t.lower() in name.lower():
                return t
    return "Seminar"


def _location(item):
    venue = item.get("venue")
    if not isinstance(venue, dict) or not venue:
        return "", False
    parts = [venue.get("venue"), venue.get("address"), venue.get("city")]
    text = ", ".join(html.unescape(p) for p in parts if p)
    return text[:200], "online" in text.lower()


def sync_feed(feed):
    since = date.today() - timedelta(days=EVENT_SYNC_PAST_DAYS)
    items = fetch(feed, since)
    existing = {e.external_id: e for e in
                Event.query.filter_by(external_source=feed["key"]).all()}
    seen, added, updated = set(), 0, 0
    for item in items:
        start = _parse_dt(item.get("start_date"))
        if not start or item.get("status", "publish") != "publish":
            continue
        ext_id = str(item["id"])
        seen.add(ext_id)
        ev = existing.get(ext_id)
        if ev is None:
            ev = Event(external_source=feed["key"], external_id=ext_id)
            db.session.add(ev)
            added += 1
        else:
            updated += 1
        location, online = _location(item)
        ev.title = html.unescape(item.get("title") or "Untitled event")[:200]
        ev.description = html_to_text(item.get("description"))
        ev.start_at = start
        ev.end_at = _parse_dt(item.get("end_date"))
        ev.location = location
        ev.is_online = online
        ev.url = (item.get("url") or feed["events_page"])[:255]
        ev.event_type = _event_type(item)
    # Remove events deleted at the source (only within the window we fetched).
    removed = 0
    for ext_id, ev in existing.items():
        if ext_id not in seen and ev.start_at.date() >= since:
            db.session.delete(ev)
            removed += 1
    db.session.commit()
    return {"added": added, "updated": updated, "removed": removed}


def sync_all():
    """Sync every feed. Returns {feed name: counts or error message}."""
    global _last_sync
    results = {}
    for feed in EVENT_FEEDS:
        try:
            results[feed["name"]] = sync_feed(feed)
        except Exception as exc:  # network down, site changed… never break the hub
            db.session.rollback()
            log.warning("Event sync from %s failed: %s", feed["name"], exc)
            results[feed["name"]] = f"failed: {exc}"
    _last_sync = time.time()
    return results


def sync_if_stale(app):
    """Refresh in the background if the last sync is older than
    EVENT_SYNC_MINUTES, so page views are never slowed down."""
    global _last_sync
    if not EVENT_FEEDS or app.testing or time.time() - _last_sync < EVENT_SYNC_MINUTES * 60:
        return
    if not _lock.acquire(blocking=False):
        return
    _last_sync = time.time()

    def run():
        try:
            with app.app_context():
                sync_all()
        finally:
            _lock.release()

    threading.Thread(target=run, daemon=True).start()
