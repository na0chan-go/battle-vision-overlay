package overlay

import (
	"testing"

	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/master"
	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/playerconfig"
	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/speed"
)

func TestBuildPreviewResponseKnownPokemon(t *testing.T) {
	t.Parallel()

	dex := master.NewDex([]master.PokemonEntry{
		{
			SpeciesID:   "gholdengo",
			DisplayName: "サーフゴー",
			Gender:      master.UnknownValue,
			Form:        master.NormalForm,
			MegaState:   master.BaseMegaState,
			BaseStats:   master.BaseStats{Spe: 84},
		},
		{
			SpeciesID:   "garchomp",
			DisplayName: "ガブリアス",
			Gender:      master.UnknownValue,
			Form:        master.NormalForm,
			MegaState:   master.BaseMegaState,
			BaseStats:   master.BaseStats{Spe: 102},
		},
	})
	playerSpeeds := playerconfig.NewSpeedSettings([]playerconfig.SpeedEntry{
		{
			SpeciesID:   "gholdengo",
			Gender:      master.UnknownValue,
			Form:        master.NormalForm,
			MegaState:   master.BaseMegaState,
			SpeedActual: 123,
		},
	})

	response := BuildPreviewResponse(
		Observation{
			PlayerActive: ActiveObservation{
				SpeciesID: "gholdengo",
				Gender:    "unknown",
				Form:      "normal",
				MegaState: "base",
			},
			OpponentActive: ActiveObservation{
				SpeciesID:   "garchomp",
				DisplayName: "ガブリアス",
				Gender:      "unknown",
				Form:        "normal",
				MegaState:   "base",
			},
		},
		dex,
		playerSpeeds,
	)

	if response.Player.DisplayName != "サーフゴー" {
		t.Fatalf("player display name = %q, want %q", response.Player.DisplayName, "サーフゴー")
	}
	if response.Player.Gender != master.UnknownValue || response.Player.Form != master.NormalForm || response.Player.MegaState != master.BaseMegaState {
		t.Fatalf("player metadata = gender:%q form:%q mega_state:%q, want unknown/normal/base", response.Player.Gender, response.Player.Form, response.Player.MegaState)
	}
	if response.Player.SpeedActual != 123 {
		t.Fatalf("player speed_actual = %d, want %d", response.Player.SpeedActual, 123)
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
	if response.Opponent.Gender != master.UnknownValue || response.Opponent.Form != master.NormalForm || response.Opponent.MegaState != master.BaseMegaState {
		t.Fatalf("opponent metadata = gender:%q form:%q mega_state:%q, want unknown/normal/base", response.Opponent.Gender, response.Opponent.Form, response.Opponent.MegaState)
	}
	if response.Judgement.VsFastest != "lose" || response.Judgement.VsNeutral != "lose" {
		t.Fatalf("unexpected judgement = %+v", response.Judgement)
	}
}

func TestBuildPreviewResponseUsesMegaEntry(t *testing.T) {
	t.Parallel()

	dex := master.NewDex([]master.PokemonEntry{
		{
			SpeciesID:   "garchomp",
			DisplayName: "ガブリアス",
			Gender:      master.UnknownValue,
			Form:        master.NormalForm,
			MegaState:   master.BaseMegaState,
			BaseStats:   master.BaseStats{Spe: 102},
		},
		{
			SpeciesID:   "garchomp",
			DisplayName: "ガブリアス",
			Gender:      master.UnknownValue,
			Form:        master.NormalForm,
			MegaState:   "mega",
			BaseStats:   master.BaseStats{Spe: 92},
		},
	})
	playerSpeeds := playerconfig.NewSpeedSettings([]playerconfig.SpeedEntry{
		{
			SpeciesID:   "garchomp",
			Gender:      master.UnknownValue,
			Form:        master.NormalForm,
			MegaState:   "mega",
			SpeedActual: 140,
		},
	})

	response := BuildPreviewResponse(
		Observation{
			PlayerActive: ActiveObservation{
				SpeciesID: "garchomp",
				Gender:    "unknown",
				Form:      "normal",
				MegaState: "mega",
			},
			OpponentActive: ActiveObservation{
				SpeciesID: "garchomp",
				Gender:    "unknown",
				Form:      "normal",
				MegaState: "mega",
			},
		},
		dex,
		playerSpeeds,
	)

	if response.Player.SpeedActual != 140 {
		t.Fatalf("player speed_actual = %d, want %d", response.Player.SpeedActual, 140)
	}
	if response.Player.MegaState != "mega" {
		t.Fatalf("player mega_state = %q, want %q", response.Player.MegaState, "mega")
	}
	if response.Opponent.SpeedCandidates.Fastest != 158 {
		t.Fatalf("opponent fastest = %d, want %d", response.Opponent.SpeedCandidates.Fastest, 158)
	}
	if response.Opponent.MegaState != "mega" {
		t.Fatalf("opponent mega_state = %q, want %q", response.Opponent.MegaState, "mega")
	}
}

func TestBuildPreviewResponseDoesNotUseBaseSettingForMissingMegaConfig(t *testing.T) {
	t.Parallel()

	dex := master.NewDex([]master.PokemonEntry{
		{
			SpeciesID:   "garchomp",
			DisplayName: "ガブリアス",
			Gender:      master.UnknownValue,
			Form:        master.NormalForm,
			MegaState:   master.BaseMegaState,
			BaseStats:   master.BaseStats{Spe: 102},
		},
		{
			SpeciesID:   "garchomp",
			DisplayName: "ガブリアス",
			Gender:      master.UnknownValue,
			Form:        master.NormalForm,
			MegaState:   "mega",
			BaseStats:   master.BaseStats{Spe: 92},
		},
	})
	playerSpeeds := playerconfig.NewSpeedSettings([]playerconfig.SpeedEntry{
		{
			SpeciesID:   "garchomp",
			Gender:      master.UnknownValue,
			Form:        master.UnknownValue,
			MegaState:   master.BaseMegaState,
			SpeedActual: 154,
		},
	})

	response := BuildPreviewResponse(
		Observation{
			PlayerActive: ActiveObservation{
				SpeciesID: "garchomp",
				Gender:    master.UnknownValue,
				Form:      master.NormalForm,
				MegaState: "mega",
			},
			OpponentActive: ActiveObservation{
				SpeciesID: "garchomp",
				Gender:    master.UnknownValue,
				Form:      master.NormalForm,
				MegaState: master.BaseMegaState,
			},
		},
		dex,
		playerSpeeds,
	)

	if response.Player.SpeedActual != 158 {
		t.Fatalf("player speed_actual = %d, want mega fastest fallback %d", response.Player.SpeedActual, 158)
	}
}

func TestBuildPreviewResponseFallsBackToFastestWithoutPlayerSetting(t *testing.T) {
	t.Parallel()

	dex := master.NewDex([]master.PokemonEntry{
		{
			SpeciesID:   "gholdengo",
			DisplayName: "サーフゴー",
			Gender:      master.UnknownValue,
			Form:        master.NormalForm,
			MegaState:   master.BaseMegaState,
			BaseStats:   master.BaseStats{Spe: 84},
		},
		{
			SpeciesID:   "garchomp",
			DisplayName: "ガブリアス",
			Gender:      master.UnknownValue,
			Form:        master.NormalForm,
			MegaState:   master.BaseMegaState,
			BaseStats:   master.BaseStats{Spe: 102},
		},
	})

	response := BuildPreviewResponse(
		Observation{
			PlayerActive: ActiveObservation{
				SpeciesID: "gholdengo",
				Gender:    master.UnknownValue,
				Form:      master.NormalForm,
				MegaState: master.BaseMegaState,
			},
			OpponentActive: ActiveObservation{
				SpeciesID: "garchomp",
				Gender:    master.UnknownValue,
				Form:      master.NormalForm,
				MegaState: master.BaseMegaState,
			},
		},
		dex,
		playerconfig.NewEmptySpeedSettings(),
	)

	if response.Player.SpeedActual != 149 {
		t.Fatalf("player speed_actual = %d, want fastest fallback %d", response.Player.SpeedActual, 149)
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
		playerconfig.NewEmptySpeedSettings(),
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
