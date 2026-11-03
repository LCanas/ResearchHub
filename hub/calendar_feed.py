"""iCalendar (.ics) output for the Events page.

/events/calendar.ics is a subscribable feed of every hub event, including those
imported from the FoLSM AI Portal, so one subscription covers both. Calendar
apps re-fetch it periodically. Single events can also be downloaded as .ics.

Event times are stored as UK local time, so they're written with
TZID=Europe/London (and a matching VTIMEZONE, which Outlook needs).
"""
from datetime import datetime, timedelta

CALENDAR_NAME = "FoLSM AI Collaboration Hub events"

_VTIMEZONE = """BEGIN:VTIMEZONE
TZID:Europe/London
BEGIN:DAYLIGHT
TZOFFSETFROM:+0000
TZOFFSETTO:+0100
TZNAME:BST
DTSTART:19700329T010000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0100
TZOFFSETTO:+0000
TZNAME:GMT
DTSTART:19701025T020000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE""".split("\n")


def _escape(text):
    return (str(text or "").replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\r\n", "\\n").replace("\n", "\\n"))


def _fold(line):
    """iCalendar lines must be at most 75 octets; continue with a space."""
    out, current = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        if len(current) + len(b) > 75:
            out.append(current.decode("utf-8"))
            current = b" " + b
        else:
            current += b
    out.append(current.decode("utf-8"))
    return "\r\n".join(out)


def _local(dt):
    return dt.strftime("%Y%m%dT%H%M%S")


def _vevent(ev, url, host):
    end = ev.end_at or ev.start_at + timedelta(hours=1)
    uid = (f"{ev.external_source}-{ev.external_id}" if ev.is_external
           else f"hub-event-{ev.id}") + f"@{host}"
    description = ev.description or ""
    if ev.is_external and ev.url:
        description += f"\n\nDetails and registration ({ev.source_name}): {ev.url}"
    description += f"\n\n{url}"
    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART;TZID=Europe/London:{_local(ev.start_at)}",
        f"DTEND;TZID=Europe/London:{_local(end)}",
        f"SUMMARY:{_escape(ev.title)}",
        f"DESCRIPTION:{_escape(description.strip())}",
        f"URL:{url}",
    ]
    if ev.is_online or ev.location:
        lines.append(f"LOCATION:{_escape('Online' if ev.is_online else ev.location)}")
    if ev.event_type:
        lines.append(f"CATEGORIES:{_escape(ev.event_type)}")
    lines.append("END:VEVENT")
    return lines


def build_ics(events, url_for_event, host, name=CALENDAR_NAME):
    """Return the .ics text for ``events``; ``url_for_event(ev)`` gives each
    event's page on the hub."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             "PRODID:-//FoLSM AI Collaboration Hub//Events//EN",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             f"X-WR-CALNAME:{_escape(name)}", "X-WR-TIMEZONE:Europe/London",
             # Ask calendar apps to check for new events every few hours.
             "REFRESH-INTERVAL;VALUE=DURATION:PT6H", "X-PUBLISHED-TTL:PT6H"]
    lines += _VTIMEZONE
    for ev in events:
        lines += _vevent(ev, url_for_event(ev), host)
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"


def google_add_link(ev, url):
    """A link that opens Google Calendar with this single event filled in."""
    from urllib.parse import urlencode
    end = ev.end_at or ev.start_at + timedelta(hours=1)
    params = {
        "action": "TEMPLATE", "text": ev.title,
        "dates": f"{_local(ev.start_at)}/{_local(end)}", "ctz": "Europe/London",
        "details": f"{(ev.description or '')[:1200]}\n\n{url}".strip(),
        "location": "Online" if ev.is_online else (ev.location or ""),
    }
    return "https://calendar.google.com/calendar/render?" + urlencode(params)
