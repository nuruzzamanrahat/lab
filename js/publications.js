/* publications.js
   Loads data/publications.json and renders the full publications page
   with year grouping, type filtering, and live search.
*/

let allPubs = [];
let activeFilter = 'all';

fetch('data/publications.json')
  .then(r => r.json())
  .then(data => {
    allPubs = data.publications;

    // Stats
    const total     = allPubs.length;
    const citations = allPubs.reduce((s, p) => s + (p.citations || 0), 0);
    const journals  = allPubs.filter(p => p.type === 'journal').length;
    const confs     = allPubs.filter(p => p.type === 'conference').length;

    document.getElementById('total-pubs').textContent      = total;
    document.getElementById('total-citations').textContent  = citations;
    document.getElementById('total-journals').textContent   = journals;
    document.getElementById('total-confs').textContent      = confs;

    if (data.last_updated) {
      document.getElementById('last-updated').textContent =
        `Last synced: ${data.last_updated} · Data from ORCID and Semantic Scholar`;
    }

    renderPubs();
  })
  .catch(() => {
    document.getElementById('pub-list').innerHTML =
      '<p class="no-results">Could not load publications. Please try again later.</p>';
  });

/* ── Render ── */
function renderPubs() {
  const query = (document.getElementById('search-box')?.value || '').toLowerCase().trim();

  let filtered = allPubs.filter(p => {
    const matchesType = activeFilter === 'all' || p.type === activeFilter;
    if (!matchesType) return false;
    if (!query) return true;
    const haystack = [p.title, ...(p.authors || []), p.venue, ...(p.tags || [])].join(' ').toLowerCase();
    return haystack.includes(query);
  });

  if (filtered.length === 0) {
    document.getElementById('pub-list').innerHTML =
      `<p class="no-results">No publications match your search.</p>`;
    return;
  }

  // Group by year descending
  const byYear = {};
  filtered.forEach(p => {
    if (!byYear[p.year]) byYear[p.year] = [];
    byYear[p.year].push(p);
  });

  const years = Object.keys(byYear).sort((a, b) => b - a);

  document.getElementById('pub-list').innerHTML = years.map(year => `
    <div style="margin-bottom:2.5rem;">
      <h3 style="font-family:var(--font-head);font-size:1.4rem;color:var(--ink);margin-bottom:1rem;
                 padding-bottom:0.5rem;border-bottom:2px solid var(--border);">${year}</h3>
      ${byYear[year].map(p => renderPubItem(p)).join('')}
    </div>
  `).join('');

  // Toggle abstracts
  document.querySelectorAll('.toggle-abstract').forEach(btn => {
    btn.addEventListener('click', () => {
      const abstract = btn.closest('.pub-item').querySelector('.pub-abstract');
      const visible  = abstract.style.display === 'block';
      abstract.style.display = visible ? 'none' : 'block';
      btn.textContent = visible ? 'Abstract ▾' : 'Hide ▴';
    });
  });
}

function renderPubItem(p) {
  const typeClass = p.type === 'conference' ? 'conference' : '';
  const authors   = (p.authors || []).join(', ');
  const tags      = (p.tags || []).map(t => `<span class="tag">${t}</span>`).join('');
  const abstract  = p.abstract
    ? `<div class="pub-abstract">${p.abstract}</div>
       <button class="toggle-abstract" style="font-size:0.78rem;font-weight:600;color:var(--accent);
         background:none;border:none;cursor:pointer;padding:0;margin-top:0.25rem;">Abstract ▾</button>`
    : '';

  return `
    <div class="pub-item ${typeClass}">
      <div class="pub-title">
        ${p.url
          ? `<a href="${p.url}" target="_blank" rel="noopener">${p.title}</a>`
          : p.title}
      </div>
      <div class="pub-authors">${authors}</div>
      <div class="pub-venue">${p.venue} &middot; ${p.year}</div>
      ${abstract}
      <div class="pub-meta">
        <div class="pub-tags">
          <span class="tag type-${p.type}">${p.type === 'journal' ? 'Journal' : 'Conference'}</span>
          ${tags}
        </div>
        ${p.citations !== undefined
          ? `<span class="pub-citations">↑ ${p.citations} citations</span>`
          : ''}
        ${p.doi
          ? `<a class="pub-link" href="https://doi.org/${p.doi}" target="_blank" rel="noopener">DOI →</a>`
          : ''}
      </div>
    </div>
  `;
}

/* ── Filter buttons ── */
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeFilter = btn.dataset.filter;
    renderPubs();
  });
});

/* ── Live search ── */
let debounce;
document.getElementById('search-box')?.addEventListener('input', () => {
  clearTimeout(debounce);
  debounce = setTimeout(renderPubs, 220);
});
