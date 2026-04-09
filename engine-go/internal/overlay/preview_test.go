package overlay

import (
	"testing"

	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/master"
	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/speed"
)

func TestBuildPreviewResponseKnownPokemon(t *testing.T) {
	t.Parallel()

	dex := master.NewDex(map[string]master.PokemonEntry{
		"gholdengo": {SpeciesID: "gholdengo", DisplayName: "サーフゴー", BaseSpeed: 84},
		"garchomp":  {SpeciesID: "garchomp", DisplayName: "ガブリアス", BaseSpeed: 102},
	})

	response := BuildPreviewResponse(
		Observation{
			PlayerActive: ActiveObservation{SpeciesID: "gholdengo", DisplayName: "サーフゴー"},
			OpponentActive: ActiveObservation{
				SpeciesID:   "garchomp",
				DisplayName: "ガブリアス",
			},
		},
		dex,
	)

	if response.Player.DisplayName != "サーフゴー" {
		t.Fatalf("player display name = %q, want %q", response.Player.DisplayName, "サーフゴー")
	}
	if response.Player.SpeedActual != 149 {
		t.Fatalf("player speed_actual = %d, want %d", response.Player.SpeedActual, 149)
	}

	wantCandidates := speed.SpeedCandidates{
		Fastest:      169,
		Neutral:      154,
		ScarfFastest: 253,
		ScarfNeutral: 231,
	}
	if response.Opponent.SpeedCandidates != wantCandidates {
		t.Fatalf("opponent speed candidates = %+v, want %+v", response.Opponent.SpeedCandidates, wantCandidates)
	}
	if response.Judgement.VsFastest != "lose" || response.Judgement.VsNeutral != "lose" {
		t.Fatalf("unexpected judgement = %+v", response.Judgement)
	}
}

func TestBuildPreviewResponseUnknownPokemon(t *testing.T) {
	t.Parallel()

	response := BuildPreviewResponse(
		Observation{
			PlayerActive:   ActiveObservation{SpeciesID: "unknown", DisplayName: "unknown"},
			OpponentActive: ActiveObservation{SpeciesID: "missing", DisplayName: "unknown"},
		},
		master.NewEmptyDex(),
	)

	if response.Player.SpeedActual != 0 {
		t.Fatalf("player speed_actual = %d, want 0", response.Player.SpeedActual)
	}
	if response.Opponent.SpeedCandidates != (speed.SpeedCandidates{}) {
		t.Fatalf("opponent speed candidates = %+v, want zero value", response.Opponent.SpeedCandidates)
	}
	if response.Judgement.VsFastest != "unknown" || response.Judgement.VsNeutral != "unknown" {
		t.Fatalf("unexpected judgement = %+v", response.Judgement)
	}
}
