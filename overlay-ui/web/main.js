const SAMPLE_SOURCE_URL = "../samples/overlay_sample.json";

function createDefaultOverlayDto() {
  return {
    player: {
      display_name: "unknown",
      gender: "unknown",
      form: "unknown",
      mega_state: "unknown",
      speed_actual: 0,
    },
    opponent: {
      display_name: "unknown",
      gender: "unknown",
      form: "unknown",
      mega_state: "unknown",
      speed_candidates: {
        fastest: 0,
        neutral: 0,
        scarf_fastest: 0,
        scarf_neutral: 0,
      },
    },
    judgement: {
      vs_fastest: "unknown",
      vs_neutral: "unknown",
      vs_scarf_fastest: "unknown",
      vs_scarf_neutral: "unknown",
    },
  };
}

function toDisplayName(value) {
  return typeof value === "string" && value.trim() ? value : "unknown";
}

function toMetadataValue(value) {
  return typeof value === "string" && value.trim() ? value : "unknown";
}

function toDisplayNumber(value) {
  return Number.isFinite(value) ? value : 0;
}

function toJudgement(value) {
  return typeof value === "string" && value.trim() ? value : "unknown";
}

function normalizeOverlayDto(payload) {
  const fallback = createDefaultOverlayDto();
  const player = payload && typeof payload === "object" ? payload.player : null;
  const opponent = payload && typeof payload === "object" ? payload.opponent : null;
  const speedCandidates =
    opponent && typeof opponent === "object" ? opponent.speed_candidates : null;
  const judgement = payload && typeof payload === "object" ? payload.judgement : null;

  return {
    player: {
      display_name: toDisplayName(player && player.display_name),
      gender: toMetadataValue(player && player.gender),
      form: toMetadataValue(player && player.form),
      mega_state: toMetadataValue(player && player.mega_state),
      speed_actual: toDisplayNumber(player && player.speed_actual),
    },
    opponent: {
      display_name: toDisplayName(opponent && opponent.display_name),
      gender: toMetadataValue(opponent && opponent.gender),
      form: toMetadataValue(opponent && opponent.form),
      mega_state: toMetadataValue(opponent && opponent.mega_state),
      speed_candidates: {
        fastest: toDisplayNumber(speedCandidates && speedCandidates.fastest),
        neutral: toDisplayNumber(speedCandidates && speedCandidates.neutral),
        scarf_fastest: toDisplayNumber(speedCandidates && speedCandidates.scarf_fastest),
        scarf_neutral: toDisplayNumber(speedCandidates && speedCandidates.scarf_neutral),
      },
    },
    judgement: {
      vs_fastest: toJudgement(judgement && judgement.vs_fastest),
      vs_neutral: toJudgement(judgement && judgement.vs_neutral),
      vs_scarf_fastest: toJudgement(judgement && judgement.vs_scarf_fastest),
      vs_scarf_neutral: toJudgement(judgement && judgement.vs_scarf_neutral),
    },
    raw: payload || fallback,
  };
}

function buildMetadataChips(target) {
  const chips = [];

  if (target.gender !== "unknown") {
    chips.push(`gender: ${target.gender}`);
  }
  if (target.form !== "unknown") {
    chips.push(`form: ${target.form}`);
  }
  if (target.mega_state === "mega") {
    chips.push("mega");
  }
  if (
    target.mega_state !== "unknown" &&
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

function setText(id, value) {
  document.getElementById(id).textContent = String(value);
}

function renderOverlayDto(payload) {
  const overlay = normalizeOverlayDto(payload);
  const textarea = document.getElementById("json-input");
  textarea.value = JSON.stringify(overlay.raw, null, 2);

  setText("opponent-display-name", overlay.opponent.display_name);
  renderMetadataChips("opponent-metadata", overlay.opponent);
  setText("opponent-fastest", overlay.opponent.speed_candidates.fastest);
  setText("opponent-neutral", overlay.opponent.speed_candidates.neutral);
  setText("opponent-scarf-fastest", overlay.opponent.speed_candidates.scarf_fastest);
  setText("opponent-scarf-neutral", overlay.opponent.speed_candidates.scarf_neutral);

  setText("player-display-name", overlay.player.display_name);
  renderMetadataChips("player-metadata", overlay.player);
  setText("player-speed-actual", overlay.player.speed_actual);

  setText("judgement-vs-fastest", overlay.judgement.vs_fastest);
  setText("judgement-vs-neutral", overlay.judgement.vs_neutral);
  setText("judgement-vs-scarf-fastest", overlay.judgement.vs_scarf_fastest);
  setText("judgement-vs-scarf-neutral", overlay.judgement.vs_scarf_neutral);
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
    setStatus(`JSON を読み込みました: ${sourceUrl}`, "success");
  } catch (error) {
    setStatus(
      `JSON の読み込みに失敗しました: ${sourceUrl} (${error.message})`,
      "error",
    );
  }
}

function applyTextareaValue() {
  const textarea = document.getElementById("json-input");
  try {
    const payload = JSON.parse(textarea.value);
    renderOverlayDto(payload);
    setStatus("貼り付け JSON を反映しました。", "success");
  } catch (error) {
    setStatus(`JSON の解析に失敗しました: ${error.message}`, "error");
  }
}

function bindEvents() {
  const sourceUrlInput = document.getElementById("source-url-input");
  const loadSampleButton = document.getElementById("load-sample-button");
  const loadUrlButton = document.getElementById("load-url-button");
  const applyTextareaButton = document.getElementById("apply-textarea-button");

  loadSampleButton.addEventListener("click", () => {
    sourceUrlInput.value = SAMPLE_SOURCE_URL;
    void applyUrl(SAMPLE_SOURCE_URL);
  });

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
