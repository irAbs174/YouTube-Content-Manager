/**
 * Library "spec places" — the workbook sheets as typed tables.
 *
 * The backend owns the authoritative column list (`GET /api/library/places`);
 * these types describe the payload shape the frontend renders.
 */

export type ColumnType = "text" | "date" | "bool" | "count" | "number" | "select";

export type PlaceKey =
  | "main"
  | "contents"
  | "scenes"
  | "episodes"
  | "collections"
  | "languages"
  | "assets"
  | "subtitles";

export interface PlaceColumn {
  key: string;
  label: string;
  type: ColumnType;
  source: string | null;
  editable: boolean;
}

export interface PlaceSpec {
  key: PlaceKey;
  title: string;
  sheet: string;
  description: string;
  columns: PlaceColumn[];
}

export interface SelectOption {
  id: number;
  label: string;
}

export interface PlaceOptions {
  episodes: SelectOption[];
  collections: SelectOption[];
  languages: SelectOption[];
  statuses: string[];
  assetTypes: string[];
  collectionTypes: string[];
}

export interface PlacesPayload {
  places: PlaceSpec[];
  options: PlaceOptions;
}

export type LibraryRow = Record<string, unknown> & { id: number };

/** Rows of the Main Library place. */
export interface MainRow {
  id: number;
  episodeId: number;
  episodeNumber: number;
  episodeDisplay: string;
  date: string;
  title: string;
  status: string;
  collectionId: number | null;
  collection: string;
  soundEffects: boolean;
  music: boolean;
  subtitlesCount: number;
  thumbnailReady: boolean;
  sharedLink: string;
}

/** Rows of the Contents place. */
export interface ContentRowItem {
  id: number;
  code: string;
  episodeId: number;
  episodeDisplay: string;
  languageId: number | null;
  language: string;
  title: string;
  description: string;
  tags: string;
  subtitles: boolean;
  relatedVideoId: number | null;
  relatedVideo: string;
  pinnedComment: string;
  music: boolean;
  thumbnail: boolean;
}

/** Rows of the Scenes place. */
export interface SceneRow {
  id: number;
  code: string;
  episodeId: number;
  episodeDisplay: string;
  sceneCount: number;
  sceneNumber: number;
  title: string;
  hook: string;
  scenario: string;
  body: string;
  durationSec: number;
}

/** Rows of the Episodes place. */
export interface EpisodeRegisterRow {
  id: number;
  episodeNumber: number;
  collectionId: number | null;
  collection: string;
  episodeDisplay: string;
  sharedLink: string;
  sceneCount: number;
}

/** Rows of the Collections place. */
export interface CollectionRow {
  id: number;
  code: string;
  name: string;
  title: string;
  description: string;
  type: string;
  shareLink: string;
  color: string;
}

/** Rows of the Languages place. */
export interface LanguageRow {
  id: number;
  name: string;
}

/** Rows of the Assets place. */
export interface AssetRow {
  id: number;
  code: string;
  type: string;
  name: string;
  context: string;
  description: string;
  storageLocation: string;
}

/** Rows of the Subtitle place. */
export interface SubtitleRow {
  id: number;
  episodeId: number;
  episodeDisplay: string;
  languageId: number | null;
  language: string;
  timeDuration: string;
  startSec: number;
  endSec: number;
  text: string;
}
