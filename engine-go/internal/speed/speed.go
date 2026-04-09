package speed

import "math"

const (
	level        = 50
	fixedIV      = 31
	maxSpeedEV   = 252
	natureFast   = 1.1
	natureNormal = 1.0
	scarfScale   = 1.5
)

type BaseStats struct {
	HP  int
	Atk int
	Def int
	SpA int
	SpD int
	Spe int
}

type SpeedCandidates struct {
	Fastest      int `json:"fastest"`
	Neutral      int `json:"neutral"`
	ScarfFastest int `json:"scarf_fastest"`
	ScarfNeutral int `json:"scarf_neutral"`
}

func CalcSpeedStat(baseSpeed int, ev int, nature float64) int {
	if baseSpeed <= 0 || ev < 0 || nature <= 0 {
		return 0
	}

	baseValue := math.Floor(float64((baseSpeed*2+fixedIV+ev/4)*level) / 100.0)
	return int(math.Floor((baseValue + 5) * nature))
}

func BuildSpeedCandidates(baseSpeed int) SpeedCandidates {
	if baseSpeed <= 0 {
		return SpeedCandidates{}
	}

	fastest := CalcSpeedStat(baseSpeed, maxSpeedEV, natureFast)
	neutral := CalcSpeedStat(baseSpeed, maxSpeedEV, natureNormal)

	return SpeedCandidates{
		Fastest:      fastest,
		Neutral:      neutral,
		ScarfFastest: applyScarf(fastest),
		ScarfNeutral: applyScarf(neutral),
	}
}

func applyScarf(speed int) int {
	if speed <= 0 {
		return 0
	}

	return int(math.Floor(float64(speed) * scarfScale))
}
