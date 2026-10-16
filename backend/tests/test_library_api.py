"""Library "spec places" — the workbook sheets exposed as editable tables."""

from __future__ import annotations

from fastapi.testclient import TestClient

PLACES = [
    "main",
    "contents",
    "scenes",
    "episodes",
    "collections",
    "languages",
    "assets",
    "subtitles",
]


def test_every_place_returns_rows(client: TestClient):
    for key in PLACES:
        response = client.get(f"/api/library/{key}")
        assert response.status_code == 200, key
        body = response.json()
        assert isinstance(body, list)
        assert body, f"{key} is empty"


def test_main_place_mirrors_the_workbook_columns(client: TestClient):
    rows = client.get("/api/library/main").json()
    row = rows[0]
    assert set(row) >= {
        "episodeId",
        "date",
        "title",
        "status",
        "collectionId",
        "soundEffects",
        "music",
        "subtitlesCount",
        "thumbnailReady",
    }
    assert row["status"] in ("Public", "Schedule", "Private", "Draft", "Not List")
    assert isinstance(row["soundEffects"], bool)
    assert isinstance(row["music"], bool)
    assert isinstance(row["thumbnailReady"], bool)
    assert isinstance(row["subtitlesCount"], int)


def test_main_place_status_select_accepts_every_status(client: TestClient):
    row = client.get("/api/library/main").json()[0]
    for status in ("Public", "Schedule", "Private", "Draft", "Not List"):
        response = client.patch(f"/api/library/main/{row['id']}", json={"status": status})
        assert response.status_code == 200, status
        assert response.json()["status"] == status


def test_main_place_rejects_unknown_status(client: TestClient):
    row = client.get("/api/library/main").json()[0]
    response = client.patch(f"/api/library/main/{row['id']}", json={"status": "Nope"})
    assert response.status_code == 400
    assert "status" in response.json()["error"]


def test_main_place_toggles_booleans_and_collection(client: TestClient):
    rows = client.get("/api/library/main").json()
    row = rows[0]
    collections = client.get("/api/library/collections").json()

    response = client.patch(
        f"/api/library/main/{row['id']}",
        json={
            "soundEffects": False,
            "music": True,
            "thumbnailReady": False,
            "collectionId": collections[0]["id"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["soundEffects"] is False
    assert body["music"] is True
    assert body["thumbnailReady"] is False
    assert body["collectionId"] == collections[0]["id"]
    assert body["collection"] == collections[0]["name"]


def test_main_place_rejects_unknown_field(client: TestClient):
    row = client.get("/api/library/main").json()[0]
    response = client.patch(f"/api/library/main/{row['id']}", json={"nope": 1})
    assert response.status_code == 400


def test_contents_place_rows_carry_their_selects(client: TestClient):
    rows = client.get("/api/library/contents").json()
    row = rows[0]
    assert row["code"].startswith("CNT")
    assert row["episodeId"]
    assert row["episodeDisplay"]
    assert row["language"]
    assert isinstance(row["subtitles"], bool)
    assert isinstance(row["music"], bool)
    assert isinstance(row["thumbnail"], bool)


def test_contents_place_reassigns_its_episode(client: TestClient):
    contents = client.get("/api/library/contents").json()
    episodes = client.get("/api/library/main").json()
    target = episodes[0]["id"]
    response = client.patch(
        f"/api/library/contents/{contents[0]['id']}", json={"episodeId": target}
    )
    assert response.status_code == 200
    assert response.json()["episodeId"] == target


def test_scenes_place_counts_scenes_per_episode(client: TestClient):
    rows = client.get("/api/library/scenes").json()
    row = rows[0]
    assert row["code"].startswith("SCN")
    assert row["sceneCount"] >= row["sceneNumber"]
    assert row["title"]
    assert row["hook"]
    assert row["scenario"]
    assert row["body"]


def test_scenes_place_patch_updates_the_script_fields(client: TestClient):
    scene = client.get("/api/library/scenes").json()[0]
    response = client.patch(
        f"/api/library/scenes/{scene['id']}",
        json={"title": "New title", "hook": "New hook", "scenario": "New scenario", "body": "New body"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "New title"
    assert body["hook"] == "New hook"
    assert body["scenario"] == "New scenario"
    assert body["body"] == "New body"


def test_episodes_place_lists_the_register(client: TestClient):
    rows = client.get("/api/library/episodes").json()
    row = rows[0]
    assert isinstance(row["episodeNumber"], int)
    assert row["collection"]
    assert row["episodeDisplay"]
    assert row["sharedLink"].startswith("https://")
    assert isinstance(row["sceneCount"], int)


def test_episodes_place_patches_number_collection_and_link(client: TestClient):
    row = client.get("/api/library/episodes").json()[0]
    collections = client.get("/api/library/collections").json()
    response = client.patch(
        f"/api/library/episodes/{row['id']}",
        json={
            "episodeNumber": 99,
            "collectionId": collections[-1]["id"],
            "sharedLink": "https://youtube.com/shorts/abc",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["episodeNumber"] == 99
    assert body["collectionId"] == collections[-1]["id"]
    assert body["sharedLink"] == "https://youtube.com/shorts/abc"


def test_collections_place_has_the_sheet_metadata(client: TestClient):
    rows = client.get("/api/library/collections").json()
    row = rows[0]
    assert set(row) >= {"id", "code", "name", "title", "description", "type", "shareLink"}
    assert row["code"].startswith("COLL")
    assert row["type"] in ("course", "Play List", "Series", "Single")
    assert row["shareLink"].startswith("https://")


def test_languages_place_and_creation(client: TestClient):
    rows = client.get("/api/library/languages").json()
    assert rows[0]["name"] == "English"
    assert all(isinstance(row["id"], int) for row in rows)

    response = client.post("/api/library/languages", json={"name": "Klingon"})
    assert response.status_code == 201
    assert response.json()["name"] == "Klingon"
    # duplicates are rejected
    assert client.post("/api/library/languages", json={"name": "Klingon"}).status_code == 400


def test_assets_place_and_creation(client: TestClient):
    rows = client.get("/api/library/assets").json()
    assert rows[0]["code"].startswith("AST")
    assert rows[0]["type"]
    assert rows[0]["storageLocation"]

    response = client.post(
        "/api/library/assets",
        json={"code": "ASTX", "type": "img", "name": "logo.png", "storageLocation": "img/logo.png"},
    )
    assert response.status_code == 201
    assert response.json()["code"] == "ASTX"


def test_subtitles_place_reports_the_time_duration(client: TestClient):
    rows = client.get("/api/library/subtitles").json()
    row = rows[0]
    assert row["episodeId"]
    assert row["language"]
    assert "–" in row["timeDuration"]
    assert row["text"]


def test_subtitles_place_creation_updates_the_main_counter(client: TestClient):
    episodes = client.get("/api/library/main").json()
    episode = episodes[0]
    before = episode["subtitlesCount"]
    response = client.post(
        "/api/library/subtitles",
        json={
            "episodeId": episode["id"],
            "languageId": 1,
            "startSec": 0,
            "endSec": 5,
            "text": "hello",
        },
    )
    assert response.status_code == 201
    assert response.json()["text"] == "hello"

    refreshed = client.get("/api/library/main").json()
    updated = next(row for row in refreshed if row["id"] == episode["id"])
    assert updated["subtitlesCount"] == before + 1


def test_subtitles_place_patch_edits_the_cue(client: TestClient):
    cue = client.get("/api/library/subtitles").json()[0]
    response = client.patch(
        f"/api/library/subtitles/{cue['id']}",
        json={"startSec": 3, "endSec": 9, "text": "edited cue"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["startSec"] == 3
    assert body["endSec"] == 9
    assert body["text"] == "edited cue"


def test_contents_place_creation(client: TestClient):
    episode = client.get("/api/library/main").json()[0]
    response = client.post(
        "/api/library/contents",
        json={
            "episodeId": episode["id"],
            "languageId": 1,
            "title": "New content block",
            "description": "Body",
            "tags": "a,b",
            "subtitles": True,
            "music": False,
            "thumbnail": True,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "New content block"
    assert body["episodeId"] == episode["id"]
    assert body["code"].startswith("CNT")


def test_collections_place_creation(client: TestClient):
    response = client.post(
        "/api/library/collections",
        json={"name": "Brand New", "title": "BN", "type": "course", "shareLink": "https://x.test"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Brand New"
    assert body["code"].startswith("COLL")


def test_places_are_scoped_per_user(client: TestClient):
    """A second account never sees the demo user's rows."""
    assert client.post(
        "/api/auth/register",
        json={"email": "second@ytcm.test", "password": "password-1234"},
    ).status_code in (200, 201)
    rows = client.get("/api/library/main").json()
    assert rows == []


def test_unknown_row_is_404(client: TestClient):
    assert client.patch("/api/library/main/999999", json={"title": "x"}).status_code == 404
    assert client.patch("/api/library/contents/999999", json={"title": "x"}).status_code == 404
    assert client.patch("/api/library/assets/999999", json={"name": "x"}).status_code == 404


def test_subtitles_place_edits_the_time_duration_range(client: TestClient):
    """The `Time duration` cell is a range — editing it moves the cue."""
    cue = client.get("/api/library/subtitles").json()[0]
    response = client.patch(
        f"/api/library/subtitles/{cue['id']}", json={"timeDuration": "00:12–00:27"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["startSec"] == 12
    assert body["endSec"] == 27
    assert body["timeDuration"] == "00:12–00:27"


def test_subtitles_place_rejects_a_broken_time_duration(client: TestClient):
    cue = client.get("/api/library/subtitles").json()[0]
    response = client.patch(
        f"/api/library/subtitles/{cue['id']}", json={"timeDuration": "not-a-time"}
    )
    assert response.status_code == 400


def test_main_place_records_the_schedule_moment(client: TestClient):
    row = client.get("/api/library/main").json()[0]
    response = client.patch(
        f"/api/library/main/{row['id']}",
        json={"status": "Schedule", "scheduleAt": "2026-12-24T18:30:00"},
    )
    assert response.status_code == 200
    assert response.json()["scheduleAt"].startswith("2026-12-24T18:30")
