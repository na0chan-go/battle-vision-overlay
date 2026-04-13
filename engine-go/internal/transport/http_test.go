package transport

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/master"
	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/playerconfig"
)

func TestOverlayPreviewHandlerReturnsOverlayDTO(t *testing.T) {
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
	mux := NewMux(dex, playerSpeeds)

	requestBody := []byte(`{
		"scene":"battle",
		"timestamp":1710000000,
		"player_active":{"species_id":"gholdengo","display_name":"サーフゴー","gender":"unknown","form":"unknown","mega_state":"base","confidence":0.9},
		"opponent_active":{"species_id":"garchomp","display_name":"ガブリアス","gender":"male","form":"unknown","mega_state":"base","confidence":0.95}
	}`)
	req := httptest.NewRequest(http.MethodPost, "/api/v1/overlay/preview", bytes.NewReader(requestBody))
	rec := httptest.NewRecorder()

	mux.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d", rec.Code, http.StatusOK)
	}

	var payload struct {
		Player struct {
			DisplayName string `json:"display_name"`
			SpeedActual int    `json:"speed_actual"`
		} `json:"player"`
		Opponent struct {
			DisplayName     string `json:"display_name"`
			SpeedCandidates struct {
				Fastest      int `json:"fastest"`
				Neutral      int `json:"neutral"`
				ScarfFastest int `json:"scarf_fastest"`
				ScarfNeutral int `json:"scarf_neutral"`
			} `json:"speed_candidates"`
		} `json:"opponent"`
		Judgement struct {
			VsFastest string `json:"vs_fastest"`
		} `json:"judgement"`
	}
	if err := json.Unmarshal(rec.Body.Bytes(), &payload); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if payload.Player.SpeedActual != 123 {
		t.Fatalf("player speed_actual = %d, want %d", payload.Player.SpeedActual, 123)
	}
	if payload.Opponent.SpeedCandidates.Fastest != 169 {
		t.Fatalf("opponent fastest = %d, want %d", payload.Opponent.SpeedCandidates.Fastest, 169)
	}
	if payload.Judgement.VsFastest != "lose" {
		t.Fatalf("vs_fastest = %q, want %q", payload.Judgement.VsFastest, "lose")
	}
}

func TestOverlayPreviewHandlerReturnsUnknownForInvalidObservation(t *testing.T) {
	t.Parallel()

	mux := NewMux(master.NewEmptyDex(), playerconfig.NewEmptySpeedSettings())
	req := httptest.NewRequest(http.MethodPost, "/api/v1/overlay/preview", bytes.NewBufferString(`{`))
	rec := httptest.NewRecorder()

	mux.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d", rec.Code, http.StatusOK)
	}
	if !bytes.Contains(rec.Body.Bytes(), []byte(`"speed_actual":0`)) {
		t.Fatalf("response body = %s, want unknown response", rec.Body.String())
	}
}
