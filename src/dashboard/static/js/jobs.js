if (K8S_AVAILABLE) {
  const form = document.getElementById('submit-form');
  const skillSelect = document.getElementById('skill');
  const fqnInput = document.getElementById('skill-fqn');
  const promptInput = document.getElementById('skill-prompt');
  const pluginSection = document.getElementById('plugin-section');
  const advancedSection = document.getElementById('advanced-section');
  const harnessSelect = document.getElementById('harness');
  const modelSelect = document.getElementById('model');
  const runnerSelect = document.getElementById('runner');
  const executionSelect = document.getElementById('execution');
  const formNote = document.getElementById('form-note');

  // --- What to run: Skill / FQN / Prompt tabs ---
  // Each tab keeps its own value; only the active tab's value is submitted.
  let inputMode = 'skill';
  const MODE_INPUTS = { skill: skillSelect, fqn: fqnInput, prompt: promptInput };

  function setInputMode(mode) {
    inputMode = mode;
    document.querySelectorAll('.mode-tab').forEach(tab => {
      tab.setAttribute('aria-selected', tab.dataset.mode === mode ? 'true' : 'false');
    });
    document.querySelectorAll('.mode-panel').forEach(panel => {
      panel.hidden = panel.dataset.mode !== mode;
    });
    // Registries and plugins matter most for prompts; open them there and
    // fold them away elsewhere unless they hold something.
    if (mode === 'prompt') pluginSection.open = true;
    else if (!hasPluginValues()) pluginSection.open = false;
  }

  document.querySelectorAll('.mode-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      setInputMode(tab.dataset.mode);
      MODE_INPUTS[tab.dataset.mode].focus();
    });
  });

  // --- Collapsed section summaries ---
  function splitLines(value) {
    return value.split(/\n+/).map(s => s.trim()).filter(Boolean);
  }

  function hasPluginValues() {
    return splitLines(document.getElementById('registries').value).length > 0 ||
      splitLines(document.getElementById('plugins').value).length > 0;
  }

  const ADVANCED_DEFAULTS = {
    'enable-force': [false, 'force on'],
    'enable-strace': [true, 'strace off'],
    'enable-mlflow': [true, 'MLflow off'],
    'enable-otel': [true, 'OTel off'],
    'enable-api-dump': [true, 'API dump off'],
  };

  function advancedChanges() {
    const changes = [];
    for (const [id, [def, label]] of Object.entries(ADVANCED_DEFAULTS)) {
      if (document.getElementById(id).checked !== def) changes.push(label);
    }
    if (document.getElementById('extra-kwargs').value.trim()) changes.push('kwargs');
    if (document.getElementById('extra-env').value.trim()) changes.push('env vars');
    return changes;
  }

  function updateSummaries() {
    const regs = splitLines(document.getElementById('registries').value).length;
    const plugs = splitLines(document.getElementById('plugins').value).length;
    const parts = [];
    if (regs) parts.push(regs + (regs === 1 ? ' registry' : ' registries'));
    if (plugs) parts.push(plugs + (plugs === 1 ? ' plugin' : ' plugins'));
    document.getElementById('plugin-summary').textContent = parts.length ? '· ' + parts.join(', ') : '';
    const changes = advancedChanges();
    document.getElementById('advanced-summary').textContent = changes.length ? '· ' + changes.join(', ') : '';
  }

  form.addEventListener('input', updateSummaries);
  form.addEventListener('change', updateSummaries);

  // --- Harness-dependent model and runner options ---
  // Claude Code takes an alias or a pinned model ID. Pinned IDs are the Vertex
  // catalog the relay reports for vertex-shim-local; "Other…" accepts any ID.
  const OTHER_MODEL = '__other__';
  const HARNESS_MODELS = {
    'claude-code': [
      { group: 'Aliases', options: [
        { value: 'haiku', label: 'haiku' },
        { value: 'sonnet', label: 'sonnet' },
        { value: 'opus', label: 'opus', selected: true },
      ] },
      { group: 'Pinned', options: [
        'claude-opus-5-5', 'claude-opus-5', 'claude-opus-4-8', 'claude-opus-4-7',
        'claude-opus-4-6', 'claude-opus-4-5@20251101',
        'claude-sonnet-5-5', 'claude-sonnet-5', 'claude-sonnet-4-6',
        'claude-sonnet-4-5@20250929',
        'claude-haiku-5-5', 'claude-haiku-4-5@20251001',
        'claude-fable-5-1', 'claude-fable-5',
      ].map(id => ({ value: id, label: id })) },
      { options: [{ value: OTHER_MODEL, label: 'Other…' }] },
    ],
    'opencode': [
      { options: [
        { value: 'google-vertex-anthropic/claude-haiku-4-5@20251001', label: 'claude-haiku-4-5' },
        { value: 'google-vertex-anthropic/claude-sonnet-4-6@default', label: 'claude-sonnet-4-6' },
        { value: 'google-vertex-anthropic/claude-opus-4-6@default', label: 'claude-opus-4-6', selected: true },
        { value: OTHER_MODEL, label: 'Other…' },
      ] },
    ],
  };

  const HARNESS_RUNNERS = {
    'claude-code': [
      { value: 'cli', label: 'CLI', selected: true },
      { value: 'sdk', label: 'SDK' },
      { value: 'agentic-ci', label: 'agentic-ci' },
    ],
    'opencode': [
      { value: 'cli', label: 'CLI' },
      { value: 'sdk', label: 'SDK', selected: true },
      { value: 'agentic-ci', label: 'agentic-ci' },
    ],
  };

  function fillOptions(select, options) {
    select.innerHTML = '';
    options.forEach(o => {
      const opt = new Option(o.label, o.value, false, !!o.selected);
      select.add(opt);
    });
  }

  // Options in optional groups: [{ group?, options: [...] }].
  function fillGroupedOptions(select, groups) {
    select.innerHTML = '';
    groups.forEach(g => {
      const parent = g.group ? document.createElement('optgroup') : select;
      if (g.group) {
        parent.label = g.group;
        select.appendChild(parent);
      }
      g.options.forEach(o => parent.appendChild(new Option(o.label, o.value, false, !!o.selected)));
    });
  }

  // Select a value, adding it as an option when a past job used one this
  // form no longer lists.
  function selectValue(select, value) {
    if (!value) return;
    if (![...select.options].some(o => o.value === value)) {
      select.add(new Option(value, value));
    }
    select.value = value;
  }

  const modelCustom = document.getElementById('model-custom');

  function syncModelCustom() {
    const other = modelSelect.value === OTHER_MODEL;
    modelCustom.hidden = !other;
    modelCustom.required = other;
  }

  // A model the list does not offer goes into the "Other…" field.
  function setModel(value) {
    if (value && ![...modelSelect.options].some(o => o.value === value && o.value !== OTHER_MODEL)) {
      modelSelect.value = OTHER_MODEL;
      modelCustom.value = value;
    } else if (value) {
      modelSelect.value = value;
      modelCustom.value = '';
    }
    syncModelCustom();
  }

  function modelValue() {
    return modelSelect.value === OTHER_MODEL ? modelCustom.value.trim() : modelSelect.value;
  }

  modelSelect.addEventListener('change', () => {
    syncModelCustom();
    if (!modelCustom.hidden) modelCustom.focus();
  });

  function setHarness(harness) {
    harnessSelect.value = harness;
    fillGroupedOptions(modelSelect, HARNESS_MODELS[harness] || HARNESS_MODELS['claude-code']);
    modelCustom.value = '';
    modelCustom.placeholder = harness === 'opencode'
      ? 'google-vertex-anthropic/claude-opus-4-6@default'
      : 'claude-opus-4-6';
    syncModelCustom();
    fillOptions(runnerSelect, HARNESS_RUNNERS[harness] || HARNESS_RUNNERS['claude-code']);
  }

  harnessSelect.addEventListener('change', () => setHarness(harnessSelect.value));
  setHarness(harnessSelect.value);

  // --- Reset and prefill ---
  function resetForm() {
    form.reset();
    setHarness('claude-code');
    executionSelect.value = 'kubernetes';
    setInputMode('skill');
    pluginSection.open = false;
    advancedSection.open = false;
    formNote.textContent = '';
    updateSummaries();
  }

  document.getElementById('form-reset').addEventListener('click', () => {
    resetForm();
    document.getElementById('submit-status').innerHTML = '';
  });

  // Load a past job into the form so it can be edited and submitted again.
  function fillForm(opts, jobName) {
    resetForm();
    if (opts.prompt) {
      setInputMode('prompt');
      promptInput.value = opts.prompt;
    } else if (opts.fqn) {
      setInputMode('fqn');
      fqnInput.value = opts.fqn;
    } else {
      setInputMode('skill');
      if (opts.phase) {
        if (![...skillSelect.options].some(o => o.value === opts.phase)) {
          skillSelect.add(new Option(SKILL_MAP[opts.phase] || opts.phase, opts.phase));
        }
        skillSelect.value = opts.phase;
      }
    }

    document.getElementById('registries').value = (opts.registries || []).join('\n');
    document.getElementById('plugins').value = (opts.plugins || []).join('\n');
    if (hasPluginValues()) pluginSection.open = true;

    setHarness(opts.harness || 'claude-code');
    setModel(opts.model);
    selectValue(runnerSelect, opts.runner || 'cli');

    const notes = [];
    const execution = opts.execution || 'kubernetes';
    if ([...executionSelect.options].some(o => o.value === execution)) {
      executionSelect.value = execution;
    } else {
      notes.push('Execution ' + execution + ' is not available here, so Kubernetes Job is selected');
    }
    if (opts.issue && opts.issue !== 'all') {
      document.getElementById('issue').value = opts.issue.toUpperCase();
    }

    document.getElementById('extra-kwargs').value = opts.extra_kwargs || '';
    document.getElementById('extra-env').value =
      Object.entries(opts.extra_env || {}).map(([k, v]) => `${k}=${v}`).join(' ');
    document.getElementById('enable-force').checked = !!opts.force;
    document.getElementById('enable-strace').checked = !!opts.strace;
    document.getElementById('enable-mlflow').checked = opts.mlflow !== false;
    document.getElementById('enable-otel').checked = opts.otel !== false;
    document.getElementById('enable-api-dump').checked = opts.api_dump !== false;
    if (advancedChanges().length) advancedSection.open = true;

    updateSummaries();
    formNote.textContent = 'Loaded from ' + jobName + '. Edit and submit.' +
      (notes.length ? ' ' + notes.join('. ') + '.' : '');
    document.getElementById('submit-status').innerHTML = '';
    document.getElementById('submit-card').scrollIntoView({ behavior: 'smooth', block: 'start' });
    MODE_INPUTS[inputMode].focus({ preventScroll: true });
  }

  // --- Submit ---
  function buildBody() {
    const value = inputMode === 'skill'
      ? skillSelect.value
      : MODE_INPUTS[inputMode].value.trim();
    if (!value) {
      const what = { skill: 'Select a skill', fqn: 'Enter an FQN', prompt: 'Enter a prompt' };
      throw new Error(what[inputMode]);
    }

    const model = modelValue();
    if (!model) throw new Error('Enter a model ID');
    const args = {
      model,
      runner: runnerSelect.value,
      harness: harnessSelect.value,
    };
    const issue = document.getElementById('issue').value.trim();
    if (issue) args.issue = issue.toUpperCase();
    const extraKwargs = document.getElementById('extra-kwargs').value.trim();
    if (extraKwargs) args.extra_kwargs = extraKwargs;
    const extraEnvStr = document.getElementById('extra-env').value.trim();
    if (extraEnvStr) {
      args.extra_env = {};
      extraEnvStr.split(/\s+/).forEach(kv => {
        const eq = kv.indexOf('=');
        if (eq > 0) args.extra_env[kv.slice(0, eq)] = kv.slice(eq + 1);
      });
    }
    if (document.getElementById('enable-force').checked) args.force = true;
    if (document.getElementById('enable-strace').checked) args.strace = true;
    if (!document.getElementById('enable-mlflow').checked) args.mlflow = false;
    if (!document.getElementById('enable-otel').checked) args.otel = false;
    if (!document.getElementById('enable-api-dump').checked) args.api_dump = false;

    const registries = splitLines(document.getElementById('registries').value);
    if (registries.length) args.registries = registries;
    const plugins = splitLines(document.getElementById('plugins').value);
    if (plugins.length) args.plugins = plugins;

    const execution = executionSelect.value;
    if (inputMode === 'prompt') {
      args.prompt = value;
      return { args, execution };
    }
    if (inputMode === 'fqn') return { fqn: value, args, execution };
    return { command: value, args, execution };
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const statusDiv = document.getElementById('submit-status');

    let body;
    try {
      body = buildBody();
    } catch (err) {
      statusDiv.innerHTML = '<strong style="color: #e74c3c;">✗ Error:</strong> ' + err.message;
      return;
    }

    statusDiv.innerHTML = '<em style="color: #3498db;">Submitting job...</em>';

    try {
      const response = await fetch('/api/jobs/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      const data = await response.json();

      if (response.ok) {
        statusDiv.innerHTML = '<strong style="color: #27ae60;">✓ Job submitted:</strong> ' + data.job_name;
        resetForm();
        await refreshJobs();
        openJobModal(data.job_name);
      } else {
        statusDiv.innerHTML = '<strong style="color: #e74c3c;">✗ Error:</strong> ' + (data.error || 'Unknown error');
      }
    } catch (err) {
      statusDiv.innerHTML = '<strong style="color: #e74c3c;">✗ Error:</strong> ' + err.message;
    }
  });

  // Refresh jobs table
  async function refreshJobs() {
    try {
      const response = await fetch('/api/jobs');
      const jobs = await response.json();

      jobs.sort((a, b) => new Date(b.created) - new Date(a.created));

      document.getElementById('job-count').textContent = '(' + jobs.length + ')';

      const tbody = document.getElementById('jobs-tbody');

      if (jobs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; color: #95a5a6;">No jobs found</td></tr>';
        return;
      }

      tbody.innerHTML = jobs.map(job => {
        const statusClass = 'status-' + job.status;
        const duration = job.duration ? job.duration.toFixed(1) : '-';
        const created = new Date(job.created).toLocaleString();
        const runner = job.runner || 'cli';

        return `
          <tr onclick="openJobModal('${job.name}')" class="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50">
            <td class="px-4 py-3 font-mono text-xs">${job.name}</td>
            <td class="px-4 py-3">${scriptLabel(job.script) || job.fqn || SKILL_MAP[job.phase] || job.phase}</td>
            <td class="px-4 py-3">${job.issue.toUpperCase()}</td>
            <td class="px-4 py-3">${job.model}</td>
            <td class="px-4 py-3">${runner}</td>
            <td class="px-4 py-3">${job.harness || 'claude-code'}</td>
            <td class="px-4 py-3">${job.execution || 'kubernetes'}</td>
            <td class="px-4 py-3 ${statusClass}">${job.status}</td>
            <td class="px-4 py-3">${created}</td>
            <td class="px-4 py-3">${duration}</td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      console.error('Failed to refresh jobs:', err);
    }
  }

  // --- Job Detail Modal ---

  let logPollInterval = null;
  let currentModalJob = null;

  const STATUS_BADGE_CLASS = {
    pending: 'badge-val-skip',
    running: 'badge-fix-ai-fixable',
    completed: 'badge-val-pass',
    failed: 'badge-val-fail'
  };

  async function openJobModal(jobName) {
    currentModalJob = jobName;
    const modal = document.getElementById('job-modal');
    const logEl = document.getElementById('modal-log-content');

    document.getElementById('modal-job-name').textContent = jobName;
    logEl.textContent = 'Loading logs...';

    // Fetch job details
    try {
      const res = await fetch('/api/jobs/' + jobName);
      const job = await res.json();

      const badge = document.getElementById('modal-status-badge');
      badge.textContent = job.status;
      badge.className = 'badge ' + (STATUS_BADGE_CLASS[job.status] || 'badge-default');

      document.getElementById('modal-phase').textContent = scriptLabel(job.script) || job.fqn || SKILL_MAP[job.phase] || job.phase || '-';
      document.getElementById('modal-issue').textContent = (job.issue || '-').toUpperCase();
      document.getElementById('modal-model').textContent = job.model || '-';
      document.getElementById('modal-runner').textContent = job.runner || 'cli';
      document.getElementById('modal-harness').textContent = job.harness || 'claude-code';
      document.getElementById('modal-execution').textContent = job.execution || 'kubernetes';
      document.getElementById('modal-created').textContent = job.created ? new Date(job.created).toLocaleString() : '-';
      document.getElementById('modal-started').textContent = job.started ? new Date(job.started).toLocaleString() : '-';

      if (job.completed && job.started) {
        const dur = ((new Date(job.completed) - new Date(job.started)) / 1000).toFixed(1);
        document.getElementById('modal-duration').textContent = dur + 's';
      } else {
        document.getElementById('modal-duration').textContent = '-';
      }

      document.getElementById('modal-result').textContent =
        (job.succeeded ? job.succeeded + ' succeeded' : '') +
        (job.failed ? (job.succeeded ? ', ' : '') + job.failed + ' failed' : '') ||
        '-';

      document.getElementById('modal-force').innerHTML = job.force
        ? '<span class="text-green-600 dark:text-green-400">Enabled</span>'
        : '<span class="text-gray-400">Off</span>';
      document.getElementById('modal-strace').innerHTML = job.strace
        ? '<span class="text-green-600 dark:text-green-400">Enabled</span>'
        : '<span class="text-gray-400">Off</span>';
      document.getElementById('modal-mlflow').innerHTML = job.mlflow
        ? '<span class="text-green-600 dark:text-green-400">Enabled</span>'
        : '<span class="text-gray-400">Off</span>';
      document.getElementById('modal-otel').innerHTML = job.otel !== false
        ? '<span class="text-green-600 dark:text-green-400">Enabled</span>'
        : '<span class="text-gray-400">Off</span>';
      document.getElementById('modal-api-dump').innerHTML = job.api_dump !== false
        ? '<span class="text-green-600 dark:text-green-400">Enabled</span>'
        : '<span class="text-gray-400">Off</span>';

      const ekRow = document.getElementById('modal-extra-kwargs-row');
      if (job.extra_kwargs) {
        document.getElementById('modal-extra-kwargs').textContent = job.extra_kwargs;
        ekRow.style.display = '';
      } else {
        ekRow.style.display = 'none';
      }

      const eeRow = document.getElementById('modal-extra-env-row');
      if (eeRow) {
        const envObj = job.extra_env || {};
        const envStr = Object.entries(envObj).map(([k,v]) => `${k}=${v}`).join(' ');
        if (envStr) {
          document.getElementById('modal-extra-env').textContent = envStr;
          eeRow.style.display = '';
        } else {
          eeRow.style.display = 'none';
        }
      }

      const promptRow = document.getElementById('modal-prompt-row');
      if (job.prompt) {
        document.getElementById('modal-prompt').textContent = job.prompt;
        promptRow.style.display = '';
      } else {
        promptRow.style.display = 'none';
      }

      const regsRow = document.getElementById('modal-registries-row');
      const regs = job.registries ? (typeof job.registries === 'string' ? JSON.parse(job.registries) : job.registries) : [];
      if (regs.length) {
        document.getElementById('modal-registries').textContent = regs.join(', ');
        regsRow.style.display = '';
      } else {
        regsRow.style.display = 'none';
      }

      const plugsRow = document.getElementById('modal-plugins-row');
      const plugs = job.plugins ? (typeof job.plugins === 'string' ? JSON.parse(job.plugins) : job.plugins) : [];
      if (plugs.length) {
        document.getElementById('modal-plugins').textContent = plugs.join(', ');
        plugsRow.style.display = '';
      } else {
        plugsRow.style.display = 'none';
      }

      // Store job opts for re-run
      window._rerunOpts = {
        phase: job.phase,
        fqn: job.fqn || '',
        prompt: job.prompt || '',
        registries: regs,
        plugins: plugs,
        issue: job.issue,
        model: job.model,
        runner: job.runner || 'cli',
        harness: job.harness || 'claude-code',
        execution: job.execution || 'kubernetes',
        extra_kwargs: job.extra_kwargs || '',
        extra_env: job.extra_env || {},
        force: !!job.force,
        strace: !!job.strace,
        mlflow: job.mlflow !== false,
        otel: job.otel !== false,
        api_dump: job.api_dump !== false,
        script: job.script || null,
        mlflow_experiment: job.mlflow_experiment || '',
      };

      // Action buttons
      const actionsEl = document.getElementById('modal-actions');
      let btns = '';
      btns += rerunButton(window._rerunOpts);
      if (job.status === 'running' || job.status === 'pending') {
        btns += `<button class="btn-stop" onclick="modalStop('${jobName}')">Stop</button>`;
      }
      btns += `<button class="btn-delete" onclick="modalDelete('${jobName}')">Delete</button>`;
      actionsEl.innerHTML = btns;

    } catch (err) {
      document.getElementById('modal-phase').textContent = '-';
      document.getElementById('modal-issue').textContent = '-';
    }

    // Fetch logs
    await fetchModalLogs(jobName);

    modal.showModal();

    // Poll logs every 2s for running/pending jobs
    startLogPolling(jobName);
  }

  async function fetchModalLogs(jobName) {
    try {
      const res = await fetch('/api/jobs/' + jobName + '/logs');
      const logs = await res.text();
      const logEl = document.getElementById('modal-log-content');
      const wasAtBottom = logEl.scrollHeight - logEl.scrollTop - logEl.clientHeight < 40;
      logEl.textContent = logs || '(no logs available)';
      if (wasAtBottom) logEl.scrollTop = logEl.scrollHeight;
    } catch (err) {
      document.getElementById('modal-log-content').textContent = 'Error loading logs: ' + err.message;
    }
  }

  function startLogPolling(jobName) {
    stopLogPolling();
    logPollInterval = setInterval(async () => {
      // Check if job is still running
      try {
        const res = await fetch('/api/jobs/' + jobName);
        const job = await res.json();

        // Update status badge
        const badge = document.getElementById('modal-status-badge');
        badge.textContent = job.status;
        badge.className = 'badge ' + (STATUS_BADGE_CLASS[job.status] || 'badge-default');

        if (job.completed && job.started) {
          const dur = ((new Date(job.completed) - new Date(job.started)) / 1000).toFixed(1);
          document.getElementById('modal-duration').textContent = dur + 's';
        }

        if (job.status !== 'running' && job.status !== 'pending') {
          // Update actions (remove Stop button)
          const actionsEl = document.getElementById('modal-actions');
          let btns = '';
          btns += rerunButton(window._rerunOpts);
          btns += `<button class="btn-delete" onclick="modalDelete('${jobName}')">Delete</button>`;
          actionsEl.innerHTML = btns;

          document.getElementById('modal-result').textContent =
            (job.succeeded ? job.succeeded + ' succeeded' : '') +
            (job.failed ? (job.succeeded ? ', ' : '') + job.failed + ' failed' : '') ||
            '-';

          stopLogPolling();
        }
      } catch (e) {}

      await fetchModalLogs(jobName);
    }, 2000);
  }

  function stopLogPolling() {
    if (logPollInterval) {
      clearInterval(logPollInterval);
      logPollInterval = null;
    }
  }

  function closeJobModal() {
    stopLogPolling();
    currentModalJob = null;
    document.getElementById('job-modal').close();
  }

  // Close on backdrop click
  document.getElementById('job-modal').addEventListener('click', function(e) {
    if (e.target === this) closeJobModal();
  });

  // Modal action handlers
  async function modalStop(jobName) {
    if (!confirm('Stop job "' + jobName + '"?')) return;
    try {
      await fetch('/api/jobs/' + jobName + '/stop', { method: 'POST' });
      refreshJobs();
    } catch (err) {
      alert('Error stopping job: ' + err.message);
    }
  }

  async function modalDelete(jobName) {
    if (!confirm('Delete job "' + jobName + '"?')) return;
    try {
      const res = await fetch('/api/jobs/' + jobName, { method: 'DELETE' });
      if (res.ok) {
        closeJobModal();
        refreshJobs();
      } else {
        const data = await res.json();
        alert('Error deleting job: ' + (data.error || 'Unknown error'));
      }
    } catch (err) {
      alert('Error deleting job: ' + err.message);
    }
  }

  // Script jobs have no form tab: their button submits the same script and
  // settings again. Other jobs load into the form to edit first.
  function scriptLabel(script) {
    if (!script) return '';
    return script.ref ? `${script.path} @ ${script.ref.slice(0, 12)}` : script.path;
  }

  function rerunButton(opts) {
    if (opts && opts.script) {
      return '<button class="btn-rerun" onclick="modalRerun(window._rerunOpts)" title="Submit this script job again with the same settings">Re-run</button>';
    }
    return '<button class="btn-rerun" onclick="modalRerun(window._rerunOpts)" title="Load this job into the form to edit and submit">Edit &amp; re-run</button>';
  }

  async function rerunScript(opts) {
    const script = { path: opts.script.path, args: opts.script.args || [] };
    if (opts.script.repo) {
      script.repo = opts.script.repo;
      script.ref = opts.script.ref;
    }
    const args = { model: opts.model };
    if (opts.issue && opts.issue !== 'all') args.issue = opts.issue.toUpperCase();
    if (opts.extra_env && Object.keys(opts.extra_env).length) args.extra_env = opts.extra_env;
    if (opts.mlflow_experiment) args.mlflow_experiment = opts.mlflow_experiment;
    if (opts.strace) args.strace = true;
    if (opts.mlflow === false) args.mlflow = false;
    if (opts.otel === false) args.otel = false;
    if (opts.api_dump === false) args.api_dump = false;
    const res = await fetch('/api/jobs/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ script, args }),
    });
    const data = await res.json();
    if (!res.ok) {
      alert('Error re-running job: ' + (data.error || 'Unknown error'));
      return;
    }
    closeJobModal();
    await refreshJobs();
    openJobModal(data.job_name);
  }

  function modalRerun(opts) {
    opts = opts || {};
    if (opts.script) {
      rerunScript(opts);
      return;
    }
    const jobName = currentModalJob;
    closeJobModal();
    fillForm(opts, jobName);
  }

  // Make functions global
  window.openJobModal = openJobModal;
  window.closeJobModal = closeJobModal;
  window.modalStop = modalStop;
  window.modalDelete = modalDelete;
  window.modalRerun = modalRerun;

  // Auto-refresh every 3 seconds
  refreshJobs();
  setInterval(refreshJobs, 3000);
}
