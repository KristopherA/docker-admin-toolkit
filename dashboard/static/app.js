const icons = {
  tools: '<path d="m14 5 5 5M13 6l3-3 5 5-3 3M3 21l10-10 3 3L6 24M3 3l5 1 1 4-2 2 4 4M16 16l5 5"/>',
  recipe: '<path d="M9 3h6M10 3v6l-6 10a2 2 0 0 0 2 3h12a2 2 0 0 0 2-3L14 9V3M8 15h8M10 18h.01M14 19h.01"/>',
  pdf: '<path d="M14 3H6v18h12V7zM14 3v5h4M9 12h6M9 15h6M9 18h3"/>',
  pulse: '<path d="M2 12h5l3-8 4 16 3-8h5"/>',
  checks: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m6 9 1 1 2-2m-3 7 1 1 2-2M12 9h5M12 15h5"/>',
  network: '<rect x="8" y="2" width="8" height="5" rx="1"/><rect x="2" y="17" width="7" height="5" rx="1"/><rect x="15" y="17" width="7" height="5" rx="1"/><path d="M12 7v5M5 17v-5h14v5"/>',
  asset: '<path d="m12 3 9 5v9l-9 5-9-5V8zM3 8l9 5 9-5M12 13v9M7 5.8l9 5"/>',
  sandbox: '<rect x="3" y="4" width="18" height="14" rx="2"/><path d="M8 22h8M12 18v4M9 11l2 2 4-4"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3z"/>',
  convert: '<path d="M4 7h13l-3-3M20 17H7l3 3"/>',
  shield: '<path d="M12 2 4 5v6c0 5 3.4 9.3 8 11 4.6-1.7 8-6 8-11V5zM8 12h2l1-3 2 6 1-3h2"/>'
};
let services = [], category = 'All', states = {}, lastCheck = null, fetching = false;
let recent = null;
try { recent = localStorage.getItem('toolkit.lastOpened'); } catch (_) {}
const $ = selector => document.querySelector(selector);

function render() {
  const query = $('#search').value.trim().toLowerCase();
  const visible = services.filter(s => (category === 'All' || s.category === category) && `${s.name} ${s.description} ${s.category}`.toLowerCase().includes(query));
  const container = $('#tools');
  container.replaceChildren();
  for (const service of visible) {
    const state = states[service.id];
    const card = document.createElement('article');
    card.className = `card${service.external ? ' external' : ''}${recent === service.id ? ' recent' : ''}`;
    card.dataset.service = service.id;
    const top = document.createElement('div'); top.className = 'card-top';
    const icon = document.createElement('span'); icon.className = 'tool-icon'; icon.setAttribute('aria-hidden','true');
    icon.innerHTML = `<svg viewBox="0 0 24 26">${icons[service.icon] || icons.tools}</svg>`;
    const number = document.createElement('span'); number.className = 'tool-number'; number.textContent = String(services.indexOf(service) + 1).padStart(2, '0');
    top.append(icon, number);
    const heading = document.createElement('h3'); heading.textContent = service.name;
    const description = document.createElement('p'); description.textContent = service.description;
    const meta = document.createElement('div'); meta.className = 'card-meta';
    const label = document.createElement('span'); label.className = 'category-label'; label.textContent = service.category;
    const status = document.createElement('span');
    if (service.external) { status.className = 'status external'; status.textContent = 'External site'; status.title = 'Third-party website; not monitored. Submissions may be public.'; }
    else { status.className = `status ${state?.state || ''}`;
    status.textContent = ({ready:'Responding', attention:'Needs attention', unavailable:'Unavailable'})[state?.state] || 'Checking';
    status.title = state?.httpCode ? `HTTP ${state.httpCode} · ${state.latencyMs} ms` : 'Waiting for an HTTP response'; }
    meta.append(label, status);
    const link = document.createElement('a'); link.className = 'card-link'; link.href = service.url || `http://localhost:${service.port}/`; link.target = service.external ? '_blank' : 'toolkit-service';
    if (service.external) link.rel = 'noopener noreferrer';
    link.setAttribute('aria-label', service.external ? `Open ${service.name} website in a new tab` : `Open ${service.name} in service tab`);
    const linkText = document.createElement('span'); linkText.textContent = service.external ? 'Open site' : 'Open tool';
    const port = document.createElement('small'); port.textContent = service.external ? new URL(service.url).host.replace(/^(www|app)\./, '') : service.url ? new URL(service.url).host.split('.')[0] : `:${service.port}`; linkText.append(port);
    const arrow = document.createElement('span'); arrow.textContent = '↗'; arrow.setAttribute('aria-hidden', 'true'); link.append(linkText, arrow);
    link.addEventListener('click', () => {
      recent = service.id;
      try { localStorage.setItem('toolkit.lastOpened', recent); } catch (_) {}
      document.querySelectorAll('.card.recent').forEach(c => c.classList.remove('recent'));
      card.classList.add('recent');
    });
    card.append(top, heading, description, meta, link); container.append(card);
  }
  $('#empty').hidden = visible.length > 0;
  $('#result-count').textContent = `${visible.length} ${visible.length === 1 ? 'tool' : 'tools'}`;
  $('#category-title').textContent = category === 'All' ? 'All services' : category;
  $('#tools').setAttribute('aria-busy','false');
  updateAvailability();
}

function updateAvailability() {
  // Keep cards in place during polling so keyboard focus is preserved.
  document.querySelectorAll('.card:not(.external)').forEach(card => {
    const state = states[card.dataset.service];
    const status = card.querySelector('.status');
    status.className = `status ${state?.state || ''}`;
    status.textContent = ({ready:'Responding', attention:'Needs attention', unavailable:'Unavailable'})[state?.state] || 'Checking';
    status.title = state?.httpCode ? `HTTP ${state.httpCode} · ${state.latencyMs} ms` : 'Waiting for an HTTP response';
  });
  const local = services.filter(s => !s.external);
  const count = local.filter(s => states[s.id]?.state === 'ready').length;
  $('#ready-count').replaceChildren(document.createTextNode(lastCheck ? String(count) : '—'));
  const total = document.createElement('span'); total.textContent = ` / ${local.length || 10}`; $('#ready-count').append(total);
  $('#summary-label').textContent = lastCheck ? 'Web services responding' : 'Checking availability';
  $('#last-check').textContent = lastCheck ? `CHECKED ${new Date(lastCheck * 1000).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit'})}` : 'Waiting for first check';
}

async function refresh() {
  if (fetching) return;
  fetching = true; $('#refresh').disabled = true;
  try {
    const response = await fetch('/api/status', {cache:'no-store', signal:AbortSignal.timeout(6000)});
    if (!response.ok) throw new Error('Status unavailable');
    const data = await response.json(); states = data.services; lastCheck = data.checkedAt;
    $('#notice').hidden = true; updateAvailability();
  } catch (_) {
    states = {}; lastCheck = null; updateAvailability();
    $('#notice').textContent = 'Availability checks are temporarily unreachable. You can still open your tools.'; $('#notice').hidden = false;
  } finally { fetching = false; $('#refresh').disabled = false; }
}

$('#categories').addEventListener('click', event => {
  const button = event.target.closest('[data-category]'); if (!button) return;
  category = button.dataset.category;
  document.querySelectorAll('[data-category]').forEach(b => { const active = b === button; b.classList.toggle('active',active); b.setAttribute('aria-pressed', String(active)); });
  render();
});
$('#search').addEventListener('input', render);
$('#refresh').addEventListener('click', refresh);
document.addEventListener('keydown', event => {
  if (event.key === '/' && !['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) { event.preventDefault(); $('#search').focus(); }
  if (event.key === 'Escape' && document.activeElement === $('#search')) { $('#search').value = ''; render(); }
});
$('#copy-command').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText('docker compose exec netbox /opt/netbox/netbox/manage.py createsuperuser'); $('#copy-command').textContent = 'Copied'; }
  catch (_) { $('#copy-command').textContent = 'Select command to copy'; }
  setTimeout(() => { $('#copy-command').textContent = 'Copy'; }, 2500);
});
async function init() {
  try {
    const response = await fetch('/api/services', {signal:AbortSignal.timeout(6000)});
    if (!response.ok) throw new Error('Catalog unavailable');
    services = await response.json(); render(); await refresh();
    setInterval(() => { if (!document.hidden) refresh(); }, 15000);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
  } catch (_) {
    $('#tools').setAttribute('aria-busy','false');
    $('#notice').textContent = 'The service list could not load. Refresh this page after the dashboard has started.'; $('#notice').hidden = false;
  }
}
init();
