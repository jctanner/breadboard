(() => {
  const state = { page: 1, pageSize: 50, timer: null };
  const $ = (id) => document.getElementById(id);

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, (char) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[char]));
  }

  function filters() {
    return {
      q: $('tickets-query').value.trim(),
      source: $('tickets-source').value,
      type: $('tickets-type').value,
      category: $('tickets-category').value,
      state: $('tickets-state').value.trim(),
      label: $('tickets-label').value.trim(),
      project: $('tickets-project').value.trim(),
    };
  }

  function render(data) {
    const body = $('tickets-body');
    body.innerHTML = '';
    for (const ticket of data.tickets || []) {
      const row = document.createElement('tr');
      row.className = 'hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors';
      const labels = (ticket.labels || []).map((label) =>
        `<span class="badge badge-default mr-1">${escapeHtml(label)}</span>`).join('');
      row.innerHTML = `
        <td class="px-4 py-2.5"><span class="badge badge-default">${escapeHtml(ticket.source)}</span></td>
        <td class="px-4 py-2.5 text-gray-600 dark:text-gray-400">${escapeHtml(ticket.type)}</td>
        <td class="px-4 py-2.5"><a href="${escapeHtml(ticket.url)}" target="_blank" rel="noopener" class="text-primary-600 dark:text-primary-400 hover:underline font-medium">${escapeHtml(ticket.key)}</a></td>
        <td class="px-4 py-2.5 max-w-md truncate" title="${escapeHtml(ticket.title)}">${escapeHtml(ticket.title)}</td>
        <td class="px-4 py-2.5 text-gray-600 dark:text-gray-400">${escapeHtml(ticket.state)}</td>
        <td class="px-4 py-2.5">${labels || '<span class="text-gray-400">—</span>'}</td>
        <td class="px-4 py-2.5 text-gray-600 dark:text-gray-400">${escapeHtml(ticket.updated || '')}</td>`;
      body.appendChild(row);
    }
    const pages = data.pages || 0;
    $('tickets-count').textContent = `${data.total || 0} ticket${data.total === 1 ? '' : 's'}`;
    $('tickets-page').textContent = pages ? `Page ${data.page} of ${pages}` : 'No results';
    $('tickets-previous').disabled = data.page <= 1;
    $('tickets-next').disabled = !pages || data.page >= pages;
    const errors = data.errors || [];
    const errorBox = $('tickets-errors');
    if (errors.length) {
      errorBox.textContent = `Some sources could not be loaded: ${errors.map((item) => `${item.source}: ${item.message}`).join(' · ')}`;
      errorBox.classList.remove('hidden');
    } else {
      errorBox.textContent = '';
      errorBox.classList.add('hidden');
    }
  }

  async function loadTickets() {
    const params = new URLSearchParams({ page: state.page, page_size: state.pageSize, ...filters() });
    $('tickets-count').textContent = 'Loading tickets…';
    try {
      const response = await fetch(`/api/tickets?${params}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      render(await response.json());
    } catch (error) {
      $('tickets-count').textContent = 'Unable to load tickets';
      $('tickets-errors').textContent = error.message;
      $('tickets-errors').classList.remove('hidden');
    }
  }

  function scheduleReload() {
    clearTimeout(state.timer);
    state.timer = setTimeout(() => { state.page = 1; loadTickets(); }, 250);
  }

  ['tickets-query', 'tickets-state', 'tickets-label', 'tickets-project'].forEach((id) => $(id).addEventListener('input', scheduleReload));
  ['tickets-source', 'tickets-category'].forEach((id) => $(id).addEventListener('change', scheduleReload));
  $('tickets-type').addEventListener('input', scheduleReload);
  $('tickets-page-size').addEventListener('change', () => {
    state.pageSize = Number($('tickets-page-size').value);
    state.page = 1;
    loadTickets();
  });
  $('tickets-refresh').addEventListener('click', loadTickets);
  $('tickets-previous').addEventListener('click', () => { if (state.page > 1) { state.page -= 1; loadTickets(); } });
  $('tickets-next').addEventListener('click', () => { state.page += 1; loadTickets(); });
  loadTickets();
})();
