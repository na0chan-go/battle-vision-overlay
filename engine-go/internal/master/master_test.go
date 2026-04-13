package master

import "testing"

func TestResolvePokemonEntry(t *testing.T) {
	t.Parallel()

	dex := NewDex([]PokemonEntry{
		{
			SpeciesID:   "garchomp",
			DisplayName: "ガブリアス",
			Gender:      UnknownValue,
			Form:        NormalForm,
			MegaState:   BaseMegaState,
			BaseStats:   BaseStats{Spe: 102},
		},
		{
			SpeciesID:   "garchomp",
			DisplayName: "ガブリアス",
			Gender:      UnknownValue,
			Form:        NormalForm,
			MegaState:   "mega",
			BaseStats:   BaseStats{Spe: 92},
		},
		{
			SpeciesID:   "meowstic",
			DisplayName: "ニャオニクス",
			Gender:      "male",
			Form:        NormalForm,
			MegaState:   BaseMegaState,
			BaseStats:   BaseStats{Spe: 104},
		},
		{
			SpeciesID:   "meowstic",
			DisplayName: "ニャオニクス",
			Gender:      "female",
			Form:        NormalForm,
			MegaState:   BaseMegaState,
			BaseStats:   BaseStats{Spe: 104},
		},
		{
			SpeciesID:   "basculegion",
			DisplayName: "イダイトウ",
			Gender:      "male",
			Form:        NormalForm,
			MegaState:   BaseMegaState,
			BaseStats:   BaseStats{Spe: 78},
		},
		{
			SpeciesID:   "basculegion",
			DisplayName: "イダイトウ",
			Gender:      "female",
			Form:        NormalForm,
			MegaState:   BaseMegaState,
			BaseStats:   BaseStats{Spe: 78},
		},
		{
			SpeciesID:   "greninja",
			DisplayName: "ゲッコウガ",
			Gender:      UnknownValue,
			Form:        NormalForm,
			MegaState:   BaseMegaState,
			BaseStats:   BaseStats{Spe: 122},
		},
		{
			SpeciesID:   "greninja",
			DisplayName: "ゲッコウガ",
			Gender:      UnknownValue,
			Form:        NormalForm,
			MegaState:   "mega",
			BaseStats:   BaseStats{Spe: 132},
		},
		{
			SpeciesID:   "excadrill",
			DisplayName: "ドリュウズ",
			Gender:      UnknownValue,
			Form:        NormalForm,
			MegaState:   BaseMegaState,
			BaseStats:   BaseStats{Spe: 88},
		},
	})

	tests := []struct {
		name       string
		query      ResolveQuery
		wantSpe    int
		wantGender string
		wantMega   string
		wantOK     bool
	}{
		{
			name: "garchomp base",
			query: ResolveQuery{
				SpeciesID: "garchomp",
				Gender:    UnknownValue,
				Form:      NormalForm,
				MegaState: BaseMegaState,
			},
			wantSpe:    102,
			wantGender: UnknownValue,
			wantMega:   BaseMegaState,
			wantOK:     true,
		},
		{
			name: "garchomp mega",
			query: ResolveQuery{
				SpeciesID: "garchomp",
				Gender:    UnknownValue,
				Form:      NormalForm,
				MegaState: "mega",
			},
			wantSpe:    92,
			wantGender: UnknownValue,
			wantMega:   "mega",
			wantOK:     true,
		},
		{
			name: "meowstic male",
			query: ResolveQuery{
				SpeciesID: "meowstic",
				Gender:    "male",
				Form:      NormalForm,
				MegaState: BaseMegaState,
			},
			wantSpe:    104,
			wantGender: "male",
			wantMega:   BaseMegaState,
			wantOK:     true,
		},
		{
			name: "meowstic female",
			query: ResolveQuery{
				SpeciesID: "meowstic",
				Gender:    "female",
				Form:      NormalForm,
				MegaState: BaseMegaState,
			},
			wantSpe:    104,
			wantGender: "female",
			wantMega:   BaseMegaState,
			wantOK:     true,
		},
		{
			name: "meowstic female unknown form falls back to female normal",
			query: ResolveQuery{
				SpeciesID: "meowstic",
				Gender:    "female",
				Form:      UnknownValue,
				MegaState: BaseMegaState,
			},
			wantSpe:    104,
			wantGender: "female",
			wantMega:   BaseMegaState,
			wantOK:     true,
		},
		{
			name: "basculegion female",
			query: ResolveQuery{
				SpeciesID: "basculegion",
				Gender:    "female",
				Form:      NormalForm,
				MegaState: BaseMegaState,
			},
			wantSpe:    78,
			wantGender: "female",
			wantMega:   BaseMegaState,
			wantOK:     true,
		},
		{
			name: "excadrill generic",
			query: ResolveQuery{
				SpeciesID: "excadrill",
				Gender:    UnknownValue,
				Form:      NormalForm,
				MegaState: BaseMegaState,
			},
			wantSpe:    88,
			wantGender: UnknownValue,
			wantMega:   BaseMegaState,
			wantOK:     true,
		},
		{
			name: "greninja base",
			query: ResolveQuery{
				SpeciesID: "greninja",
				Gender:    UnknownValue,
				Form:      NormalForm,
				MegaState: BaseMegaState,
			},
			wantSpe:    122,
			wantGender: UnknownValue,
			wantMega:   BaseMegaState,
			wantOK:     true,
		},
		{
			name: "greninja mega",
			query: ResolveQuery{
				SpeciesID: "greninja",
				Gender:    UnknownValue,
				Form:      NormalForm,
				MegaState: "mega",
			},
			wantSpe:    132,
			wantGender: UnknownValue,
			wantMega:   "mega",
			wantOK:     true,
		},
		{
			name: "unknown gender falls back to generic entry",
			query: ResolveQuery{
				SpeciesID: "garchomp",
				Gender:    "male",
				Form:      NormalForm,
				MegaState: BaseMegaState,
			},
			wantSpe:    102,
			wantGender: UnknownValue,
			wantMega:   BaseMegaState,
			wantOK:     true,
		},
		{
			name: "unknown mega state prefers base",
			query: ResolveQuery{
				SpeciesID: "greninja",
				Gender:    UnknownValue,
				Form:      NormalForm,
				MegaState: UnknownValue,
			},
			wantSpe:    122,
			wantGender: UnknownValue,
			wantMega:   BaseMegaState,
			wantOK:     true,
		},
		{
			name: "missing species",
			query: ResolveQuery{
				SpeciesID: "missing",
				Gender:    UnknownValue,
				Form:      NormalForm,
				MegaState: BaseMegaState,
			},
			wantOK: false,
		},
	}

	for _, tt := range tests {
		tt := tt
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()

			got, ok := dex.Resolve(tt.query)
			if ok != tt.wantOK {
				t.Fatalf("Resolve() ok = %v, want %v", ok, tt.wantOK)
			}
			if !tt.wantOK {
				return
			}
			if got.BaseStats.Spe != tt.wantSpe {
				t.Fatalf("Resolve() spe = %d, want %d", got.BaseStats.Spe, tt.wantSpe)
			}
			if got.Gender != tt.wantGender {
				t.Fatalf("Resolve() gender = %q, want %q", got.Gender, tt.wantGender)
			}
			if got.MegaState != tt.wantMega {
				t.Fatalf("Resolve() mega_state = %q, want %q", got.MegaState, tt.wantMega)
			}
		})
	}
}
