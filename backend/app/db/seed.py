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

from app.core.config import get_settings
from app.core.constants import (
    COLLECTIONS,
    EFFECT_OPTIONS,
    SUBTITLE_OPTIONS,
    VISIBILITIES,
)
from app.db.models import Collection, ContentDailyStats, Series, User, YoutubeMain

# Back-compat alias used elsewhere.
YoutubeContent = YoutubeMain

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
    count = session.scalar(select(func.count()).select_from(YoutubeMain))
    return (count or 0) == 0


def _ensure_collections(session: Session) -> dict[str, Collection]:
    """Ensure COLLECTIONS rows exist; return name→row map."""
    existing = {c.name: c for c in session.scalars(select(Collection)).all()}
    for coll in COLLECTIONS:
        name = str(coll["name"])  # type: ignore[arg-type]
        color = str(coll["color"])  # type: ignore[arg-type]
        if name not in existing:
            row = Collection(name=name, color=color)
            session.add(row)
            session.flush()
            existing[name] = row
        else:
            # keep color in sync in case constants changed
            if existing[name].color != color:
                existing[name].color = color
    session.flush()
    return existing


def _ensure_demo_user(session: Session) -> User:
    settings = get_settings()
    # Use demo_email from settings but fallback to hardcoded if not set
    try:
        demo_email = settings.demo_email  # type: ignore[attr-defined]
        demo_password = settings.demo_password  # type: ignore[attr-defined]
    except Exception:
        demo_email = "demo@ytcm.test"
        demo_password = "demo-password-1"
    existing = session.scalar(select(User).where(User.email == demo_email))
    if existing is not None:
        return existing
    # hash password lazily to avoid import cost at module load
    from app.services.auth import hash_password

    user = User(email=demo_email, password_hash=hash_password(demo_password))
    session.add(user)
    session.flush()
    return user


def _ensure_seed_series(session: Session, user: User) -> Series:
    name = "Seed Series"
    row = session.scalar(select(Series).where(Series.user_id == user.id, Series.name == name))
    if row is not None:
        return row
    row = Series(user_id=user.id, name=name)
    session.add(row)
    session.flush()
    return row


def seed(session: Session, *, today: date | None = None) -> int:
    """Insert the deterministic sample dataset. Returns episodes created."""
    if not needs_seed(session):
        return 0

    rng = Random(_SEED)
    today = today or date.today()
    start = today - timedelta(days=_HISTORY_DAYS - 1)
    created = 0

    collections_by_name = _ensure_collections(session)
    demo_user = _ensure_demo_user(session)
    seed_series = _ensure_seed_series(session, demo_user)

    for index in range(_EPISODES):
        collection = COLLECTIONS[index % len(COLLECTIONS)]
        assert isinstance(collection["name"], str)
        name = str(collection["name"])
        coll_row = collections_by_name[name]
        topics = _TOPIC_BY_COLLECTION[name]
        topic = topics[index % len(topics)]
        flavor = _FLAVORS[index % len(_FLAVORS)]
        episode_no = index + 1
        published_day = start + timedelta(days=int(_HISTORY_DAYS * (index / _EPISODES)))
        # Visibility: Public for older, Private for recent — maps legacy Published→Public
        age = (today - published_day).days
        if age > 21:
            visibility = "Public"
        else:
            # deterministic but varied Private for recent pipeline
            visibility = rng.choice(list(VISIBILITIES))

        duration = rng.randrange(30, 76, 5)
        sound_choice = str(rng.choice(collection["sounds"]))  # type: ignore[arg-type]
        effects = " · ".join(rng.sample(list(EFFECT_OPTIONS), rng.randrange(1, 3)))
        subtitles_choice = str(rng.choice(SUBTITLE_OPTIONS[1:]))
        thumbnail_path = f"thumbs/{name.lower().replace(' ', '-')}/ep-{episode_no}.jpg"
        # new boolean fields derived
        sound_effects = rng.choice([True, False])
        music = rng.choice([True, False])
        subtitles_count = 0 if subtitles_choice == "None" else 1
        thumbnail_ready = True  # seed always has thumbnail

        row = YoutubeMain(
            user_id=demo_user.id,
            series_id=seed_series.id,
            episode_number=episode_no,
            date=published_day,
            title=f"{topic} · {flavor}",
            visibility=visibility,
            collection_id=coll_row.id,
            collection=name,  # legacy string for backward compat filters
            sound_effects=sound_effects,
            music=music,
            subtitles_count=subtitles_count,
            thumbnail_ready=thumbnail_ready,
            # legacy columns kept so old API/tests still see values
            sound_music=sound_choice,
            effects=effects,
            subtitles=subtitles_choice,
            thumbnail=thumbnail_path,
            duration_sec=duration,
        )
        # also ensure synonym fields consistent (episode/status aliases)
        # via synonyms episode↔episode_number and status↔visibility they are same
        session.add(row)
        session.flush()  # need row.id for the stats rows

        _seed_stats_for_episode(rng, session, row, published_day, today)
        created += 1

    session.commit()
    return created


def _seed_stats_for_episode(
    rng: Random,
    session: Session,
    row: YoutubeMain,
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
