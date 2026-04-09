package main

import (
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/master"
	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/transport"
)

var masterDataPathCandidates = []string{
	"../shared/master-data/pokemon.json",
	"shared/master-data/pokemon.json",
}

func loadDex() (*master.Dex, string, error) {
	var lastErr error
	for _, path := range masterDataPathCandidates {
		dex, err := master.LoadDex(path)
		if err == nil {
			return dex, path, nil
		}
		lastErr = err
	}

	if lastErr == nil {
		lastErr = fmt.Errorf("no master data path candidates configured")
	}
	return nil, "", lastErr
}

func main() {
	dex, path, err := loadDex()
	if err != nil {
		log.Fatalf("failed to load master data: %v", err)
	}

	addr := ":8080"
	server := &http.Server{
		Addr:              addr,
		Handler:           transport.NewMux(dex),
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       10 * time.Second,
		WriteTimeout:      10 * time.Second,
		IdleTimeout:       30 * time.Second,
	}

	log.Printf("loaded master data from %s", path)
	log.Printf("overlay-api listening on %s", addr)
	if err := server.ListenAndServe(); err != nil {
		log.Fatal(err)
	}
}
