package playerconfig

import (
	"encoding/json"
	"os"

	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/master"
)

type SpeedEntry struct {
	SpeciesID   string `json:"species_id"`
	Gender      string `json:"gender"`
	Form        string `json:"form"`
	MegaState   string `json:"mega_state"`
	SpeedActual int    `json:"speed_actual"`
}

type ResolveQuery struct {
	SpeciesID string
	Gender    string
	Form      string
	MegaState string
}

type SpeedSettings struct {
	entries []SpeedEntry
}

func NewSpeedSettings(entries []SpeedEntry) *SpeedSettings {
	clonedEntries := make([]SpeedEntry, 0, len(entries))
	for _, entry := range entries {
		if entry.SpeciesID == "" || entry.SpeedActual <= 0 {
			continue
		}
		clonedEntries = append(clonedEntries, normalizeEntry(entry))
	}

	return &SpeedSettings{entries: clonedEntries}
}

func LoadSpeedSettings(path string) (*SpeedSettings, error) {
	payload, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var items []SpeedEntry
	if err := json.Unmarshal(payload, &items); err != nil {
		return nil, err
	}

	return NewSpeedSettings(items), nil
}

func NewEmptySpeedSettings() *SpeedSettings {
	return NewSpeedSettings(nil)
}

func (s *SpeedSettings) Resolve(query ResolveQuery) (SpeedEntry, bool) {
	if s == nil {
		return SpeedEntry{}, false
	}

	query = normalizeQuery(query)
	for _, candidate := range resolveCandidates(query) {
		if entry, ok := s.find(candidate); ok {
			return entry, true
		}
	}

	return SpeedEntry{}, false
}

func (s *SpeedSettings) find(query ResolveQuery) (SpeedEntry, bool) {
	for _, entry := range s.entries {
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

	return SpeedEntry{}, false
}

func resolveCandidates(query ResolveQuery) []ResolveQuery {
	return []ResolveQuery{
		query,
		{
			SpeciesID: query.SpeciesID,
			Gender:    master.UnknownValue,
			Form:      query.Form,
			MegaState: query.MegaState,
		},
		{
			SpeciesID: query.SpeciesID,
			Gender:    query.Gender,
			Form:      master.UnknownValue,
			MegaState: query.MegaState,
		},
		{
			SpeciesID: query.SpeciesID,
			Gender:    master.UnknownValue,
			Form:      master.UnknownValue,
			MegaState: query.MegaState,
		},
	}
}

func normalizeEntry(entry SpeedEntry) SpeedEntry {
	entry.Gender = normalizeToken(entry.Gender, master.UnknownValue)
	entry.Form = normalizeToken(entry.Form, master.UnknownValue)
	entry.MegaState = normalizeMegaState(entry.MegaState)
	return entry
}

func normalizeQuery(query ResolveQuery) ResolveQuery {
	query.Gender = normalizeToken(query.Gender, master.UnknownValue)
	query.Form = normalizeToken(query.Form, master.UnknownValue)
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
	if value == "" || value == master.UnknownValue {
		return master.BaseMegaState
	}
	return value
}
