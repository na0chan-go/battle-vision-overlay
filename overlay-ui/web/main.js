const SAMPLE_SOURCES = {
  ok: "../samples/overlay_sample_ok.json",
  opponentUnknown: "../samples/overlay_sample_opponent_unknown.json",
  playerUnknown: "../samples/overlay_sample_player_unknown.json",
  unknown: "../samples/overlay_sample_unknown.json",
  error: "../samples/overlay_sample_error.json",
};
const SAMPLE_SOURCE_URL = SAMPLE_SOURCES.ok;
const UNKNOWN_VALUE = "unknown";
const UNKNOWN_NAME_LABEL = "認識失敗";
const UNAVAILABLE_LABEL = "−";
const UNKNOWN_JUDGEMENT_LABEL = "比較不可";

function createDefaultOverlayDto() {
  return {
    status: UNKNOWN_VALUE,
    message: "",
    player: {
      display_name: UNKNOWN_VALUE,
      gender: UNKNOWN_VALUE,
      form: UNKNOWN_VALUE,
      mega_state: UNKNOWN_VALUE,
      speed_actual: 0,
    },
    opponent: {
      display_name: UNKNOWN_VALUE,
      gender: UNKNOWN_VALUE,
      form: UNKNOWN_VALUE,
      mega_state: UNKNOWN_VALUE,
      speed_candidates: {
        fastest: 0,
        neutral: 0,
        scarf_fastest: 0,
        scarf_neutral: 0,
      },
    },
    judgement: {
      vs_fastest: UNKNOWN_VALUE,
      vs_neutral: UNKNOWN_VALUE,
      vs_scarf_fastest: UNKNOWN_VALUE,
      vs_scarf_neutral: UNKNOWN_VALUE,
    },
  };
}

function isPlainObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function isUnknownText(value) {
  return typeof value !== "string" || !value.trim() || value.trim() === UNKNOWN_VALUE;
}

function isKnownEntity(target) {
  return !isUnknownText(target.display_name_raw);
}

function toRawText(value) {
  return typeof value === "string" && value.trim() ? value.trim() : UNKNOWN_VALUE;
}

function toDisplayName(value) {
  return isUnknownText(value) ? UNKNOWN_NAME_LABEL : value.trim();
}

function toMetadataValue(value) {
  return typeof value === "string" && value.trim() ? value.trim() : UNKNOWN_VALUE;
}

function toDisplayNumber(value) {
  return Number.isFinite(value) ? value : 0;
}

function toJudgement(value) {
  return typeof value === "string" && value.trim() ? value.trim() : UNKNOWN_VALUE;
}

function normalizeOverlayDto(payload) {
  const fallback = createDefaultOverlayDto();
  const source = isPlainObject(payload) ? payload : fallback;
  const player = isPlainObject(source.player) ? source.player : fallback.player;
  const opponent = isPlainObject(source.opponent) ? source.opponent : fallback.opponent;
  const speedCandidates = isPlainObject(opponent.speed_candidates)
    ? opponent.speed_candidates
    : fallback.opponent.speed_candidates;
  const judgement = isPlainObject(source.judgement) ? source.judgement : fallback.judgement;
  const error = isPlainObject(source.error) ? source.error : null;

  return {
    status: toRawText(source.status),
    message: typeof source.message === "string" ? source.message.trim() : "",
    error: error
      ? {
          message: toRawText(error.message),
          detail: toRawText(error.detail),
        }
      : null,
    player: {
      display_name_raw: toRawText(player.display_name),
      display_name: toDisplayName(player.display_name),
      gender: toMetadataValue(player.gender),
      form: toMetadataValue(player.form),
      mega_state: toMetadataValue(player.mega_state),
      speed_actual: toDisplayNumber(player.speed_actual),
    },
    opponent: {
      display_name_raw: toRawText(opponent.display_name),
      display_name: toDisplayName(opponent.display_name),
      gender: toMetadataValue(opponent.gender),
      form: toMetadataValue(opponent.form),
      mega_state: toMetadataValue(opponent.mega_state),
      speed_candidates: {
        fastest: toDisplayNumber(speedCandidates.fastest),
        neutral: toDisplayNumber(speedCandidates.neutral),
        scarf_fastest: toDisplayNumber(speedCandidates.scarf_fastest),
        scarf_neutral: toDisplayNumber(speedCandidates.scarf_neutral),
      },
    },
    judgement: {
      vs_fastest: toJudgement(judgement.vs_fastest),
      vs_neutral: toJudgement(judgement.vs_neutral),
      vs_scarf_fastest: toJudgement(judgement.vs_scarf_fastest),
      vs_scarf_neutral: toJudgement(judgement.vs_scarf_neutral),
    },
    raw: payload || fallback,
  };
}

function buildMetadataChips(target) {
  const chips = [];

  if (target.gender !== UNKNOWN_VALUE) {
    chips.push(`gender: ${target.gender}`);
  }
  if (target.form !== UNKNOWN_VALUE) {
    chips.push(`form: ${target.form}`);
  }
  if (target.mega_state === "mega") {
    chips.push("mega");
  }
  if (
    target.mega_state !== UNKNOWN_VALUE &&
    target.mega_state !== "base" &&
    target.mega_state !== "mega"
  ) {
    chips.push(`mega_state: ${target.mega_state}`);
  }

  return chips;
}

function renderMetadataChips(id, target) {
  const container = document.getElementById(id);
  const chips = buildMetadataChips(target);
  container.innerHTML = "";

  if (chips.length === 0) {
    const empty = document.createElement("span");
    empty.className = "metadata-chip metadata-chip-muted";
    empty.textContent = "差分情報なし";
    container.appendChild(empty);
    return;
  }

  for (const chipText of chips) {
    const chip = document.createElement("span");
    chip.className =
      chipText === "mega" ? "metadata-chip metadata-chip-alert" : "metadata-chip";
    chip.textContent = chipText;
    container.appendChild(chip);
  }
}

function setStatus(message, variant) {
  const banner = document.getElementById("status-banner");
  banner.textContent = message;
  banner.className = `status-banner status-${variant}`;
}

function setText(id, value, className = "") {
  const element = document.getElementById(id);
  element.textContent = String(value);
  element.className = className;
}

function formatSpeed(value, isAvailable) {
  if (!isAvailable || value <= 0) {
    return UNAVAILABLE_LABEL;
  }
  return value;
}

function formatJudgement(value) {
  if (value === UNKNOWN_VALUE) {
    return UNKNOWN_JUDGEMENT_LABEL;
  }
  return value;
}

function judgementClassName(value) {
  if (value === UNKNOWN_VALUE) {
    return "value-unavailable";
  }
  return `judgement-${value}`;
}

function buildOverlayStatus(overlay) {
  if (overlay.error) {
    return {
      variant: "error",
      message: `データ取得失敗: ${overlay.error.message}`,
    };
  }
  if (overlay.status === "partial" || overlay.status === "unknown") {
    return {
      variant: "warning",
      message: overlay.message || "認識結果に不明な項目があります。",
    };
  }
  if (overlay.status === "error") {
    return {
      variant: "error",
      message: overlay.message || "データ取得失敗",
    };
  }

  const playerKnown = isKnownEntity(overlay.player);
  const opponentKnown = isKnownEntity(overlay.opponent);
  if (playerKnown && opponentKnown) {
    return { variant: "success", message: "overlay DTO を表示しています。" };
  }
  if (playerKnown || opponentKnown) {
    return {
      variant: "warning",
      message: "一部の認識結果が不明です。known 側のみ参考表示しています。",
    };
  }
  return {
    variant: "warning",
    message: "player / opponent ともに不明です。速度比較は表示できません。",
  };
}

function renderOverlayDto(payload, statusOverride = null) {
  const overlay = normalizeOverlayDto(payload);
  const textarea = document.getElementById("json-input");
  textarea.value = JSON.stringify(overlay.raw, null, 2);

  const playerKnown = isKnownEntity(overlay.player);
  const opponentKnown = isKnownEntity(overlay.opponent);

  setText(
    "opponent-display-name",
    overlay.opponent.display_name,
    opponentKnown ? "" : "value-unknown",
  );
  renderMetadataChips("opponent-metadata", overlay.opponent);
  setText(
    "opponent-fastest",
    formatSpeed(overlay.opponent.speed_candidates.fastest, opponentKnown),
    opponentKnown ? "" : "value-unavailable",
  );
  setText(
    "opponent-neutral",
    formatSpeed(overlay.opponent.speed_candidates.neutral, opponentKnown),
    opponentKnown ? "" : "value-unavailable",
  );
  setText(
    "opponent-scarf-fastest",
    formatSpeed(overlay.opponent.speed_candidates.scarf_fastest, opponentKnown),
    opponentKnown ? "" : "value-unavailable",
  );
  setText(
    "opponent-scarf-neutral",
    formatSpeed(overlay.opponent.speed_candidates.scarf_neutral, opponentKnown),
    opponentKnown ? "" : "value-unavailable",
  );

  setText(
    "player-display-name",
    overlay.player.display_name,
    playerKnown ? "" : "value-unknown",
  );
  renderMetadataChips("player-metadata", overlay.player);
  setText(
    "player-speed-actual",
    formatSpeed(overlay.player.speed_actual, playerKnown),
    playerKnown ? "" : "value-unavailable",
  );

  setText(
    "judgement-vs-fastest",
    formatJudgement(overlay.judgement.vs_fastest),
    judgementClassName(overlay.judgement.vs_fastest),
  );
  setText(
    "judgement-vs-neutral",
    formatJudgement(overlay.judgement.vs_neutral),
    judgementClassName(overlay.judgement.vs_neutral),
  );
  setText(
    "judgement-vs-scarf-fastest",
    formatJudgement(overlay.judgement.vs_scarf_fastest),
    judgementClassName(overlay.judgement.vs_scarf_fastest),
  );
  setText(
    "judgement-vs-scarf-neutral",
    formatJudgement(overlay.judgement.vs_scarf_neutral),
    judgementClassName(overlay.judgement.vs_scarf_neutral),
  );

  const status = statusOverride || buildOverlayStatus(overlay);
  setStatus(status.message, status.variant);
}

function createTransportErrorPayload(message, detail = UNKNOWN_VALUE) {
  return {
    ...createDefaultOverlayDto(),
    status: "error",
    message,
    error: {
      message,
      detail,
    },
  };
}

async function loadOverlayDtoFromUrl(sourceUrl) {
  const response = await fetch(sourceUrl, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

async function applyUrl(sourceUrl) {
  try {
    const payload = await loadOverlayDtoFromUrl(sourceUrl);
    renderOverlayDto(payload);
  } catch (error) {
    renderOverlayDto(createTransportErrorPayload("JSON の読み込みに失敗しました", error.message));
  }
}

function applyTextareaValue() {
  const textarea = document.getElementById("json-input");
  try {
    const payload = JSON.parse(textarea.value);
    renderOverlayDto(payload);
  } catch (error) {
    renderOverlayDto(createTransportErrorPayload("JSON の解析に失敗しました", error.message));
  }
}

function bindEvents() {
  const sourceUrlInput = document.getElementById("source-url-input");
  const sampleButtons = document.querySelectorAll("[data-sample-url]");
  const loadUrlButton = document.getElementById("load-url-button");
  const applyTextareaButton = document.getElementById("apply-textarea-button");

  for (const sampleButton of sampleButtons) {
    sampleButton.addEventListener("click", () => {
      const sampleUrl = sampleButton.dataset.sampleUrl;
      sourceUrlInput.value = sampleUrl;
      void applyUrl(sampleUrl);
    });
  }

  loadUrlButton.addEventListener("click", () => {
    void applyUrl(sourceUrlInput.value.trim());
  });

  applyTextareaButton.addEventListener("click", () => {
    applyTextareaValue();
  });
}

function bootstrap() {
  renderOverlayDto(createDefaultOverlayDto());
  bindEvents();
  void applyUrl(SAMPLE_SOURCE_URL);
}

bootstrap();
