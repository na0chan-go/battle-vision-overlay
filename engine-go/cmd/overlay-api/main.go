package main

import (
	"bytes"
	"encoding/json"
	"log"
	"net/http"
	"strconv"
	"time"

	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/speed"
)

type healthResponse struct {
	Status string `json:"status"`
}

type speedTestResponse struct {
	BaseSpeed       int                   `json:"base_speed"`
	SpeedCandidates speed.SpeedCandidates `json:"speed_candidates"`
}

func healthzHandler(w http.ResponseWriter, _ *http.Request) {
	var body bytes.Buffer
	if err := json.NewEncoder(&body).Encode(healthResponse{Status: "ok"}); err != nil {
		http.Error(w, `{"status":"error"}`, http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(body.Bytes())
}

func speedTestHandler(w http.ResponseWriter, r *http.Request) {
	baseSpeedText := r.URL.Query().Get("base_speed")
	baseSpeed, err := strconv.Atoi(baseSpeedText)
	if err != nil || baseSpeed <= 0 {
		http.Error(w, `{"error":"base_speed must be a positive integer"}`, http.StatusBadRequest)
		return
	}

	response := speedTestResponse{
		BaseSpeed:       baseSpeed,
		SpeedCandidates: speed.BuildSpeedCandidates(baseSpeed),
	}

	var body bytes.Buffer
	if err := json.NewEncoder(&body).Encode(response); err != nil {
		http.Error(w, `{"error":"failed to encode response"}`, http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(body.Bytes())
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", healthzHandler)
	mux.HandleFunc("/speed-test", speedTestHandler)

	addr := ":8080"
	server := &http.Server{
		Addr:              addr,
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       10 * time.Second,
		WriteTimeout:      10 * time.Second,
		IdleTimeout:       30 * time.Second,
	}

	log.Printf("overlay-api listening on %s", addr)
	if err := server.ListenAndServe(); err != nil {
		log.Fatal(err)
	}
}
