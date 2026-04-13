package transport

import (
	"bytes"
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/master"
	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/overlay"
	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/playerconfig"
	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/speed"
)

type healthResponse struct {
	Status string `json:"status"`
}

type speedTestResponse struct {
	BaseSpeed       int                   `json:"base_speed"`
	SpeedCandidates speed.SpeedCandidates `json:"speed_candidates"`
}

func NewMux(dex *master.Dex, playerSpeeds *playerconfig.SpeedSettings) *http.ServeMux {
	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", healthzHandler)
	mux.HandleFunc("/speed-test", speedTestHandler)
	mux.HandleFunc("/api/v1/overlay/preview", overlayPreviewHandler(dex, playerSpeeds))
	return mux
}

func healthzHandler(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, healthResponse{Status: "ok"})
}

func speedTestHandler(w http.ResponseWriter, r *http.Request) {
	baseSpeedText := r.URL.Query().Get("base_speed")
	baseSpeed, err := strconv.Atoi(baseSpeedText)
	if err != nil || !speed.IsValidBaseSpeed(baseSpeed) {
		http.Error(w, `{"error":"base_speed must be an integer between 1 and 255"}`, http.StatusBadRequest)
		return
	}

	writeJSON(w, http.StatusOK, speedTestResponse{
		BaseSpeed:       baseSpeed,
		SpeedCandidates: speed.BuildSpeedCandidates(baseSpeed),
	})
}

func overlayPreviewHandler(dex *master.Dex, playerSpeeds *playerconfig.SpeedSettings) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, `{"error":"method not allowed"}`, http.StatusMethodNotAllowed)
			return
		}

		var observationDTO overlay.Observation
		if err := json.NewDecoder(r.Body).Decode(&observationDTO); err != nil {
			writeJSON(w, http.StatusOK, overlay.BuildPreviewResponse(overlay.Observation{}, dex, playerSpeeds))
			return
		}

		writeJSON(w, http.StatusOK, overlay.BuildPreviewResponse(observationDTO, dex, playerSpeeds))
	}
}

func writeJSON(w http.ResponseWriter, statusCode int, payload any) {
	var body bytes.Buffer
	if err := json.NewEncoder(&body).Encode(payload); err != nil {
		http.Error(w, `{"error":"failed to encode response"}`, http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	_, _ = w.Write(body.Bytes())
}
