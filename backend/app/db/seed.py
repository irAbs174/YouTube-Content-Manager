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
from app.db.models import (
    Asset,
    Collection,
    ContentDailyStats,
    ContentItem,
    EpisodeScene,
    Language,
    Series,
    SubtitleRow,
    User,
    YoutubeMain,
)

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

# Assets 👁️👁️ — (code, type, name, context, description, storage location).
# The emoji block mirrors the workbook's Assets sheet; fonts and images round
# out the `Type` select list.
_ASSETS: tuple[tuple[str, str, str, str, str, str], ...] = (
    ("AST1", "Emojie", "•", "•", "•", "assets/emoji/dot.png"),
    ("AST2", "Emojie", "💻", "💻", "💻", "assets/emoji/laptop.png"),
    ("AST3", "Emojie", "📌", "📌", "📌", "assets/emoji/pin.png"),
    ("AST4", "Emojie", "👇", "👇", "👇", "assets/emoji/point.png"),
    ("AST5", "Emojie", "👁️", "👁️", "👁️", "assets/emoji/eyes.png"),
    ("AST6", "Emojie", "♥️", "♥️", "♥️", "assets/emoji/heart.png"),
    ("AST7", "Emojie", "🎬", "🎬", "🎬", "assets/emoji/clapper.png"),
    ("AST8", "Emojie", "🔔", "🔔", "🔔", "assets/emoji/bell.png"),
    ("AST9", "Emojie", "🔍", "🔍", "🔍", "assets/emoji/magnifier.png"),
    ("AST10", "Emojie", "⚠️", "⚠️", "⚠️", "assets/emoji/warning.png"),
    ("AST11", "Emojie", "🗨️", "🗨️", "🗨️", "assets/emoji/box.png"),
    ("AST12", "Emojie", "⏭️", "⏭️", "⏭️", "assets/emoji/next.png"),
    ("AST13", "Emojie", "⏮️", "⏮️", "⏮️", "assets/emoji/previous.png"),
    ("AST14", "Emojie", "📐", "📐", "📐", "assets/emoji/ruler.png"),
    ("AST15", "Emojie", "🔗", "🔗", "🔗", "assets/emoji/link.png"),
    ("AST16", "Emojie", "🖊️", "🖊️", "🖊️", "assets/emoji/pen.png"),
    ("AST17", "Emojie", "📃", "📃", "📃", "assets/emoji/curved.png"),
    ("AST18", "Emojie", "🌍", "🌍", "🌍", "assets/emoji/globe.png"),
    ("AST19", "Emojie", "🎉", "🎉", "🎉", "assets/emoji/party.png"),
    ("AST20", "Fonts", "JetBrainsMono-Bold", "Command", "Monospaced face for on-screen commands", "fonts/JetBrainsMono-Bold.ttf"),
    ("AST21", "Fonts", "Inter-SemiBold", "Title", "Title face used by the Shorts stage", "fonts/Inter-SemiBold.ttf"),
    ("AST22", "Fonts", "FiraCode-Regular", "Tip", "Face for the tip card", "fonts/FiraCode-Regular.ttf"),
    ("AST23", "img", "logo-strip.png", "Brand", "YouTube logo strip placed on the hook", "img/logo-strip.png"),
    ("AST24", "img", "terminal-bg.png", "Background", "Background plate for the command card", "img/terminal-bg.png"),
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
            row = Collection(
                name=name,
                color=color,
                code=str(coll.get("id", "")),
                title=str(coll.get("title", "")),
                description=str(coll.get("description", "")),
                type=str(coll.get("type", "")),
                share_link=str(coll.get("shareLink", "")),
            )
            session.add(row)
            session.flush()
            existing[name] = row
        else:
            # keep color + Collections-sheet metadata in sync with the constants
            if existing[name].color != color:
                existing[name].color = color
            for column, key in (
                ("code", "id"),
                ("title", "title"),
                ("description", "description"),
                ("type", "type"),
                ("share_link", "shareLink"),
            ):
                value = str(coll.get(key, ""))
                if value and getattr(existing[name], column) != value:
                    setattr(existing[name], column, value)
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
    languages = _ensure_languages(session)
    _ensure_assets(session)
    seeded_episodes: list[YoutubeMain] = []

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
            shared_link=f"https://youtube.com/shorts/{_slug(f'{topic}-{episode_no}')}",
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
        seeded_episodes.append(row)
        created += 1

    _seed_library_places(session, demo_user, seeded_episodes, languages)
    session.commit()
    return created


def _slug(value: str) -> str:
    """Deterministic YouTube-style id fragment (a-z0-9 and dashes)."""
    out: list[str] = []
    for char in value.lower():
        if char.isalnum():
            out.append(char)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-") or "short"


def _ensure_languages(session: Session) -> dict[str, Language]:
    """Make sure the Languages 🌍 sheet exists (ID · Name)."""
    from app.core.constants import LANGUAGES

    existing = {row.name: row for row in session.scalars(select(Language)).all()}
    for name in LANGUAGES:
        if name not in existing:
            row = Language(name=name)
            session.add(row)
            session.flush()
            existing[name] = row
    session.flush()
    return existing


def _ensure_assets(session: Session) -> dict[str, Asset]:
    """Make sure the Assets 👁️👁️ sheet exists (Assets ID · Type · …)."""
    existing = {row.code: row for row in session.scalars(select(Asset)).all()}
    for code, kind, name, context, description, storage in _ASSETS:
        row = existing.get(code)
        if row is None:
            session.add(
                Asset(
                    code=code,
                    type=kind,
                    name=name,
                    context=context,
                    description=description,
                    storage_location=storage,
                )
            )
            session.flush()
        else:
            row.type = kind
            row.name = name
            row.context = context
            row.description = description
            row.storage_location = storage
    session.flush()
    return existing


def _seed_library_places(
    session: Session,
    user: User,
    episodes: list[YoutubeMain],
    languages: dict[str, Language],
) -> None:
    """Populate the Library places that hang off an episode.

    Scenes 🎬 · Contents 🖊️ · Subtitles 🔍 — every episode gets a scene
    breakdown, its content blocks and (when the episode declares subtitles)
    a couple of timed cues.
    """
    english = languages.get("English")
    for index, episode in enumerate(episodes):
        topic = episode.title.split(" · ")[0]
        collection = episode.collection or "General"
        scene_count = 2 + (index % 2)  # 2 or 3 scenes, deterministic
        share = max(5, episode.duration_sec // scene_count)
        plan = [
            (
                "Hook",
                f"{topic} — {episode.title.split(' · ')[-1]}.",
                "Hook On Top, YouTube Logo & Title",
                f"Why {topic} matters and what you will be able to do after this Short.",
            ),
            (
                "Command",
                f"Run the {topic} command and read the output.",
                "Terminal card, command highlighted, tip below",
                "The exact command and the one flag that changes the result.",
            ),
            (
                "Takeaway",
                "One line to remember.",
                "Outro card with the collection logo",
                f"Recap of {topic} plus a pointer to the next episode of {collection}.",
            ),
        ][:scene_count]
        for position, (title, hook, scenario, body) in enumerate(plan):
            scene = EpisodeScene(
                content_id=episode.id,
                position=position,
                duration_sec=share,
                command=topic,
                tip=f"{title}: {hook}",
                audio=bool(episode.music or episode.sound_effects),
                notes=body,
                title=title,
                hook=hook,
                scenario=scenario,
                body=body,
            )
            session.add(scene)
            session.flush()

        # Contents 🖊️ — the episode header block + one block per scene.
        blocks = [
            (
                f"{collection} | {episode.title}",
                f"{collection} collection entry for episode #{episode.episode_number}.",
                ",".join(word for word in topic.split()[:3]),
                True,
                True,
            )
        ]
        blocks.extend(
            (
                f"{title}: {hook}",
                body,
                ",".join(word for word in title.lower().split()[:3]),
                bool(episode.music),
                bool(episode.thumbnail_ready),
            )
            for title, hook, scenario, body in plan
        )
        for position, (title, description, tags, has_music, has_thumb) in enumerate(blocks):
            session.add(
                ContentItem(
                    user_id=user.id,
                    episode_id=episode.id,
                    language_id=english.id if english else None,
                    related_video_id=None,
                    code=f"CNT{position + 1}",
                    position=position,
                    title=title,
                    description=description,
                    tags=tags,
                    subtitles=episode.subtitles_count > 0,
                    pinned_comment=f"💬 Which flag do you use for {topic}?",
                    music=has_music,
                    thumbnail=has_thumb,
                )
            )

        # Subtitles 🔍 — two cues for episodes that declare subtitles.
        if episode.subtitles_count > 0:
            cues = [
                (0, share, f"{topic}"),
                (share, share * 2, "the one flag that changes everything"),
            ]
            for start, end, text in cues:
                session.add(
                    SubtitleRow(
                        user_id=user.id,
                        episode_id=episode.id,
                        language_id=english.id if english else None,
                        start_sec=start,
                        end_sec=end,
                        text=text,
                    )
                )


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
