package overlay

import (
	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/master"
	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/speed"
)

const (
	unknownValue = "unknown"
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
	SpeedActual int    `json:"speed_actual"`
}

type OpponentOverlay struct {
	DisplayName     string                `json:"display_name"`
	SpeedCandidates speed.SpeedCandidates `json:"speed_candidates"`
}

type Judgement struct {
	VsFastest      string `json:"vs_fastest"`
	VsNeutral      string `json:"vs_neutral"`
	VsScarfFastest string `json:"vs_scarf_fastest"`
	VsScarfNeutral string `json:"vs_scarf_neutral"`
}

type PreviewResponse struct {
	Player    PlayerOverlay   `json:"player"`
	Opponent  OpponentOverlay `json:"opponent"`
	Judgement Judgement       `json:"judgement"`
}

func BuildPreviewResponse(observation Observation, dex *master.Dex) PreviewResponse {
	playerName, playerSpeed := buildPlayerOverlay(observation.PlayerActive, dex)
	opponentName, opponentCandidates := buildOpponentOverlay(observation.OpponentActive, dex)

	return PreviewResponse{
		Player: PlayerOverlay{
			DisplayName: playerName,
			SpeedActual: playerSpeed,
		},
		Opponent: OpponentOverlay{
			DisplayName:     opponentName,
			SpeedCandidates: opponentCandidates,
		},
		Judgement: buildJudgement(playerSpeed, opponentCandidates),
	}
}

func buildPlayerOverlay(active ActiveObservation, dex *master.Dex) (string, int) {
	entry, ok := resolveEntry(active, dex)
	if !ok {
		return unknownValue, 0
	}

	return entry.DisplayName, speed.BuildSpeedCandidates(entry.BaseStats.Spe).Fastest
}

func buildOpponentOverlay(active ActiveObservation, dex *master.Dex) (string, speed.SpeedCandidates) {
	entry, ok := resolveEntry(active, dex)
	if !ok {
		return unknownValue, speed.SpeedCandidates{}
	}

	return entry.DisplayName, speed.BuildSpeedCandidates(entry.BaseStats.Spe)
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
