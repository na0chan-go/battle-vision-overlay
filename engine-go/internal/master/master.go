package master

import (
	"encoding/json"
	"os"
)

const (
	UnknownValue  = "unknown"
	NormalForm    = "normal"
	BaseMegaState = "base"
)

type BaseStats struct {
	Spe int `json:"spe"`
}

type PokemonEntry struct {
	SpeciesID   string    `json:"species_id"`
	DisplayName string    `json:"display_name"`
	Gender      string    `json:"gender"`
	Form        string    `json:"form"`
	MegaState   string    `json:"mega_state"`
	BaseStats   BaseStats `json:"base_stats"`
}

type ResolveQuery struct {
	SpeciesID string
	Gender    string
	Form      string
	MegaState string
}

type Dex struct {
	entries []PokemonEntry
}

func NewDex(entries []PokemonEntry) *Dex {
	clonedEntries := make([]PokemonEntry, 0, len(entries))
	for _, entry := range entries {
		if entry.SpeciesID == "" {
			continue
		}
		clonedEntries = append(clonedEntries, normalizeEntry(entry))
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

	return NewDex(items), nil
}

func NewEmptyDex() *Dex {
	return NewDex(nil)
}

func (d *Dex) Lookup(speciesID string) (PokemonEntry, bool) {
	return d.Resolve(ResolveQuery{SpeciesID: speciesID})
}

func (d *Dex) Resolve(query ResolveQuery) (PokemonEntry, bool) {
	if d == nil {
		return PokemonEntry{}, false
	}

	query = normalizeQuery(query)
	for _, candidate := range resolveCandidates(query) {
		if entry, ok := d.find(candidate); ok {
			return entry, true
		}
	}

	return PokemonEntry{}, false
}

func (d *Dex) find(query ResolveQuery) (PokemonEntry, bool) {
	for _, entry := range d.entries {
		if entry.SpeciesID != query.SpeciesID {
			continue
		}
		if query.Gender != "" && entry.Gender != query.Gender {
			continue
		}
		if query.Form != "" && entry.Form != query.Form {
			continue
		}
		if query.MegaState != "" && entry.MegaState != query.MegaState {
			continue
		}
		return entry, true
	}

	return PokemonEntry{}, false
}

func resolveCandidates(query ResolveQuery) []ResolveQuery {
	return []ResolveQuery{
		query,
		{
			SpeciesID: query.SpeciesID,
			Gender:    UnknownValue,
			Form:      query.Form,
			MegaState: query.MegaState,
		},
		{
			SpeciesID: query.SpeciesID,
			Gender:    query.Gender,
			Form:      UnknownValue,
			MegaState: query.MegaState,
		},
		{
			SpeciesID: query.SpeciesID,
			Gender:    UnknownValue,
			Form:      UnknownValue,
			MegaState: query.MegaState,
		},
		{
			SpeciesID: query.SpeciesID,
			Gender:    UnknownValue,
			Form:      NormalForm,
			MegaState: normalizeUnknownMegaState(query.MegaState),
		},
		{
			SpeciesID: query.SpeciesID,
		},
	}
}

func normalizeEntry(entry PokemonEntry) PokemonEntry {
	entry.Gender = normalizeToken(entry.Gender, UnknownValue)
	entry.Form = normalizeToken(entry.Form, NormalForm)
	entry.MegaState = normalizeMegaState(entry.MegaState)
	return entry
}

func normalizeQuery(query ResolveQuery) ResolveQuery {
	query.Gender = normalizeToken(query.Gender, UnknownValue)
	query.Form = normalizeToken(query.Form, NormalForm)
	query.MegaState = normalizeMegaState(query.MegaState)
	return query
}

func normalizeToken(value string, fallback string) string {
	if value == "" {
		return fallback
	}
	return value
}

func normalizeMegaState(value string) string {
	if value == "" || value == UnknownValue {
		return BaseMegaState
	}
	return value
}

func normalizeUnknownMegaState(value string) string {
	if value == "" || value == UnknownValue {
		return BaseMegaState
	}
	return value
}
