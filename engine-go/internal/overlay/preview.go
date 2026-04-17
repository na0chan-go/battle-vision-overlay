package overlay

import (
	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/master"
	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/playerconfig"
	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/speed"
)

const (
	unknownValue  = "unknown"
	statusOK      = "ok"
	statusPartial = "partial"
	statusUnknown = "unknown"
)

type ActiveObservation struct {
	SpeciesID   string  `json:"species_id"`
	DisplayName string  `json:"display_name"`
	Gender      string  `json:"gender"`
	Form        string  `json:"form"`
	MegaState   string  `json:"mega_state"`
	Confidence  float64 `json:"confidence"`
}

type Observation struct {
	Scene          string            `json:"scene"`
	Timestamp      int64             `json:"timestamp"`
	PlayerActive   ActiveObservation `json:"player_active"`
	OpponentActive ActiveObservation `json:"opponent_active"`
}

type PlayerOverlay struct {
	DisplayName string `json:"display_name"`
	Gender      string `json:"gender"`
	Form        string `json:"form"`
	MegaState   string `json:"mega_state"`
	SpeedActual int    `json:"speed_actual"`
}

type OpponentOverlay struct {
	DisplayName     string                `json:"display_name"`
	Gender          string                `json:"gender"`
	Form            string                `json:"form"`
	MegaState       string                `json:"mega_state"`
	SpeedCandidates speed.SpeedCandidates `json:"speed_candidates"`
}

type Judgement struct {
	VsFastest      string `json:"vs_fastest"`
	VsNeutral      string `json:"vs_neutral"`
	VsScarfFastest string `json:"vs_scarf_fastest"`
	VsScarfNeutral string `json:"vs_scarf_neutral"`
}

type PreviewResponse struct {
	Status    string          `json:"status"`
	Message   string          `json:"message"`
	Player    PlayerOverlay   `json:"player"`
	Opponent  OpponentOverlay `json:"opponent"`
	Judgement Judgement       `json:"judgement"`
}

func BuildPreviewResponse(observation Observation, dex *master.Dex, playerSpeeds *playerconfig.SpeedSettings) PreviewResponse {
	player := buildPlayerOverlay(observation.PlayerActive, dex, playerSpeeds)
	opponent := buildOpponentOverlay(observation.OpponentActive, dex)
	status, message := buildResponseStatus(player, opponent)

	return PreviewResponse{
		Status:    status,
		Message:   message,
		Player:    player,
		Opponent:  opponent,
		Judgement: buildJudgement(player.SpeedActual, opponent.SpeedCandidates),
	}
}

func buildResponseStatus(player PlayerOverlay, opponent OpponentOverlay) (string, string) {
	playerKnown := player.DisplayName != unknownValue
	opponentKnown := opponent.DisplayName != unknownValue

	switch {
	case playerKnown && opponentKnown:
		return statusOK, ""
	case playerKnown || opponentKnown:
		return statusPartial, "player or opponent could not be resolved"
	default:
		return statusUnknown, "player and opponent could not be resolved"
	}
}

func buildPlayerOverlay(active ActiveObservation, dex *master.Dex, playerSpeeds *playerconfig.SpeedSettings) PlayerOverlay {
	entry, ok := resolveEntry(active, dex)
	if !ok {
		return PlayerOverlay{
			DisplayName: unknownValue,
			Gender:      unknownValue,
			Form:        unknownValue,
			MegaState:   unknownValue,
			SpeedActual: 0,
		}
	}

	player := PlayerOverlay{
		DisplayName: entry.DisplayName,
		Gender:      observedMetadata(active.Gender),
		Form:        observedMetadata(active.Form),
		MegaState:   observedMetadata(active.MegaState),
		SpeedActual: buildPlayerSpeedFallback(entry),
	}
	if setting, ok := resolvePlayerSpeedSetting(active, playerSpeeds); ok {
		player.SpeedActual = setting.SpeedActual
	}

	return player
}

func buildOpponentOverlay(active ActiveObservation, dex *master.Dex) OpponentOverlay {
	entry, ok := resolveEntry(active, dex)
	if !ok {
		return OpponentOverlay{
			DisplayName:     unknownValue,
			Gender:          unknownValue,
			Form:            unknownValue,
			MegaState:       unknownValue,
			SpeedCandidates: speed.SpeedCandidates{},
		}
	}

	return OpponentOverlay{
		DisplayName:     entry.DisplayName,
		Gender:          observedMetadata(active.Gender),
		Form:            observedMetadata(active.Form),
		MegaState:       observedMetadata(active.MegaState),
		SpeedCandidates: speed.BuildSpeedCandidates(entry.BaseStats.Spe),
	}
}

func buildJudgement(playerSpeed int, candidates speed.SpeedCandidates) Judgement {
	if playerSpeed <= 0 || candidates == (speed.SpeedCandidates{}) {
		return Judgement{
			VsFastest:      unknownValue,
			VsNeutral:      unknownValue,
			VsScarfFastest: unknownValue,
			VsScarfNeutral: unknownValue,
		}
	}

	return Judgement{
		VsFastest:      compareSpeed(playerSpeed, candidates.Fastest),
		VsNeutral:      compareSpeed(playerSpeed, candidates.Neutral),
		VsScarfFastest: compareSpeed(playerSpeed, candidates.ScarfFastest),
		VsScarfNeutral: compareSpeed(playerSpeed, candidates.ScarfNeutral),
	}
}

func compareSpeed(playerSpeed int, opponentSpeed int) string {
	switch {
	case playerSpeed <= 0 || opponentSpeed <= 0:
		return unknownValue
	case playerSpeed > opponentSpeed:
		return "win"
	case playerSpeed == opponentSpeed:
		return "tie"
	default:
		return "lose"
	}
}

func resolveEntry(active ActiveObservation, dex *master.Dex) (master.PokemonEntry, bool) {
	if active.SpeciesID == "" || active.SpeciesID == unknownValue {
		return master.PokemonEntry{}, false
	}

	entry, ok := dex.Resolve(master.ResolveQuery{
		SpeciesID: active.SpeciesID,
		Gender:    active.Gender,
		Form:      active.Form,
		MegaState: active.MegaState,
	})
	if !ok || !speed.IsValidBaseSpeed(entry.BaseStats.Spe) {
		return master.PokemonEntry{}, false
	}

	if entry.DisplayName == "" {
		entry.DisplayName = active.DisplayName
	}
	if entry.DisplayName == "" {
		entry.DisplayName = unknownValue
	}
	return entry, true
}

func resolvePlayerSpeedSetting(active ActiveObservation, playerSpeeds *playerconfig.SpeedSettings) (playerconfig.SpeedEntry, bool) {
	if active.SpeciesID == "" || active.SpeciesID == unknownValue {
		return playerconfig.SpeedEntry{}, false
	}

	return playerSpeeds.Resolve(playerconfig.ResolveQuery{
		SpeciesID: active.SpeciesID,
		Gender:    active.Gender,
		Form:      active.Form,
		MegaState: active.MegaState,
	})
}

func buildPlayerSpeedFallback(entry master.PokemonEntry) int {
	return speed.BuildSpeedCandidates(entry.BaseStats.Spe).Fastest
}

func observedMetadata(value string) string {
	if value == "" {
		return unknownValue
	}
	return value
}
