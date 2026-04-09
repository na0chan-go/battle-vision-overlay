package speed

import "testing"

func TestCalcSpeedStat(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name      string
		baseSpeed int
		ev        int
		nature    float64
		want      int
	}{
		{
			name:      "base speed 102 fastest",
			baseSpeed: 102,
			ev:        252,
			nature:    1.1,
			want:      169,
		},
		{
			name:      "base speed 102 neutral",
			baseSpeed: 102,
			ev:        252,
			nature:    1.0,
			want:      154,
		},
		{
			name:      "invalid base speed",
			baseSpeed: 0,
			ev:        252,
			nature:    1.1,
			want:      0,
		},
		{
			name:      "too large base speed",
			baseSpeed: 256,
			ev:        252,
			nature:    1.1,
			want:      0,
		},
	}

	for _, tt := range tests {
		tt := tt
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()

			got := CalcSpeedStat(tt.baseSpeed, tt.ev, tt.nature)
			if got != tt.want {
				t.Fatalf("CalcSpeedStat() = %d, want %d", got, tt.want)
			}
		})
	}
}

func TestBuildSpeedCandidates(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name      string
		baseSpeed int
		want      SpeedCandidates
	}{
		{
			name:      "base speed 102",
			baseSpeed: 102,
			want: SpeedCandidates{
				Fastest:      169,
				Neutral:      154,
				ScarfFastest: 253,
				ScarfNeutral: 231,
			},
		},
		{
			name:      "base speed 92",
			baseSpeed: 92,
			want: SpeedCandidates{
				Fastest:      158,
				Neutral:      144,
				ScarfFastest: 237,
				ScarfNeutral: 216,
			},
		},
		{
			name:      "base speed 104",
			baseSpeed: 104,
			want: SpeedCandidates{
				Fastest:      171,
				Neutral:      156,
				ScarfFastest: 256,
				ScarfNeutral: 234,
			},
		},
		{
			name:      "invalid base speed",
			baseSpeed: -1,
			want:      SpeedCandidates{},
		},
		{
			name:      "too large base speed",
			baseSpeed: 999999999,
			want:      SpeedCandidates{},
		},
	}

	for _, tt := range tests {
		tt := tt
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()

			got := BuildSpeedCandidates(tt.baseSpeed)
			if got != tt.want {
				t.Fatalf("BuildSpeedCandidates() = %+v, want %+v", got, tt.want)
			}
		})
	}
}
