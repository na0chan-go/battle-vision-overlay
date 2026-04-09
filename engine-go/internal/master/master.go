package master

import (
	"encoding/json"
	"os"
)

type PokemonEntry struct {
	SpeciesID   string `json:"species_id"`
	DisplayName string `json:"display_name"`
	BaseSpeed   int    `json:"base_speed"`
}

type Dex struct {
	entries map[string]PokemonEntry
}

func NewDex(entries map[string]PokemonEntry) *Dex {
	clonedEntries := make(map[string]PokemonEntry, len(entries))
	for speciesID, entry := range entries {
		if speciesID == "" {
			continue
		}
		clonedEntries[speciesID] = entry
	}

	return &Dex{entries: clonedEntries}
}

func LoadDex(path string) (*Dex, error) {
	payload, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var items []PokemonEntry
	if err := json.Unmarshal(payload, &items); err != nil {
		return nil, err
	}

	entries := make(map[string]PokemonEntry, len(items))
	for _, item := range items {
		if item.SpeciesID == "" {
			continue
		}
		entries[item.SpeciesID] = item
	}

	return &Dex{entries: entries}, nil
}

func NewEmptyDex() *Dex {
	return NewDex(map[string]PokemonEntry{})
}

func (d *Dex) Lookup(speciesID string) (PokemonEntry, bool) {
	if d == nil {
		return PokemonEntry{}, false
	}

	entry, ok := d.entries[speciesID]
	return entry, ok
}
