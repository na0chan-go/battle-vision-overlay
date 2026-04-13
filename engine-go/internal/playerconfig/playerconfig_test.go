package playerconfig

import (
	"testing"

	"github.com/na0chan-go/battle-vision-overlay/engine-go/internal/master"
)

func TestResolveSpeedSettings(t *testing.T) {
	t.Parallel()

	settings := NewSpeedSettings([]SpeedEntry{
		{
			SpeciesID:   "gholdengo",
			Gender:      master.UnknownValue,
			Form:        master.UnknownValue,
			MegaState:   master.BaseMegaState,
			SpeedActual: 149,
		},
		{
			SpeciesID:   "meowstic",
			Gender:      "female",
			Form:        master.NormalForm,
			MegaState:   master.BaseMegaState,
			SpeedActual: 157,
		},
		{
			SpeciesID:   "greninja",
			Gender:      master.UnknownValue,
			Form:        master.UnknownValue,
			MegaState:   master.BaseMegaState,
			SpeedActual: 191,
		},
		{
			SpeciesID:   "greninja",
			Gender:      master.UnknownValue,
			Form:        master.UnknownValue,
			MegaState:   "mega",
			SpeedActual: 202,
		},
	})

	tests := []struct {
		name   string
		query  ResolveQuery
		want   int
		wantOK bool
	}{
		{
			name: "exact species setting",
			query: ResolveQuery{
				SpeciesID: "gholdengo",
				Gender:    master.UnknownValue,
				Form:      master.NormalForm,
				MegaState: master.BaseMegaState,
			},
			want:   149,
			wantOK: true,
		},
		{
			name: "mega specific setting",
			query: ResolveQuery{
				SpeciesID: "greninja",
				Gender:    master.UnknownValue,
				Form:      master.NormalForm,
				MegaState: "mega",
			},
			want:   202,
			wantOK: true,
		},
		{
			name: "unknown gender falls back to generic",
			query: ResolveQuery{
				SpeciesID: "greninja",
				Gender:    "male",
				Form:      master.NormalForm,
				MegaState: master.BaseMegaState,
			},
			want:   191,
			wantOK: true,
		},
		{
			name: "normal form falls back to generic unknown form",
			query: ResolveQuery{
				SpeciesID: "gholdengo",
				Gender:    master.UnknownValue,
				Form:      master.NormalForm,
				MegaState: master.BaseMegaState,
			},
			want:   149,
			wantOK: true,
		},
		{
			name: "gender specific setting",
			query: ResolveQuery{
				SpeciesID: "meowstic",
				Gender:    "female",
				Form:      master.NormalForm,
				MegaState: master.BaseMegaState,
			},
			want:   157,
			wantOK: true,
		},
		{
			name: "missing variant does not fall back to species only",
			query: ResolveQuery{
				SpeciesID: "meowstic",
				Gender:    "male",
				Form:      master.NormalForm,
				MegaState: master.BaseMegaState,
			},
			wantOK: false,
		},
		{
			name: "missing species",
			query: ResolveQuery{
				SpeciesID: "missing",
				Gender:    master.UnknownValue,
				Form:      master.NormalForm,
				MegaState: master.BaseMegaState,
			},
			wantOK: false,
		},
	}

	for _, tt := range tests {
		tt := tt
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()

			got, ok := settings.Resolve(tt.query)
			if ok != tt.wantOK {
				t.Fatalf("Resolve() ok = %v, want %v", ok, tt.wantOK)
			}
			if !tt.wantOK {
				return
			}
			if got.SpeedActual != tt.want {
				t.Fatalf("Resolve() speed_actual = %d, want %d", got.SpeedActual, tt.want)
			}
		})
	}
}
