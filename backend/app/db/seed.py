"""Deterministic sample-data seeding.

Runs once against an empty database (guarded by an explicit row check so it
is idempotent). `random.Random(42)` keeps every environment's dataset
identical — the dashboard footer proudly says "Sample data".
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from random import Random

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import (
    COLLECTIONS,
    EFFECT_OPTIONS,
    STATUSES,
    SUBTITLE_OPTIONS,
)
from app.db.models import ContentDailyStats, YoutubeContent

_SEED = 42
_EPISODES = 26
_HISTORY_DAYS = 180

_TOPIC_BY_COLLECTION: dict[str, tuple[str, ...]] = {
    "Linux Basics": (
        "chmod math in 30 seconds",
        "cron made simple",
        "systemctl list-units cheat code",
        "grep -o the words you want",
        "journalctl --since today",
        "nohup, disown & screen",
    ),
    "Network Hacking": (
        "netcat listener on 9999",
        "extra verbose with -vv",
        "nmap -sV top 100 ports",
        "tcpdump in one take",
        "SSH tunneling for humans",
        "Wireshark follow stream",
        "ARP spoof in a lab",
    ),
    "Privilege Escalation": (
        "find SUID binaries",
        "sudo -l low-hanging fruit",
        "SUID env path abuse",
        "docker group = root",
        "cron file misconfig",
    ),
    "OSINT": (
        "whois beyond the basics",
        "google dork starter pack",
        "shodan honeypot sweep",
        "metadata in screenshots",
        "theHarvest in 40 seconds",
    ),
    "Scripting & Automation": (
        "bash loop over find",
        "xargs is a superpower",
        "python one-liner servers",
        "rsync dry-run first",
        "make your own CLI",
    ),
}

_FLAVORS = (
    "terminal speedrun",
    "no fluff edition",
    "one-take take",
    "read the man page",
    "in under a minute",
    "the short version",
)


def needs_seed(session: Session) -> bool:
    """True when the content table is empty."""
    count = session.scalar(select(func.count()).select_from(YoutubeContent))
    return (count or 0) == 0


def seed(session: Session, *, today: date | None = None) -> int:
    """Insert the deterministic sample dataset. Returns episodes created."""
    if not needs_seed(session):
        return 0

    rng = Random(_SEED)
    today = today or date.today()
    start = today - timedelta(days=_HISTORY_DAYS - 1)
    created = 0

    for index in range(_EPISODES):
        collection = COLLECTIONS[index % len(COLLECTIONS)]
        assert isinstance(collection["name"], str)
        name = str(collection["name"])
        topics = _TOPIC_BY_COLLECTION[name]
        topic = topics[index % len(topics)]
        flavor = _FLAVORS[index % len(_FLAVORS)]
        episode_no = index + 1
        published_day = start + timedelta(days=int(_HISTORY_DAYS * (index / _EPISODES)))
        # Older episodes are Published; the newest few sit in the pipeline.
        age = (today - published_day).days
        if age > 21:
            status = "Published"
        elif age > 12:
            status = STATUSES[rng.randrange(4, 6)]
        else:
            status = STATUSES[rng.randrange(0, 4)]

        duration = rng.randrange(30, 76, 5)
        row = YoutubeContent(
            episode=episode_no,
            date=published_day,
            title=f"{topic} · {flavor}",
            status=status,
            collection=name,
            sound_music=str(rng.choice(collection["sounds"])),  # type: ignore[arg-type]
            effects=" · ".join(rng.sample(list(EFFECT_OPTIONS), rng.randrange(1, 3))),
            subtitles=str(rng.choice(SUBTITLE_OPTIONS[1:])),
            thumbnail=f"thumbs/{name.lower().replace(' ', '-')}/ep-{episode_no}.jpg",
            duration_sec=duration,
        )
        session.add(row)
        session.flush()  # need row.id for the stats rows

        _seed_stats_for_episode(rng, session, row, published_day, today)
        created += 1

    session.commit()
    return created


def _seed_stats_for_episode(
    rng: Random,
    session: Session,
    row: YoutubeContent,
    published_day: date,
    today: date,
) -> None:
    """Views decay from publish day; a lucky few get a viral spike."""
    base_views = rng.randrange(350, 2400)
    decay = rng.uniform(4.5, 9.0)  # days
    ctr = rng.uniform(0.045, 0.09)
    like_rate = rng.uniform(0.03, 0.07)
    sub_rate = rng.uniform(0.003, 0.012)
    retention = rng.uniform(0.55, 0.78)
    viral_on: date | None = None
    if rng.random() < 0.3:  # 30% of episodes get one spike day
        viral_on = published_day + timedelta(days=rng.randrange(1, 6))

    day = published_day
    while day <= today:
        age = (day - published_day).days
        views = base_views * math.exp(-age / decay) * rng.uniform(0.75, 1.25)
        if day == viral_on:
            views *= rng.uniform(2.5, 4.0)
        views = max(0, int(views))
        impressions = int(views / ctr) if views else 0
        session.add(
            ContentDailyStats(
                content_id=row.id,
                day=day,
                views=views,
                impressions=impressions,
                watch_seconds=int(views * row.duration_sec * retention),
                likes=int(views * like_rate),
                subs_gained=int(views * sub_rate),
            )
        )
        day += timedelta(days=1)
