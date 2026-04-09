setup:
	@echo "bootstrap repository: no extra setup steps yet"

run-go:
	cd engine-go && go run ./cmd/overlay-api

test-go:
	cd engine-go && go test ./...

fmt-go:
	cd engine-go && gofmt -w ./cmd ./internal ./pkg ./tests
