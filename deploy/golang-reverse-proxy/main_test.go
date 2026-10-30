package main

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"net/http/httputil"
	"net/url"
	"strings"
	"testing"
	"time"
)

func mockProxy(t *testing.T, host string, tls bool, upstream http.Handler, http2 ...bool) (*httptest.Server, *http.Client) {
	t.Helper()
	backend := httptest.NewServer(upstream)
	t.Cleanup(backend.Close)
	u, err := url.Parse(backend.URL)
	if err != nil {
		t.Fatal(err)
	}
	previousHosts, previousCache, previousTransport := hostToBackend, proxyCache, sharedTransport
	transport := &http.Transport{ResponseHeaderTimeout: 150 * time.Millisecond}
	sharedTransport = transport
	hostToBackend = map[string]string{strings.ToLower(strings.Split(host, ":")[0]): backend.URL}
	proxy := httputil.NewSingleHostReverseProxy(u)
	proxy.Transport = transportForHost(host)
	proxyCache = map[string]*httputil.ReverseProxy{backend.URL: proxy}
	t.Cleanup(func() {
		proxy.Transport.(*http.Transport).CloseIdleConnections()
		transport.CloseIdleConnections()
		hostToBackend, proxyCache, sharedTransport = previousHosts, previousCache, previousTransport
	})
	server := httptest.NewUnstartedServer(http.HandlerFunc(proxyHandler))
	server.Config.WriteTimeout = 150 * time.Millisecond
	server.EnableHTTP2 = tls && len(http2) > 0 && http2[0]
	if tls {
		server.StartTLS()
	} else {
		server.Start()
	}
	t.Cleanup(server.Close)
	client := server.Client()
	client.Timeout = 3 * time.Second
	return server, client
}

func TestInferenceStreamOutlivesFrontendWriteDeadline(t *testing.T) {
	for _, protocol := range []string{"http", "https", "http2"} {
		for _, host := range []string{"relay-api.local", "RELAY-API.LOCAL:443", "model-relay.ai-pipeline.svc.cluster.local"} {
			t.Run(protocol+"/"+host, func(t *testing.T) {
				server, client := mockProxy(t, host, protocol != "http", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
					w.Header().Set("Content-Type", "text/event-stream")
					fmt.Fprint(w, "event: message_start\ndata: {}\n\n")
					w.(http.Flusher).Flush()
					select {
					case <-time.After(400 * time.Millisecond):
						fmt.Fprint(w, "event: message_stop\ndata: {}\n\n")
					case <-r.Context().Done():
					}
				}), protocol == "http2")
				req, _ := http.NewRequest(http.MethodGet, server.URL+"/v1/messages", nil)
				req.Host = host
				response, err := client.Do(req)
				if err != nil {
					t.Fatal(err)
				}
				defer response.Body.Close()
				if protocol == "http2" && response.ProtoMajor != 2 {
					t.Fatal("HTTP/2 case did not negotiate HTTP/2")
				}
				body, err := io.ReadAll(response.Body)
				if err != nil || !strings.Contains(string(body), "message_stop") {
					t.Fatalf("model stream lost its terminal event: body=%q err=%v", body, err)
				}
			})
		}
	}
}

func TestInferenceNonstreamResponseOutlivesFrontendWriteDeadline(t *testing.T) {
	for _, protocol := range []string{"http", "https", "http2"} {
		t.Run(protocol, func(t *testing.T) {
			server, client := mockProxy(t, "relay-api.local", protocol != "http", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				time.Sleep(400 * time.Millisecond)
				w.Header().Set("Content-Type", "application/json")
				fmt.Fprint(w, `{"type":"message","stop_reason":"end_turn"}`)
			}), protocol == "http2")
			req, _ := http.NewRequest(http.MethodGet, server.URL+"/v1/messages", nil)
			req.Host = "relay-api.local"
			response, err := client.Do(req)
			if err != nil {
				t.Fatal(err)
			}
			defer response.Body.Close()
			body, err := io.ReadAll(response.Body)
			if err != nil || !strings.Contains(string(body), "end_turn") {
				t.Fatalf("long model response was cut off: body=%q err=%v", body, err)
			}
		})
	}
}

func TestConsoleRetainsFrontendWriteDeadline(t *testing.T) {
	server, client := mockProxy(t, "relay.local", false, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/event-stream")
		fmt.Fprint(w, "started\n")
		w.(http.Flusher).Flush()
		time.Sleep(400 * time.Millisecond)
		fmt.Fprint(w, "finished\n")
	}))
	req, _ := http.NewRequest(http.MethodGet, server.URL+"/", nil)
	req.Host = "relay.local"
	response, err := client.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer response.Body.Close()
	body, err := io.ReadAll(response.Body)
	if err == nil || strings.Contains(string(body), "finished") {
		t.Fatalf("ordinary console deadline unexpectedly removed: body=%q err=%v", body, err)
	}
}

func TestInferenceClientCancellationReachesUpstream(t *testing.T) {
	cancelled := make(chan struct{})
	server, client := mockProxy(t, "relay-api.local", false, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/event-stream")
		fmt.Fprint(w, "started\n")
		w.(http.Flusher).Flush()
		<-r.Context().Done()
		close(cancelled)
	}))
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	req, _ := http.NewRequestWithContext(ctx, http.MethodGet, server.URL+"/v1/messages", nil)
	req.Host = "relay-api.local"
	response, err := client.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer response.Body.Close()
	cancel()
	select {
	case <-cancelled:
	case <-time.After(time.Second):
		t.Fatal("cancelled client left the upstream model request running")
	}
}
