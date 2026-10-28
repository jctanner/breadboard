package main

import (
	"os"
	"testing"
)

func TestGetBackend(t *testing.T) {
	// 1. Verify default domain ("local")
	os.Unsetenv("BREADBOARD_DOMAIN")
	initProxies()

	if backend := getBackend("dashboard.local"); backend == "" {
		t.Errorf("expected dashboard.local to resolve by default, got empty")
	}
	if backend := getBackend("dashboard.bb.internal"); backend != "" {
		t.Errorf("expected dashboard.bb.internal to NOT resolve by default, got %q", backend)
	}

	// 2. Verify with BREADBOARD_DOMAIN=bb.internal
	os.Setenv("BREADBOARD_DOMAIN", "bb.internal")
	initProxies()

	if backend := getBackend("dashboard.local"); backend == "" {
		t.Errorf("expected dashboard.local to resolve when BREADBOARD_DOMAIN=bb.internal, got empty")
	}
	if backend := getBackend("dashboard.bb.internal"); backend == "" {
		t.Errorf("expected dashboard.bb.internal to resolve when BREADBOARD_DOMAIN=bb.internal, got empty")
	}

	expectedBackend := "http://pipeline-dashboard.ai-pipeline.svc.cluster.local:5000"
	if backend := getBackend("dashboard.bb.internal"); backend != expectedBackend {
		t.Errorf("expected %q, got %q", expectedBackend, backend)
	}

	// Verify all other external services also resolve with bb.internal and local
	services := []string{
		"github", "jira", "dashboard", "fullsend", "mlflow", "markovd",
		"observatory", "gitlab", "orgpulse", "relay-api", "relay",
		"hooksink", "hooksink-admin",
	}
	for _, svc := range services {
		localHost := svc + ".local"
		bbHost := svc + ".bb.internal"
		if getBackend(localHost) == "" {
			t.Errorf("expected %s to resolve", localHost)
		}
		if getBackend(bbHost) == "" {
			t.Errorf("expected %s to resolve", bbHost)
		}
	}
}
