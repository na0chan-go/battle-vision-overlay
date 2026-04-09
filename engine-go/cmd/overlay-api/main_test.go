package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoadDexUsesFirstAvailableCandidate(t *testing.T) {
	t.Parallel()

	originalCandidates := masterDataPathCandidates
	t.Cleanup(func() {
		masterDataPathCandidates = originalCandidates
	})

	tmpDir := t.TempDir()
	masterDataPath := filepath.Join(tmpDir, "pokemon.json")
	payload := `[{"species_id":"garchomp","display_name":"ガブリアス","base_speed":102}]`
	if err := os.WriteFile(masterDataPath, []byte(payload), 0o644); err != nil {
		t.Fatalf("failed to write temp master data: %v", err)
	}

	masterDataPathCandidates = []string{
		filepath.Join(tmpDir, "missing.json"),
		masterDataPath,
	}

	dex, path, err := loadDex()
	if err != nil {
		t.Fatalf("loadDex() returned error: %v", err)
	}
	if path != masterDataPath {
		t.Fatalf("loadDex() path = %q, want %q", path, masterDataPath)
	}
	if _, ok := dex.Lookup("garchomp"); !ok {
		t.Fatal("loadDex() did not load expected species")
	}
}

func TestLoadDexReturnsErrorWhenAllCandidatesFail(t *testing.T) {
	t.Parallel()

	originalCandidates := masterDataPathCandidates
	t.Cleanup(func() {
		masterDataPathCandidates = originalCandidates
	})

	masterDataPathCandidates = []string{
		filepath.Join(t.TempDir(), "missing.json"),
	}

	if _, _, err := loadDex(); err == nil {
		t.Fatal("loadDex() error = nil, want non-nil")
	}
}
