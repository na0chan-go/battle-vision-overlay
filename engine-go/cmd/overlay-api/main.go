package main

import (
	"log"
	"net/http"
	"time"

	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/master"
	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/transport"
)

const defaultMasterDataPath = "../shared/master-data/pokemon.json"

func main() {
	dex, err := master.LoadDex(defaultMasterDataPath)
	if err != nil {
		log.Printf("failed to load master data from %s: %v", defaultMasterDataPath, err)
		dex = master.NewEmptyDex()
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

	log.Printf("overlay-api listening on %s", addr)
	if err := server.ListenAndServe(); err != nil {
		log.Fatal(err)
	}
}
