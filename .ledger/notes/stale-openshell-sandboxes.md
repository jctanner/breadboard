# Stale OpenShell sandboxes removed 2026-09-22

Six sandboxes predating the current integration were removed. Nothing in the
repository created them and nothing could reference them: Fullsend generates
every sandbox name itself as `fs-<slug>-<hex>` from PID, nanosecond timestamp
and a counter (`generateSandboxName`, internal/cli/run.go), so neither
`agent-review-*` nor `net-*` is a name the current code can produce.

They were not inert. `agent-review-ca597` held a reference to the
`fullsend-vertex-ai` provider profile, which made `provider profile delete`
fail; Fullsend's ImportProfile discarded that failure and cached success, so
the gateway served a 26-day-old policy while every run reported an import.
That is G42, and patch 0010 stops the silent half of it.

Specs captured here so removal is reversible in principle. All six were
`1/1 Running`, ~1m CPU and ~13Mi each.

## default--agent-review-63c93

```yaml
creationTimestamp: '2026-08-26T20:30:13Z'
labels:
  openshell.ai/gateway-id: openshell
  openshell.ai/managed-by: openshell
  openshell.ai/sandbox-id: b08c853d-9e55-4c3b-bb62-993204c91db9
  openshell.ai/sandbox-name: agent-review-63c93
  openshell.ai/sandbox-workspace: default
annotations:
  agents.x-k8s.io/pod-name: default--agent-review-63c93
  openshell.ai/sandbox-id: b08c853d-9e55-4c3b-bb62-993204c91db9
  openshell.ai/sandbox-name: agent-review-63c93
  openshell.ai/sandbox-workspace: default
spec:
  operatingMode: Running
  podTemplate:
    metadata:
      annotations:
        openshell.io/sandbox-id: b08c853d-9e55-4c3b-bb62-993204c91db9
    spec:
      automountServiceAccountToken: false
      containers:
      - command:
        - /opt/openshell/bin/openshell-sandbox
        - --workdir
        - /sandbox
        env:
        - name: OPENSHELL_SANDBOX_ID
          value: b08c853d-9e55-4c3b-bb62-993204c91db9
        - name: OPENSHELL_SANDBOX
          value: agent-review-63c93
        - name: OPENSHELL_ENDPOINT
          value: http://openshell.openshell-system.svc.cluster.local:8080
        - name: OPENSHELL_SANDBOX_COMMAND
          value: sleep infinity
        - name: OPENSHELL_TELEMETRY_ENABLED
          value: 'false'
        - name: OPENSHELL_SSH_SOCKET_PATH
          value: /run/openshell/ssh.sock
        - name: OPENSHELL_K8S_SA_TOKEN_FILE
          value: /var/run/secrets/openshell/token
        - name: OPENSHELL_OCI_IMAGE_USER
          value: ''
        - name: OPENSHELL_SANDBOX_UID
          value: '1000'
        - name: OPENSHELL_SANDBOX_GID
          value: '1000'
        image: fullsend-sandbox-dev:k3s
        imagePullPolicy: Never
        name: agent
        securityContext:
          appArmorProfile:
            type: Unconfined
          capabilities:
            add:
            - SYS_ADMIN
            - NET_ADMIN
            - SYS_PTRACE
            - SYSLOG
          runAsUser: 0
        volumeMounts:
        - mountPath: /var/run/secrets/openshell
          name: openshell-sa-token
          readOnly: true
        - mountPath: /opt/openshell/bin
          name: openshell-supervisor-bin
          readOnly: true
        - mountPath: /sandbox
          name: workspace
      initContainers:
      - command:
        - /openshell-sandbox
        - copy-self
        - /opt/openshell/bin/openshell-sandbox
        image: ghcr.io/nvidia/openshell/supervisor:0.0.110
        imagePullPolicy: IfNotPresent
        name: openshell-supervisor-install
        securityContext:
          runAsUser: 0
        volumeMounts:
        - mountPath: /opt/openshell/bin
          name: openshell-supervisor-bin
          readOnly: false
      - command:
        - sh
        - -c
        - if [ ! -f /workspace-pvc/.workspace-initialized ]; then if [ -d /sandbox
          ]; then tmp=$(mktemp) && rm -f "$tmp" && (cd /sandbox && find . -mindepth
          1 -maxdepth 1 -exec tar -cf "$tmp" {} +) && if [ -f "$tmp" ]; then tar -C
          /workspace-pvc --no-same-owner --no-same-permissions --touch -xf "$tmp"
          && rm -f "$tmp"; fi; fi && touch /workspace-pvc/.workspace-initialized;
          fi
        image: fullsend-sandbox-dev:k3s
        imagePullPolicy: Never
        name: workspace-init
        securityContext:
          runAsUser: 0
        volumeMounts:
        - mountPath: /workspace-pvc
          name: workspace
      securityContext:
        fsGroup: 1000
      serviceAccountName: openshell-sandbox
      volumes:
      - name: openshell-sa-token
        projected:
          defaultMode: 256
          sources:
          - serviceAccountToken:
              audience: openshell-gateway
              expirationSeconds: 3600
              path: token
      - emptyDir: {}
        name: openshell-supervisor-bin
  shutdownPolicy: Retain
  volumeClaimTemplates:
  - metadata:
      name: workspace
    spec:
      accessModes:
      - ReadWriteOnce
      resources:
        requests:
          storage: 2Gi
      storageClassName: local-path
```

## default--agent-review-96049

```yaml
creationTimestamp: '2026-08-26T20:29:13Z'
labels:
  openshell.ai/gateway-id: openshell
  openshell.ai/managed-by: openshell
  openshell.ai/sandbox-id: b73f450c-b076-434f-8a0d-388690874127
  openshell.ai/sandbox-name: agent-review-96049
  openshell.ai/sandbox-workspace: default
annotations:
  agents.x-k8s.io/pod-name: default--agent-review-96049
  openshell.ai/sandbox-id: b73f450c-b076-434f-8a0d-388690874127
  openshell.ai/sandbox-name: agent-review-96049
  openshell.ai/sandbox-workspace: default
spec:
  operatingMode: Running
  podTemplate:
    metadata:
      annotations:
        openshell.io/sandbox-id: b73f450c-b076-434f-8a0d-388690874127
    spec:
      automountServiceAccountToken: false
      containers:
      - command:
        - /opt/openshell/bin/openshell-sandbox
        - --workdir
        - /sandbox
        env:
        - name: OPENSHELL_SANDBOX_ID
          value: b73f450c-b076-434f-8a0d-388690874127
        - name: OPENSHELL_SANDBOX
          value: agent-review-96049
        - name: OPENSHELL_ENDPOINT
          value: http://openshell.openshell-system.svc.cluster.local:8080
        - name: OPENSHELL_SANDBOX_COMMAND
          value: sleep infinity
        - name: OPENSHELL_TELEMETRY_ENABLED
          value: 'false'
        - name: OPENSHELL_SSH_SOCKET_PATH
          value: /run/openshell/ssh.sock
        - name: OPENSHELL_K8S_SA_TOKEN_FILE
          value: /var/run/secrets/openshell/token
        - name: OPENSHELL_OCI_IMAGE_USER
          value: ''
        - name: OPENSHELL_SANDBOX_UID
          value: '1000'
        - name: OPENSHELL_SANDBOX_GID
          value: '1000'
        image: fullsend-sandbox-dev:k3s
        imagePullPolicy: Never
        name: agent
        securityContext:
          appArmorProfile:
            type: Unconfined
          capabilities:
            add:
            - SYS_ADMIN
            - NET_ADMIN
            - SYS_PTRACE
            - SYSLOG
          runAsUser: 0
        volumeMounts:
        - mountPath: /var/run/secrets/openshell
          name: openshell-sa-token
          readOnly: true
        - mountPath: /opt/openshell/bin
          name: openshell-supervisor-bin
          readOnly: true
        - mountPath: /sandbox
          name: workspace
      initContainers:
      - command:
        - /openshell-sandbox
        - copy-self
        - /opt/openshell/bin/openshell-sandbox
        image: ghcr.io/nvidia/openshell/supervisor:0.0.110
        imagePullPolicy: IfNotPresent
        name: openshell-supervisor-install
        securityContext:
          runAsUser: 0
        volumeMounts:
        - mountPath: /opt/openshell/bin
          name: openshell-supervisor-bin
          readOnly: false
      - command:
        - sh
        - -c
        - if [ ! -f /workspace-pvc/.workspace-initialized ]; then if [ -d /sandbox
          ]; then tmp=$(mktemp) && rm -f "$tmp" && (cd /sandbox && find . -mindepth
          1 -maxdepth 1 -exec tar -cf "$tmp" {} +) && if [ -f "$tmp" ]; then tar -C
          /workspace-pvc --no-same-owner --no-same-permissions --touch -xf "$tmp"
          && rm -f "$tmp"; fi; fi && touch /workspace-pvc/.workspace-initialized;
          fi
        image: fullsend-sandbox-dev:k3s
        imagePullPolicy: Never
        name: workspace-init
        securityContext:
          runAsUser: 0
        volumeMounts:
        - mountPath: /workspace-pvc
          name: workspace
      securityContext:
        fsGroup: 1000
      serviceAccountName: openshell-sandbox
      volumes:
      - name: openshell-sa-token
        projected:
          defaultMode: 256
          sources:
          - serviceAccountToken:
              audience: openshell-gateway
              expirationSeconds: 3600
              path: token
      - emptyDir: {}
        name: openshell-supervisor-bin
  shutdownPolicy: Retain
  volumeClaimTemplates:
  - metadata:
      name: workspace
    spec:
      accessModes:
      - ReadWriteOnce
      resources:
        requests:
          storage: 2Gi
      storageClassName: local-path
```

## default--agent-review-b1ded

```yaml
creationTimestamp: '2026-08-26T20:26:52Z'
labels:
  openshell.ai/gateway-id: openshell
  openshell.ai/managed-by: openshell
  openshell.ai/sandbox-id: cf1ebb04-1b50-4b6c-a983-fdbf21f89f1c
  openshell.ai/sandbox-name: agent-review-b1ded
  openshell.ai/sandbox-workspace: default
annotations:
  agents.x-k8s.io/pod-name: default--agent-review-b1ded
  openshell.ai/sandbox-id: cf1ebb04-1b50-4b6c-a983-fdbf21f89f1c
  openshell.ai/sandbox-name: agent-review-b1ded
  openshell.ai/sandbox-workspace: default
spec:
  operatingMode: Running
  podTemplate:
    metadata:
      annotations:
        openshell.io/sandbox-id: cf1ebb04-1b50-4b6c-a983-fdbf21f89f1c
    spec:
      automountServiceAccountToken: false
      containers:
      - command:
        - /opt/openshell/bin/openshell-sandbox
        - --workdir
        - /sandbox
        env:
        - name: OPENSHELL_SANDBOX_ID
          value: cf1ebb04-1b50-4b6c-a983-fdbf21f89f1c
        - name: OPENSHELL_SANDBOX
          value: agent-review-b1ded
        - name: OPENSHELL_ENDPOINT
          value: http://openshell.openshell-system.svc.cluster.local:8080
        - name: OPENSHELL_SANDBOX_COMMAND
          value: sleep infinity
        - name: OPENSHELL_TELEMETRY_ENABLED
          value: 'false'
        - name: OPENSHELL_SSH_SOCKET_PATH
          value: /run/openshell/ssh.sock
        - name: OPENSHELL_K8S_SA_TOKEN_FILE
          value: /var/run/secrets/openshell/token
        - name: OPENSHELL_OCI_IMAGE_USER
          value: ''
        - name: OPENSHELL_SANDBOX_UID
          value: '1000'
        - name: OPENSHELL_SANDBOX_GID
          value: '1000'
        image: fullsend-sandbox-dev:k3s
        imagePullPolicy: Never
        name: agent
        securityContext:
          appArmorProfile:
            type: Unconfined
          capabilities:
            add:
            - SYS_ADMIN
            - NET_ADMIN
            - SYS_PTRACE
            - SYSLOG
          runAsUser: 0
        volumeMounts:
        - mountPath: /var/run/secrets/openshell
          name: openshell-sa-token
          readOnly: true
        - mountPath: /opt/openshell/bin
          name: openshell-supervisor-bin
          readOnly: true
        - mountPath: /sandbox
          name: workspace
      initContainers:
      - command:
        - /openshell-sandbox
        - copy-self
        - /opt/openshell/bin/openshell-sandbox
        image: ghcr.io/nvidia/openshell/supervisor:0.0.110
        imagePullPolicy: IfNotPresent
        name: openshell-supervisor-install
        securityContext:
          runAsUser: 0
        volumeMounts:
        - mountPath: /opt/openshell/bin
          name: openshell-supervisor-bin
          readOnly: false
      - command:
        - sh
        - -c
        - if [ ! -f /workspace-pvc/.workspace-initialized ]; then if [ -d /sandbox
          ]; then tmp=$(mktemp) && rm -f "$tmp" && (cd /sandbox && find . -mindepth
          1 -maxdepth 1 -exec tar -cf "$tmp" {} +) && if [ -f "$tmp" ]; then tar -C
          /workspace-pvc --no-same-owner --no-same-permissions --touch -xf "$tmp"
          && rm -f "$tmp"; fi; fi && touch /workspace-pvc/.workspace-initialized;
          fi
        image: fullsend-sandbox-dev:k3s
        imagePullPolicy: Never
        name: workspace-init
        securityContext:
          runAsUser: 0
        volumeMounts:
        - mountPath: /workspace-pvc
          name: workspace
      securityContext:
        fsGroup: 1000
      serviceAccountName: openshell-sandbox
      volumes:
      - name: openshell-sa-token
        projected:
          defaultMode: 256
          sources:
          - serviceAccountToken:
              audience: openshell-gateway
              expirationSeconds: 3600
              path: token
      - emptyDir: {}
        name: openshell-supervisor-bin
  shutdownPolicy: Retain
  volumeClaimTemplates:
  - metadata:
      name: workspace
    spec:
      accessModes:
      - ReadWriteOnce
      resources:
        requests:
          storage: 2Gi
      storageClassName: local-path
```

## default--agent-review-ca597

```yaml
creationTimestamp: '2026-08-26T20:12:31Z'
labels:
  openshell.ai/gateway-id: openshell
  openshell.ai/managed-by: openshell
  openshell.ai/sandbox-id: 4376eda0-1bcb-456d-9ad3-134dd17f9332
  openshell.ai/sandbox-name: agent-review-ca597
  openshell.ai/sandbox-workspace: default
annotations:
  agents.x-k8s.io/pod-name: default--agent-review-ca597
  openshell.ai/sandbox-id: 4376eda0-1bcb-456d-9ad3-134dd17f9332
  openshell.ai/sandbox-name: agent-review-ca597
  openshell.ai/sandbox-workspace: default
spec:
  operatingMode: Running
  podTemplate:
    metadata:
      annotations:
        openshell.io/sandbox-id: 4376eda0-1bcb-456d-9ad3-134dd17f9332
    spec:
      automountServiceAccountToken: false
      containers:
      - command:
        - /opt/openshell/bin/openshell-sandbox
        - --workdir
        - /sandbox
        env:
        - name: OPENSHELL_SANDBOX_ID
          value: 4376eda0-1bcb-456d-9ad3-134dd17f9332
        - name: OPENSHELL_SANDBOX
          value: agent-review-ca597
        - name: OPENSHELL_ENDPOINT
          value: http://openshell.openshell-system.svc.cluster.local:8080
        - name: OPENSHELL_SANDBOX_COMMAND
          value: sleep infinity
        - name: OPENSHELL_TELEMETRY_ENABLED
          value: 'false'
        - name: OPENSHELL_SSH_SOCKET_PATH
          value: /run/openshell/ssh.sock
        - name: OPENSHELL_K8S_SA_TOKEN_FILE
          value: /var/run/secrets/openshell/token
        - name: OPENSHELL_OCI_IMAGE_USER
          value: ''
        - name: OPENSHELL_SANDBOX_UID
          value: '1000'
        - name: OPENSHELL_SANDBOX_GID
          value: '1000'
        image: fullsend-sandbox-dev:k3s
        imagePullPolicy: Never
        name: agent
        securityContext:
          appArmorProfile:
            type: Unconfined
          capabilities:
            add:
            - SYS_ADMIN
            - NET_ADMIN
            - SYS_PTRACE
            - SYSLOG
          runAsUser: 0
        volumeMounts:
        - mountPath: /var/run/secrets/openshell
          name: openshell-sa-token
          readOnly: true
        - mountPath: /opt/openshell/bin
          name: openshell-supervisor-bin
          readOnly: true
        - mountPath: /sandbox
          name: workspace
      initContainers:
      - command:
        - /openshell-sandbox
        - copy-self
        - /opt/openshell/bin/openshell-sandbox
        image: ghcr.io/nvidia/openshell/supervisor:0.0.110
        imagePullPolicy: IfNotPresent
        name: openshell-supervisor-install
        securityContext:
          runAsUser: 0
        volumeMounts:
        - mountPath: /opt/openshell/bin
          name: openshell-supervisor-bin
          readOnly: false
      - command:
        - sh
        - -c
        - if [ ! -f /workspace-pvc/.workspace-initialized ]; then if [ -d /sandbox
          ]; then tmp=$(mktemp) && rm -f "$tmp" && (cd /sandbox && find . -mindepth
          1 -maxdepth 1 -exec tar -cf "$tmp" {} +) && if [ -f "$tmp" ]; then tar -C
          /workspace-pvc --no-same-owner --no-same-permissions --touch -xf "$tmp"
          && rm -f "$tmp"; fi; fi && touch /workspace-pvc/.workspace-initialized;
          fi
        image: fullsend-sandbox-dev:k3s
        imagePullPolicy: Never
        name: workspace-init
        securityContext:
          runAsUser: 0
        volumeMounts:
        - mountPath: /workspace-pvc
          name: workspace
      securityContext:
        fsGroup: 1000
      serviceAccountName: openshell-sandbox
      volumes:
      - name: openshell-sa-token
        projected:
          defaultMode: 256
          sources:
          - serviceAccountToken:
              audience: openshell-gateway
              expirationSeconds: 3600
              path: token
      - emptyDir: {}
        name: openshell-supervisor-bin
  shutdownPolicy: Retain
  volumeClaimTemplates:
  - metadata:
      name: workspace
    spec:
      accessModes:
      - ReadWriteOnce
      resources:
        requests:
          storage: 2Gi
      storageClassName: local-path
```

## default--net-debug

```yaml
creationTimestamp: '2026-08-21T04:05:19Z'
labels:
  openshell.ai/gateway-id: openshell
  openshell.ai/managed-by: openshell
  openshell.ai/sandbox-id: 946ec387-77c1-4cfe-a88e-a64cb0bc2220
  openshell.ai/sandbox-name: net-debug
  openshell.ai/sandbox-workspace: default
annotations:
  agents.x-k8s.io/pod-name: default--net-debug
  openshell.ai/sandbox-id: 946ec387-77c1-4cfe-a88e-a64cb0bc2220
  openshell.ai/sandbox-name: net-debug
  openshell.ai/sandbox-workspace: default
spec:
  operatingMode: Running
  podTemplate:
    metadata:
      annotations:
        openshell.io/sandbox-id: 946ec387-77c1-4cfe-a88e-a64cb0bc2220
    spec:
      automountServiceAccountToken: false
      containers:
      - command:
        - /opt/openshell/bin/openshell-sandbox
        - --workdir
        - /sandbox
        env:
        - name: OPENSHELL_SANDBOX_ID
          value: 946ec387-77c1-4cfe-a88e-a64cb0bc2220
        - name: OPENSHELL_SANDBOX
          value: net-debug
        - name: OPENSHELL_ENDPOINT
          value: http://openshell.openshell-system.svc.cluster.local:8080
        - name: OPENSHELL_SANDBOX_COMMAND
          value: sleep infinity
        - name: OPENSHELL_TELEMETRY_ENABLED
          value: 'false'
        - name: OPENSHELL_SSH_SOCKET_PATH
          value: /run/openshell/ssh.sock
        - name: OPENSHELL_K8S_SA_TOKEN_FILE
          value: /var/run/secrets/openshell/token
        - name: OPENSHELL_OCI_IMAGE_USER
          value: ''
        - name: OPENSHELL_SANDBOX_UID
          value: '1000'
        - name: OPENSHELL_SANDBOX_GID
          value: '1000'
        image: fullsend-sandbox-dev:k3s
        imagePullPolicy: Never
        name: agent
        securityContext:
          appArmorProfile:
            type: Unconfined
          capabilities:
            add:
            - SYS_ADMIN
            - NET_ADMIN
            - SYS_PTRACE
            - SYSLOG
          runAsUser: 0
        volumeMounts:
        - mountPath: /var/run/secrets/openshell
          name: openshell-sa-token
          readOnly: true
        - mountPath: /opt/openshell/bin
          name: openshell-supervisor-bin
          readOnly: true
        - mountPath: /sandbox
          name: workspace
      initContainers:
      - command:
        - /openshell-sandbox
        - copy-self
        - /opt/openshell/bin/openshell-sandbox
        image: ghcr.io/nvidia/openshell/supervisor:0.0.110
        imagePullPolicy: IfNotPresent
        name: openshell-supervisor-install
        securityContext:
          runAsUser: 0
        volumeMounts:
        - mountPath: /opt/openshell/bin
          name: openshell-supervisor-bin
          readOnly: false
      - command:
        - sh
        - -c
        - if [ ! -f /workspace-pvc/.workspace-initialized ]; then if [ -d /sandbox
          ]; then tmp=$(mktemp) && rm -f "$tmp" && (cd /sandbox && find . -mindepth
          1 -maxdepth 1 -exec tar -cf "$tmp" {} +) && if [ -f "$tmp" ]; then tar -C
          /workspace-pvc --no-same-owner --no-same-permissions --touch -xf "$tmp"
          && rm -f "$tmp"; fi; fi && touch /workspace-pvc/.workspace-initialized;
          fi
        image: fullsend-sandbox-dev:k3s
        imagePullPolicy: Never
        name: workspace-init
        securityContext:
          runAsUser: 0
        volumeMounts:
        - mountPath: /workspace-pvc
          name: workspace
      securityContext:
        fsGroup: 1000
      serviceAccountName: openshell-sandbox
      volumes:
      - name: openshell-sa-token
        projected:
          defaultMode: 256
          sources:
          - serviceAccountToken:
              audience: openshell-gateway
              expirationSeconds: 3600
              path: token
      - emptyDir: {}
        name: openshell-supervisor-bin
  shutdownPolicy: Retain
  volumeClaimTemplates:
  - metadata:
      name: workspace
    spec:
      accessModes:
      - ReadWriteOnce
      resources:
        requests:
          storage: 2Gi
      storageClassName: local-path
```

## default--net-nopolicy

```yaml
creationTimestamp: '2026-08-21T04:02:33Z'
labels:
  openshell.ai/gateway-id: openshell
  openshell.ai/managed-by: openshell
  openshell.ai/sandbox-id: 45081c98-c008-45c2-a97e-0c6013600d9f
  openshell.ai/sandbox-name: net-nopolicy
  openshell.ai/sandbox-workspace: default
annotations:
  agents.x-k8s.io/pod-name: default--net-nopolicy
  openshell.ai/sandbox-id: 45081c98-c008-45c2-a97e-0c6013600d9f
  openshell.ai/sandbox-name: net-nopolicy
  openshell.ai/sandbox-workspace: default
spec:
  operatingMode: Running
  podTemplate:
    metadata:
      annotations:
        openshell.io/sandbox-id: 45081c98-c008-45c2-a97e-0c6013600d9f
    spec:
      automountServiceAccountToken: false
      containers:
      - command:
        - /opt/openshell/bin/openshell-sandbox
        - --workdir
        - /sandbox
        env:
        - name: OPENSHELL_SANDBOX_ID
          value: 45081c98-c008-45c2-a97e-0c6013600d9f
        - name: OPENSHELL_SANDBOX
          value: net-nopolicy
        - name: OPENSHELL_ENDPOINT
          value: http://openshell.openshell-system.svc.cluster.local:8080
        - name: OPENSHELL_SANDBOX_COMMAND
          value: sleep infinity
        - name: OPENSHELL_TELEMETRY_ENABLED
          value: 'false'
        - name: OPENSHELL_SSH_SOCKET_PATH
          value: /run/openshell/ssh.sock
        - name: OPENSHELL_K8S_SA_TOKEN_FILE
          value: /var/run/secrets/openshell/token
        - name: OPENSHELL_OCI_IMAGE_USER
          value: ''
        - name: OPENSHELL_SANDBOX_UID
          value: '1000'
        - name: OPENSHELL_SANDBOX_GID
          value: '1000'
        image: fullsend-sandbox-dev:k3s
        imagePullPolicy: Never
        name: agent
        securityContext:
          appArmorProfile:
            type: Unconfined
          capabilities:
            add:
            - SYS_ADMIN
            - NET_ADMIN
            - SYS_PTRACE
            - SYSLOG
          runAsUser: 0
        volumeMounts:
        - mountPath: /var/run/secrets/openshell
          name: openshell-sa-token
          readOnly: true
        - mountPath: /opt/openshell/bin
          name: openshell-supervisor-bin
          readOnly: true
        - mountPath: /sandbox
          name: workspace
      initContainers:
      - command:
        - /openshell-sandbox
        - copy-self
        - /opt/openshell/bin/openshell-sandbox
        image: ghcr.io/nvidia/openshell/supervisor:0.0.110
        imagePullPolicy: IfNotPresent
        name: openshell-supervisor-install
        securityContext:
          runAsUser: 0
        volumeMounts:
        - mountPath: /opt/openshell/bin
          name: openshell-supervisor-bin
          readOnly: false
      - command:
        - sh
        - -c
        - if [ ! -f /workspace-pvc/.workspace-initialized ]; then if [ -d /sandbox
          ]; then tmp=$(mktemp) && rm -f "$tmp" && (cd /sandbox && find . -mindepth
          1 -maxdepth 1 -exec tar -cf "$tmp" {} +) && if [ -f "$tmp" ]; then tar -C
          /workspace-pvc --no-same-owner --no-same-permissions --touch -xf "$tmp"
          && rm -f "$tmp"; fi; fi && touch /workspace-pvc/.workspace-initialized;
          fi
        image: fullsend-sandbox-dev:k3s
        imagePullPolicy: Never
        name: workspace-init
        securityContext:
          runAsUser: 0
        volumeMounts:
        - mountPath: /workspace-pvc
          name: workspace
      securityContext:
        fsGroup: 1000
      serviceAccountName: openshell-sandbox
      volumes:
      - name: openshell-sa-token
        projected:
          defaultMode: 256
          sources:
          - serviceAccountToken:
              audience: openshell-gateway
              expirationSeconds: 3600
              path: token
      - emptyDir: {}
        name: openshell-supervisor-bin
  shutdownPolicy: Retain
  volumeClaimTemplates:
  - metadata:
      name: workspace
    spec:
      accessModes:
      - ReadWriteOnce
      resources:
        requests:
          storage: 2Gi
      storageClassName: local-path
```

