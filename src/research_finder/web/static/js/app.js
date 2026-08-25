/**
 * Research Prospect Finder - Modern Web UI Frontend Logic (Bahasa Indonesia)
 */

class App {
  constructor() {
    this.currentTab = 'dashboard';
    this.scannedBusinesses = [];
    this.businessesCache = [];
    this.savedSortCol = 'id';
    this.savedSortDir = 'desc';
    this.savedPage = 1;
    this.savedPageSize = 50;
    this.savedTotalCount = 0;
    this.initTheme();
    this.bindEvents();
    this.loadInitialData();
  }

  // --- Theme Management (Dark / Light) ---
  initTheme() {
    const savedTheme = localStorage.getItem('rf_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    this.updateThemeIcon(savedTheme);
  }

  toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('rf_theme', next);
    this.updateThemeIcon(next);
    this.showToast(`Mode tema diubah ke: ${next === 'dark' ? 'Gelap 🌙' : 'Terang ☀️'}`, 'info');
  }

  updateThemeIcon(theme) {
    const sun = document.getElementById('theme-icon-sun');
    const moon = document.getElementById('theme-icon-moon');
    if (!sun || !moon) return;
    if (theme === 'dark') {
      sun.style.display = 'block';
      moon.style.display = 'none';
    } else {
      sun.style.display = 'none';
      moon.style.display = 'block';
    }
  }

  // --- Event Binding ---
  bindEvents() {
    // Nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const tab = e.currentTarget.getAttribute('data-tab');
        this.switchTab(tab);
      });
    });

    // Theme toggle
    document.getElementById('btn-theme-toggle')?.addEventListener('click', () => this.toggleTheme());

    // Global refresh
    document.getElementById('btn-refresh')?.addEventListener('click', () => {
      this.refreshCurrentTab();
      this.showToast('Data berhasil diperbarui', 'success');
    });
  }

  // --- SPA Tab Switching ---
  switchTab(tabName) {
    this.currentTab = tabName;

    // Update nav active state
    document.querySelectorAll('.nav-btn').forEach(btn => {
      if (btn.getAttribute('data-tab') === tabName) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    // Update panes
    document.querySelectorAll('.tab-pane').forEach(pane => {
      pane.classList.remove('active');
    });
    const targetPane = document.getElementById(`pane-${tabName}`);
    if (targetPane) targetPane.classList.add('active');

    // Update header title
    const titles = {
      dashboard: 'Dashboard Overview',
      discover: 'Discovery / Scanner Bisnis',
      saved: 'Bisnis Tersimpan',
      scoring: 'Scoring & Ranking Kelayakan Riset',
      ai: 'AI Skripsi Insights & Solusi Sistem',
      topics: 'Bank Topik & Ide Skripsi',
      outreach: 'Outreach & Bulk Broadcast',
      export: 'Ekspor Data Riset',
      settings: 'Pengaturan & Konfigurasi'
    };
    const titleEl = document.getElementById('page-title');
    if (titleEl) titleEl.textContent = titles[tabName] || 'Research Prospect Finder';

    // Lazy load tab data
    this.refreshCurrentTab();
  }

  refreshCurrentTab() {
    if (this.currentTab === 'dashboard') this.loadDashboard();
    else if (this.currentTab === 'saved') {
      this.loadCategoriesDropdown();
      this.loadSavedBusinesses();
    }
    else if (this.currentTab === 'scoring') this.loadScoringLeaderboard();
    else if (this.currentTab === 'ai') this.loadAIBusinessDropdown();
    else if (this.currentTab === 'topics') this.loadTopics();
    else if (this.currentTab === 'outreach') this.loadOutreach();
    else if (this.currentTab === 'settings') this.loadSettings();
  }

  loadInitialData() {
    this.loadDashboard();
    this.checkAIStatus();
    this.loadCategoriesDropdown();
  }

  // --- AI Status Check ---
  async checkAIStatus() {
    try {
      const res = await fetch('/api/settings');
      const data = await res.json();
      const badge = document.getElementById('ai-status-badge');
      const text = document.getElementById('ai-status-text');
      if (data.ai_enabled) {
        badge.classList.remove('disabled');
        text.textContent = `AI Aktif (${data.ai_model || 'OmniRoute'})`;
      } else {
        badge.classList.add('disabled');
        text.textContent = 'AI Non-aktif';
      }
    } catch (err) {
      console.error('Failed to check AI status:', err);
    }
  }

  // --- 1. Dashboard ---
  async loadDashboard() {
    try {
      const res = await fetch('/api/stats');
      const stats = await res.json();

      document.getElementById('stat-total-biz').textContent = stats.total_businesses || 0;
      document.getElementById('stat-scored-biz').textContent = stats.scored_businesses || 0;
      document.getElementById('stat-analyzed-biz').textContent = stats.analyzed_businesses || 0;
      document.getElementById('stat-total-topics').textContent = stats.total_topics || 0;

      const tbody = document.getElementById('dash-recent-table-body');
      if (!tbody) return;

      if (!stats.recent_businesses || stats.recent_businesses.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="empty-state">Belum ada bisnis tersimpan. Silakan gunakan menu <b>Discovery</b> untuk mencari bisnis.</td></tr>`;
        return;
      }

      tbody.innerHTML = stats.recent_businesses.map(b => `
        <tr>
          <td><b>${this.escapeHtml(b.name)}</b></td>
          <td><span class="badge badge-purple">${this.escapeHtml(b.category || '-')}</span></td>
          <td>⭐ ${b.rating || '-'} <small>(${b.review_count || 0})</small></td>
          <td>${b.total_score ? `<span class="badge badge-score">${b.total_score.toFixed(1)} / 100</span>` : '<span style="color:var(--text-muted)">-</span>'}</td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="app.showBusinessDetail(${b.id})">Detail</button>
          </td>
        </tr>
      `).join('');
    } catch (err) {
      console.error('Error loading dashboard stats:', err);
    }
  }

  // --- 2. Discovery / Scanner ---
  async startScan() {
    const loc = document.getElementById('scan-location').value.trim();
    const radius = parseFloat(document.getElementById('scan-radius').value) || 5;
    const catCheckboxes = document.querySelectorAll('input[name="cat"]:checked');
    const categories = Array.from(catCheckboxes).map(c => c.value);

    if (!loc) {
      this.showToast('Masukkan lokasi pencarian terlebih dahulu', 'error');
      return;
    }

    const btn = document.getElementById('btn-start-scan');
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Mencari data OSM...`;

    try {
      const res = await fetch('/api/discovery/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ location: loc, radius_km: radius, categories: categories })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Pencarian gagal');
      }

      const data = await res.json();
      this.scannedBusinesses = data.businesses || [];

      const resultsCard = document.getElementById('scan-results-card');
      resultsCard.style.display = 'block';

      document.getElementById('scan-summary-text').textContent =
        `Ditemukan ${this.scannedBusinesses.length} bisnis di sekitar "${data.location}" (Radius ${radius} km).`;

      const tbody = document.getElementById('scan-results-body');
      if (this.scannedBusinesses.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="empty-state">Tidak ada bisnis ditemukan dengan filter tersebut. Coba perbesar radius atau gunakan nama kota yang lebih umum.</td></tr>`;
      } else {
        tbody.innerHTML = this.scannedBusinesses.map(b => `
          <tr>
            <td><b>${this.escapeHtml(b.name)}</b></td>
            <td><span class="badge badge-purple">${this.escapeHtml(b.category || '-')}</span></td>
            <td><small>${this.escapeHtml(b.address || '-')}</small></td>
            <td>
              ${b.website ? `<a href="${b.website}" target="_blank" style="color:var(--accent-primary); text-decoration:underline;">Website</a>` : '<span style="color:var(--text-muted)">-</span>'}
              ${b.phone ? `<br><small>${b.phone}</small>` : ''}
            </td>
            <td>⭐ ${b.rating || '-'} (${b.review_count || 0})</td>
          </tr>
        `).join('');
      }

      this.showToast(`Berhasil menemukan ${this.scannedBusinesses.length} bisnis!`, 'success');
    } catch (err) {
      this.showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg> Mulai Scanning`;
    }
  }

  clearScannedResults() {
    this.scannedBusinesses = [];
    const resultsCard = document.getElementById('scan-results-card');
    if (resultsCard) resultsCard.style.display = 'none';
    this.showToast('Data hasil scan telah dibersihkan', 'info');
  }

  async saveScannedResults() {
    if (!this.scannedBusinesses || this.scannedBusinesses.length === 0) return;

    const btn = document.getElementById('btn-save-scanned');
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Menyimpan...`;

    try {
      const res = await fetch('/api/discovery/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ businesses: this.scannedBusinesses })
      });
      const data = await res.json();
      this.showToast(`Berhasil menyimpan ${data.saved_count} bisnis ke database!`, 'success');
      this.switchTab('saved');
    } catch (err) {
      this.showToast('Gagal menyimpan hasil: ' + err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = `Simpan Semua ke Database`;
    }
  }

  // --- 3. Saved Businesses ---
  async loadCategoriesDropdown() {
    const select = document.getElementById('filter-category');
    if (!select) return;
    try {
      const res = await fetch('/api/categories');
      const cats = await res.json();
      const currentVal = select.value;
      select.innerHTML = '<option value="all">📁 Semua Kategori</option>' +
        cats.map(c => `<option value="${this.escapeQuotes(c)}">${this.escapeHtml(c)}</option>`).join('');
      if (currentVal && cats.includes(currentVal)) {
        select.value = currentVal;
      }
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  }

  async loadSavedBusinesses(page = 1) {
    this.savedPage = page;
    const search = document.getElementById('saved-search')?.value || '';
    const category = document.getElementById('filter-category')?.value || 'all';
    const ratingVal = document.getElementById('filter-rating')?.value || '0';
    const minScore = parseFloat(document.getElementById('filter-score')?.value) || 0;

    const hasPhone = document.getElementById('tag-wa')?.checked || false;
    const hasWebsite = document.getElementById('tag-web')?.checked || false;
    const hasEmail = document.getElementById('tag-email')?.checked || false;
    const hasSocial = document.getElementById('tag-social')?.checked || false;
    const hasAI = document.getElementById('tag-ai')?.checked || false;

    const tbody = document.getElementById('saved-table-body');
    if (!tbody) return;

    try {
      const params = new URLSearchParams({
        page: this.savedPage,
        limit: this.savedPageSize,
        paged: 'true'
      });
      if (search) params.set('search', search);
      if (category && category !== 'all') params.set('category', category);
      if (ratingVal === 'none') {
        params.set('rating_type', 'none');
      } else {
        const minRating = parseFloat(ratingVal) || 0;
        if (minRating > 0) params.set('min_rating', minRating);
      }
      if (minScore > 0) params.set('min_score', minScore);
      if (hasPhone) params.set('has_phone', 'true');
      if (hasWebsite) params.set('has_website', 'true');
      if (hasEmail) params.set('has_email', 'true');
      if (hasSocial) params.set('has_social', 'true');
      if (hasAI) params.set('has_ai', 'true');

      const res = await fetch(`/api/businesses?${params.toString()}`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();

      if (Array.isArray(data)) {
        this.businessesCache = data;
        this.savedTotalCount = data.length;
      } else {
        this.businessesCache = data.items || [];
        this.savedTotalCount = data.total !== undefined ? data.total : this.businessesCache.length;
      }

      // Update pagination toolbar numbers
      const showingCountEl = document.getElementById('saved-showing-count');
      const totalCountEl = document.getElementById('saved-total-count');
      if (showingCountEl) showingCountEl.textContent = this.businessesCache.length;
      if (totalCountEl) totalCountEl.textContent = this.savedTotalCount.toLocaleString('id-ID');

      const totalPages = this.savedPageSize > 0 ? Math.max(1, Math.ceil(this.savedTotalCount / this.savedPageSize)) : 1;
      const pageIndicator = document.getElementById('saved-page-indicator');
      if (pageIndicator) pageIndicator.textContent = `Hal ${this.savedPage} / ${totalPages}`;

      const btnPrev = document.getElementById('btn-page-prev');
      const btnNext = document.getElementById('btn-page-next');
      if (btnPrev) btnPrev.disabled = this.savedPage <= 1;
      if (btnNext) btnNext.disabled = this.savedPage >= totalPages || this.savedPageSize === 0;

      this.applySavedSorting();
      this.renderSavedBusinesses();
    } catch (err) {
      console.error('Failed to load saved businesses:', err);
      const tbody = document.getElementById('saved-table-body');
      if (tbody) tbody.innerHTML = `<tr><td colspan="7" class="empty-state" style="color:var(--accent-danger);">Gagal memuat data: ${this.escapeHtml(err.message)}</td></tr>`;
    }
  }

  resetSavedFilters() {
    const searchInput = document.getElementById('saved-search');
    if (searchInput) searchInput.value = '';
    const catSelect = document.getElementById('filter-category');
    if (catSelect) catSelect.value = 'all';
    const ratingSelect = document.getElementById('filter-rating');
    if (ratingSelect) ratingSelect.value = '0';
    const scoreSelect = document.getElementById('filter-score');
    if (scoreSelect) scoreSelect.value = '0';

    ['tag-wa', 'tag-web', 'tag-email', 'tag-social', 'tag-ai'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.checked = false;
    });

    this.showToast('Filter telah direset', 'info');
    this.loadSavedBusinesses(1);
  }

  changePageSize(newSize) {
    this.savedPageSize = parseInt(newSize);
    this.loadSavedBusinesses(1);
  }

  prevPage() {
    if (this.savedPage > 1) {
      this.loadSavedBusinesses(this.savedPage - 1);
    }
  }

  nextPage() {
    const totalPages = this.savedPageSize > 0 ? Math.ceil(this.savedTotalCount / this.savedPageSize) : 1;
    if (this.savedPage < totalPages) {
      this.loadSavedBusinesses(this.savedPage + 1);
    }
  }

  async clearAllSavedBusinesses() {
    const confirmPrompt = confirm(
      `⚠️ PERINGATAN HAPUS SEMUA DATA:\n\nApakah Anda yakin ingin menghapus SELURUH bisnis tersimpan (${this.savedTotalCount.toLocaleString('id-ID')} data) di database beserta seluruh riwayat analisis AI, topik, dan outreach?\n\nTindakan ini bersifat permanen dan TIDAK DAPAT dibatalkan!`
    );
    if (!confirmPrompt) return;

    try {
      const res = await fetch('/api/businesses', { method: 'DELETE' });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}: Gagal menghapus`);
      }
      const data = await res.json();
      const countText = data.deleted_count !== undefined ? `${data.deleted_count} ` : '';
      this.showToast(`Berhasil menghapus ${countText}bisnis dari database!`, 'success');
      this.loadSavedBusinesses(1);
      this.loadDashboard();
    } catch (err) {
      this.showToast('Gagal menghapus semua bisnis: ' + err.message, 'error');
    }
  }

  sortSaved(col) {
    if (this.savedSortCol === col) {
      this.savedSortDir = this.savedSortDir === 'asc' ? 'desc' : 'asc';
    } else {
      this.savedSortCol = col;
      this.savedSortDir = (col === 'total_score' || col === 'rating') ? 'desc' : 'asc';
    }
    this.updateSortIcons();
    this.applySavedSorting();
    this.renderSavedBusinesses();
  }

  updateSortIcons() {
    const cols = ['id', 'name', 'category', 'address', 'rating', 'total_score'];
    cols.forEach(c => {
      const icon = document.getElementById(`sort-icon-${c}`);
      if (!icon) return;
      if (c === this.savedSortCol) {
        icon.textContent = this.savedSortDir === 'asc' ? '▲' : '▼';
        icon.classList.add('active');
      } else {
        icon.textContent = '↕';
        icon.classList.remove('active');
      }
    });
  }

  applySavedSorting() {
    if (!this.businessesCache || this.businessesCache.length === 0) return;
    const col = this.savedSortCol || 'id';
    const dir = this.savedSortDir || 'desc';

    this.businessesCache.sort((a, b) => {
      let valA = a[col];
      let valB = b[col];

      // Handle nulls / undefined (push to bottom)
      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;

      if (typeof valA === 'string' || typeof valB === 'string') {
        const strA = String(valA || '');
        const strB = String(valB || '');
        const cmp = strA.localeCompare(strB, 'id', { sensitivity: 'base' });
        return dir === 'asc' ? cmp : -cmp;
      } else {
        const numA = Number(valA) || 0;
        const numB = Number(valB) || 0;
        return dir === 'asc' ? (numA - numB) : (numB - numA);
      }
    });
  }

  renderSavedBusinesses() {
    const tbody = document.getElementById('saved-table-body');
    if (!tbody) return;

    if (!this.businessesCache || this.businessesCache.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="empty-state">Tidak ada data bisnis tersimpan.</td></tr>`;
      return;
    }

    tbody.innerHTML = this.businessesCache.map(b => {
      const waLink = this.formatWaUrl(b.phone, `Halo Bapak/Ibu pengelola ${b.name}, perkenalkan saya mahasiswa yang sedang melakukan riset skripsi.`);
      const gmapsQuery = encodeURIComponent(`${b.name} ${b.address || ''}`.trim());
      const gmapsUrl = `https://www.google.com/maps/search/?api=1&query=${gmapsQuery}`;

      return `
      <tr>
        <td><code>#${b.id}</code></td>
        <td>
          <b>${this.escapeHtml(b.name)}</b>
          <div style="margin-top:4px; display:flex; gap:6px; flex-wrap:wrap;">
            <a href="${gmapsUrl}" target="_blank" class="badge-social badge-maps" title="Lihat Profil, Ulasan & Rating di Google Maps">📍 Maps</a>
            ${b.website ? `<a href="${b.website}" target="_blank" class="badge-social badge-web" title="Kunjungi Website">🌐 Web</a>` : ''}
            ${waLink ? `<a href="${waLink}" target="_blank" class="badge-social badge-wa" title="Chat WhatsApp">💬 WA</a>` : ''}
            ${b.email ? `<a href="mailto:${b.email}" class="badge-social badge-purple" title="Kirim Email">✉️ Email</a>` : ''}
          </div>
        </td>
        <td><span class="badge badge-purple">${this.escapeHtml(b.category || '-')}</span></td>
        <td><small>${this.escapeHtml(b.address || '-')}</small></td>
        <td>${(b.rating && b.rating > 0) ? `⭐ ${b.rating} <small>(${b.review_count || 0})</small>` : `<span style="color:var(--text-muted);" title="Data OpenStreetMap tidak memiliki ulasan rating bintang">-</span>`}</td>
        <td>${b.total_score ? `<span class="badge badge-score">${b.total_score.toFixed(1)}</span>` : '<span style="color:var(--text-muted)">-</span>'}</td>
        <td style="white-space:nowrap;">
          <button class="btn btn-secondary btn-sm" onclick="app.showBusinessDetail(${b.id})" title="Lihat Detail">Detail</button>
          <button class="btn btn-primary btn-sm" onclick="app.analyzeSingleBusiness(${b.id})" title="Analisis AI">AI</button>
          ${b.website ? `<button class="btn btn-secondary btn-sm" onclick="app.auditWebsite(${b.id})" title="Audit Website & Sosmed">🔍 Audit</button>` : ''}
          <button class="btn btn-danger btn-sm" onclick="app.deleteBusiness(${b.id})" title="Hapus">✕</button>
        </td>
      </tr>
    `}).join('');
  }

  async auditWebsite(bizId) {
    this.showToast('Sedang mengaudit website & mengekstrak media sosial...', 'info');
    try {
      const res = await fetch(`/api/businesses/${bizId}/audit-website`, { method: 'POST' });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Audit website gagal');
      }
      const data = await res.json();
      this.showToast('Audit website & kontak selesai!', 'success');
      this.loadSavedBusinesses();
      this.showBusinessDetail(bizId);
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  async deleteBusiness(id) {
    if (!confirm('Apakah Anda yakin ingin menghapus bisnis ini beserta seluruh analisisnya?')) return;
    try {
      await fetch(`/api/businesses/${id}`, { method: 'DELETE' });
      this.showToast('Bisnis berhasil dihapus', 'info');
      this.loadSavedBusinesses();
      this.loadDashboard();
    } catch (err) {
      this.showToast('Gagal menghapus bisnis', 'error');
    }
  }

  // --- 4. Scoring & Ranking ---
  async loadScoringLeaderboard() {
    const tbody = document.getElementById('scoring-table-body');
    if (!tbody) return;

    try {
      const res = await fetch('/api/businesses?limit=100');
      const list = await res.json();

      const scoredList = list.filter(b => b.total_score !== null).sort((a, b) => b.total_score - a.total_score);

      if (scoredList.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="empty-state">Belum ada bisnis yang discore. Klik tombol "Score Semua yang Belum Dinilai" di atas.</td></tr>`;
        return;
      }

      tbody.innerHTML = scoredList.map((b, idx) => {
        const bd = b.score_breakdown || {};
        return `
          <tr>
            <td><b>#${idx + 1}</b></td>
            <td><b>${this.escapeHtml(b.name)}</b></td>
            <td><span class="badge badge-purple">${this.escapeHtml(b.category || '-')}</span></td>
            <td><span class="badge badge-score" style="font-size:13px;">${b.total_score.toFixed(1)} / 100</span></td>
            <td>
              <small style="color:var(--text-secondary);">
                Size: <b>${bd.business_size || 0}</b> |
                Complex: <b>${bd.operational_complexity || 0}</b> |
                Online: <b>${bd.online_presence || 0}</b> |
                Contact: <b>${bd.contact_availability || 0}</b>
              </small>
            </td>
            <td>
              <button class="btn btn-primary btn-sm" onclick="app.analyzeSingleBusiness(${b.id})">Analisis AI</button>
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      console.error('Error loading leaderboard:', err);
    }
  }

  async runScoreAll() {
    this.showToast('Menjalankan algoritma scoring...', 'info');
    try {
      const res = await fetch('/api/scoring/run-all', { method: 'POST' });
      const data = await res.json();
      this.showToast(`Scoring selesai! ${data.scored_count} bisnis berhasil dinilai.`, 'success');
      this.loadScoringLeaderboard();
      this.loadDashboard();
    } catch (err) {
      this.showToast('Gagal menjalankan scoring: ' + err.message, 'error');
    }
  }

  // --- 5. AI Insights (Bahasa Indonesia) ---
  async loadAIBusinessDropdown() {
    const select = document.getElementById('ai-select-business');
    if (!select) return;

    try {
      const res = await fetch('/api/businesses');
      const list = await res.json();

      if (list.length === 0) {
        select.innerHTML = '<option value="">Belum ada bisnis tersimpan</option>';
        return;
      }

      select.innerHTML = list.map(b => `
        <option value="${b.id}">${b.name} (${b.category || 'Umum'}) - Skor: ${b.total_score ? b.total_score.toFixed(1) : '-'}</option>
      `).join('');
    } catch (err) {
      console.error('Failed to load businesses for AI select:', err);
    }
  }

  analyzeSingleBusiness(bizId) {
    this.switchTab('ai');
    const select = document.getElementById('ai-select-business');
    if (select) select.value = bizId;
    this.runAIAnalysis();
  }

  async runAIAnalysis() {
    const select = document.getElementById('ai-select-business');
    const bizId = select?.value;
    if (!bizId) {
      this.showToast('Pilih bisnis yang ingin dianalisis terlebih dahulu', 'error');
      return;
    }

    const btn = document.getElementById('btn-run-ai');
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Menganalisis dengan AI (Bahasa Indonesia)...`;

    try {
      const res = await fetch(`/api/ai/analyze/${bizId}`, { method: 'POST' });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Analisis AI gagal');
      }

      const data = await res.json();
      const card = document.getElementById('ai-results-card');
      card.style.display = 'block';

      document.getElementById('ai-result-model').textContent = `Model: ${data.model_used || 'Gemini'}`;
      document.getElementById('ai-res-problems').textContent = data.operational_problems || 'Tidak ditemukan.';
      document.getElementById('ai-res-opportunities').textContent = data.info_system_opportunities || 'Tidak ditemukan.';
      document.getElementById('ai-res-relevance').textContent = data.research_relevance || 'Tidak ditemukan.';

      // Topics grid
      const topicsGrid = document.getElementById('ai-res-topics-grid');
      if (data.research_topics && data.research_topics.length > 0) {
        topicsGrid.innerHTML = data.research_topics.map((topic, i) => `
          <div class="topic-card">
            <div>
              <div class="topic-title">💡 ${this.escapeHtml(topic)}</div>
            </div>
            <div class="topic-footer">
              <button class="btn btn-secondary btn-sm" onclick="app.copyToClipboard('${this.escapeQuotes(topic)}')">Salin Judul</button>
            </div>
          </div>
        `).join('');
      } else {
        topicsGrid.innerHTML = '<div class="empty-state">Tidak ada topik digenerate.</div>';
      }

      // Questions
      const qList = document.getElementById('ai-res-questions');
      if (data.validation_questions && data.validation_questions.length > 0) {
        qList.innerHTML = data.validation_questions.map(q => `<li>${this.escapeHtml(q)}</li>`).join('');
      } else {
        qList.innerHTML = '<li>Tidak ada pertanyaan validasi.</li>';
      }

      this.showToast('Analisis AI berhasil digenerate (Bahasa Indonesia)!', 'success');
      this.loadDashboard();
    } catch (err) {
      this.showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a8 8 0 0 0-8 8c0 3.36 2.08 6.24 5 7.42V20a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-2.58c2.92-1.18 5-4.06 5-7.42a8 8 0 0 0-8-8z"/></svg> Jalankan Analisis AI`;
    }
  }

  // --- 6. Topics ---
  async loadTopics() {
    const container = document.getElementById('topics-cards-container');
    if (!container) return;

    try {
      const res = await fetch('/api/topics');
      const topics = await res.json();

      if (topics.length === 0) {
        container.innerHTML = `<div class="empty-state" style="grid-column: 1/-1;">Belum ada topik riset. Jalankan <b>AI Skripsi Insights</b> pada bisnis yang Anda pilih untuk membuat rekomendasi topik secara otomatis.</div>`;
        return;
      }

      container.innerHTML = topics.map(t => `
        <div class="topic-card ${t.is_saved ? 'saved' : ''}">
          <div>
            <div class="topic-header">
              <span class="badge badge-purple">${this.escapeHtml(t.business_name)}</span>
              <button class="btn btn-sm ${t.is_saved ? 'btn-primary' : 'btn-secondary'}" onclick="app.toggleSaveTopic(${t.id})" title="Favoritkan Topik">
                ${t.is_saved ? '⭐ Tersimpan' : '☆ Simpan'}
              </button>
            </div>
            <h4 class="topic-title">${this.escapeHtml(t.title)}</h4>
            ${t.problem_statement ? `<p class="topic-desc"><b>Masalah:</b> ${this.escapeHtml(t.problem_statement)}</p>` : ''}
            ${t.proposed_system ? `<p class="topic-desc"><b>Solusi SI:</b> ${this.escapeHtml(t.proposed_system)}</p>` : ''}
          </div>
          <div class="topic-footer">
            <button class="btn btn-secondary btn-sm" onclick="app.copyToClipboard('${this.escapeQuotes(t.title)}')">Salin Judul</button>
            <button class="btn btn-danger btn-sm" onclick="app.deleteTopic(${t.id})">Hapus</button>
          </div>
        </div>
      `).join('');
    } catch (err) {
      console.error('Failed to load topics:', err);
    }
  }

  async toggleSaveTopic(topicId) {
    try {
      await fetch(`/api/topics/${topicId}/toggle-save`, { method: 'PUT' });
      this.loadTopics();
      this.showToast('Status topik diperbarui', 'info');
    } catch (err) {
      this.showToast('Gagal mengubah status topik', 'error');
    }
  }

  async deleteTopic(topicId) {
    if (!confirm('Hapus topik ini?')) return;
    try {
      await fetch(`/api/topics/${topicId}`, { method: 'DELETE' });
      this.loadTopics();
      this.showToast('Topik dihapus', 'info');
    } catch (err) {
      this.showToast('Gagal menghapus topik', 'error');
    }
  }

  openModalAddTopic() {
    this.populateBizSelectInModal('modal-topic-biz-select');
    this.openModal('modal-add-topic');
  }

  async submitNewTopic() {
    const bizId = document.getElementById('modal-topic-biz-select').value;
    const title = document.getElementById('modal-topic-title').value.trim();
    const problem = document.getElementById('modal-topic-problem').value.trim();
    const system = document.getElementById('modal-topic-system').value.trim();

    if (!bizId || !title) return;

    try {
      await fetch('/api/topics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_id: parseInt(bizId),
          title: title,
          problem_statement: problem,
          proposed_system: system,
          is_saved: true
        })
      });
      this.closeModal('modal-add-topic');
      this.loadTopics();
      this.showToast('Topik skripsi baru berhasil ditambahkan!', 'success');
    } catch (err) {
      this.showToast('Gagal menyimpan topik: ' + err.message, 'error');
    }
  }

  // --- 7. Outreach & AI Bulk Generator ---
  async runBulkAIGenerate() {
    const channel = document.getElementById('bulk-channel').value;
    const limit = parseInt(document.getElementById('bulk-limit').value) || 5;
    const filterContact = document.getElementById('bulk-filter-contact').value;
    const studentName = document.getElementById('bulk-student-name').value.trim() || 'Mahasiswa Peneliti';
    const university = document.getElementById('bulk-university').value.trim() || 'Perguruan Tinggi';

    const btn = document.getElementById('btn-generate-bulk');
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Menyusun ${limit} pesan personalisasi AI...`;

    try {
      const res = await fetch('/api/outreach/generate-bulk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          limit: limit,
          channel: channel,
          only_with_contacts: filterContact === 'with_contact',
          student_name: studentName,
          university: university
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Gagal generate pesan');
      }

      const data = await res.json();
      this.showToast(`Berhasil menyusun ${data.generated_count} pesan personalisasi untuk ${channel.toUpperCase()}! 🎉`, 'success');
      this.loadOutreach();
    } catch (err) {
      this.showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = `⚡ Generate Pesan Massal AI`;
    }
  }

  async loadOutreach() {
    const tbody = document.getElementById('outreach-table-body');
    if (!tbody) return;

    try {
      const res = await fetch('/api/outreach');
      const items = await res.json();

      if (items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="empty-state">Belum ada draft outreach. Klik "⚡ Generate Pesan Massal AI" di atas untuk membuat pesan personalisasi secara otomatis.</td></tr>`;
        return;
      }

      tbody.innerHTML = items.map(o => {
        const waLink = this.formatWaUrl(o.email_to, o.email_body);
        return `
        <tr>
          <td>
            <b>${this.escapeHtml(o.business_name)}</b>
            <div style="font-size:11px; color:var(--text-muted); margin-top:2px;">ID Bisnis: #${o.business_id}</div>
          </td>
          <td>
            <code>${this.escapeHtml(o.email_to || '-')}</code>
          </td>
          <td>
            <b>${this.escapeHtml(o.email_subject || 'Pesan Permohonan')}</b>
            <div class="broadcast-body-preview" style="margin-top:6px; max-height:80px; overflow-y:auto;">${this.escapeHtml(o.email_body)}</div>
          </td>
          <td>
            <select class="form-select" style="padding:4px 8px; font-size:12px; width:auto;" onchange="app.updateOutreachStatus(${o.id}, this.value)">
              <option value="draft" ${o.status === 'draft' ? 'selected' : ''}>📝 Draft</option>
              <option value="ready" ${o.status === 'ready' ? 'selected' : ''}>⏳ Siap Kirim</option>
              <option value="sent" ${o.status === 'sent' ? 'selected' : ''}>✉️ Terkirim</option>
              <option value="replied" ${o.status === 'replied' ? 'selected' : ''}>💬 Dibalas</option>
              <option value="interested" ${o.status === 'interested' ? 'selected' : ''}>🎉 Bersedia / ACC</option>
              <option value="declined" ${o.status === 'declined' ? 'selected' : ''}>❌ Menolak</option>
            </select>
          </td>
          <td style="white-space:nowrap;">
            ${waLink ? `<a href="${waLink}" target="_blank" class="btn btn-whatsapp btn-sm" style="text-decoration:none;">💬 Chat WA</a>` : ''}
            <button class="btn btn-secondary btn-sm" onclick="app.copyToClipboard('${this.escapeQuotes(o.email_body)}')">Salin Pesan</button>
            <button class="btn btn-danger btn-sm" onclick="app.deleteOutreach(${o.id})">✕</button>
          </td>
        </tr>
      `}).join('');
    } catch (err) {
      console.error('Failed to load outreach:', err);
    }
  }

  async updateOutreachStatus(id, status) {
    try {
      await fetch(`/api/outreach/${id}/status?status=${status}`, { method: 'PUT' });
      this.showToast('Status outreach diperbarui', 'info');
    } catch (err) {
      this.showToast('Gagal update status outreach', 'error');
    }
  }

  async deleteOutreach(id) {
    if (!confirm('Hapus draft outreach ini?')) return;
    try {
      await fetch(`/api/outreach/${id}`, { method: 'DELETE' });
      this.loadOutreach();
      this.showToast('Draft dihapus', 'info');
    } catch (err) {
      this.showToast('Gagal menghapus draft', 'error');
    }
  }

  openModalAddOutreach() {
    this.populateBizSelectInModal('modal-outreach-biz-select');
    this.openModal('modal-add-outreach');
  }

  onOutreachBizChange(bizId) {
    const biz = this.businessesCache.find(b => b.id == bizId);
    if (biz) {
      document.getElementById('modal-outreach-email').value = biz.phone || biz.email || '';
      document.getElementById('modal-outreach-body').value =
`Kepada Yth. Pimpinan / Pengelola ${biz.name},

Perkenalkan saya mahasiswa yang sedang melakukan penyusunan tugas akhir / skripsi di bidang Sistem Informasi.

Berdasarkan pengamatan kami terhadap aktivitas operasional ${biz.name}, kami sangat tertarik untuk mengajukan ${biz.name} sebagai studi kasus penelitian perancangan dan pengembangan sistem informasi.

Adapun penelitian ini bertujuan untuk membantu memetakan kebutuhan digitalisasi proses bisnis dan memberikan rekomendasi solusi teknologi yang tepat guna tanpa memungut biaya apapun.

Besar harapan kami untuk dapat berdiskusi atau melakukan wawancara singkat terkait kesediaan pihak ${biz.name}.

Atas perhatian dan kerja sama Bapak/Ibu, kami ucapkan terima kasih.

Hormat kami,
[Nama Mahasiswa]
[Kontak WhatsApp / Telp]`;
    }
  }

  async submitNewOutreach() {
    const bizId = document.getElementById('modal-outreach-biz-select').value;
    const email = document.getElementById('modal-outreach-email').value.trim();
    const subject = document.getElementById('modal-outreach-subject').value.trim();
    const body = document.getElementById('modal-outreach-body').value.trim();

    if (!bizId || !email || !subject || !body) return;

    try {
      await fetch('/api/outreach', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_id: parseInt(bizId),
          email_to: email,
          email_subject: subject,
          email_body: body,
          status: 'draft'
        })
      });
      this.closeModal('modal-add-outreach');
      this.loadOutreach();
      this.showToast('Draft pesan berhasil disimpan!', 'success');
    } catch (err) {
      this.showToast('Gagal membuat outreach: ' + err.message, 'error');
    }
  }

  // --- 8. Business Detail Modal ---
  async showBusinessDetail(bizId) {
    this.openModal('modal-biz-detail');
    const content = document.getElementById('modal-biz-content');
    content.innerHTML = '<div class="empty-state"><span class="spinner"></span> Memuat detail...</div>';

    try {
      const res = await fetch(`/api/businesses/${bizId}`);
      const data = await res.json();
      const b = data.business;
      const wa = data.website_analysis;
      document.getElementById('modal-biz-name').textContent = b.name;

      const waLink = this.formatWaUrl(b.phone, `Halo Bapak/Ibu pengelola ${b.name}, perkenalkan saya mahasiswa yang sedang melakukan riset skripsi.`);

      // Render social links if found
      let socialBadgesHtml = '';
      if (wa && wa.social_links && wa.social_links.length > 0) {
        socialBadgesHtml = `
          <div style="margin-top:10px;">
            <b>📱 Media Sosial Terdeteksi:</b>
            <div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:4px;">
              ${wa.social_links.map(link => {
                let label = 'Tautan';
                let cls = 'badge-social badge-web';
                if (link.includes('instagram.com')) { label = 'Instagram'; cls = 'badge-social badge-ig'; }
                else if (link.includes('facebook.com') || link.includes('fb.com')) { label = 'Facebook'; cls = 'badge-social badge-fb'; }
                else if (link.includes('linkedin.com')) { label = 'LinkedIn'; cls = 'badge-social badge-li'; }
                else if (link.includes('wa.me') || link.includes('whatsapp.com')) { label = 'WhatsApp'; cls = 'badge-social badge-wa'; }
                return `<a href="${link}" target="_blank" class="${cls}">🔗 ${label}</a>`;
              }).join('')}
            </div>
          </div>
        `;
      }

      content.innerHTML = `
        <div style="margin-bottom:20px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <span class="badge badge-purple" style="font-size:13px;">${b.category || 'Umum'}</span>
            ${b.total_score ? `<span class="badge badge-score" style="font-size:14px;">Skor Riset: ${b.total_score.toFixed(1)}/100</span>` : ''}
          </div>
          <p><b>📍 Alamat:</b> ${b.address || '-'}</p>
          <p>
            <b>📞 Kontak:</b> ${b.phone || '-'}
            ${waLink ? `<a href="${waLink}" target="_blank" class="btn btn-whatsapp btn-sm" style="margin-left:8px; text-decoration:none;">💬 Chat WhatsApp</a>` : ''}
          </p>
          <p><b>✉️ Email:</b> ${b.email || '-'}</p>
          <p>
            <b>🌐 Website:</b> ${b.website ? `<a href="${b.website}" target="_blank" style="color:var(--accent-primary);">${b.website}</a>` : '-'}
            ${b.website ? `<button class="btn btn-secondary btn-sm" style="margin-left:8px;" onclick="app.auditWebsite(${b.id})">🔍 Audit Web & Sosmed</button>` : ''}
          </p>
          <p>
            <b>⭐ Rating Google/Maps:</b> ${b.rating || '-'} (${b.review_count || 0} ulasan)
            <a href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent((b.name + ' ' + (b.address || '')).trim())}" target="_blank" class="btn btn-secondary btn-sm" style="margin-left:8px; text-decoration:none;">📍 Buka di Google Maps</a>
          </p>
          ${socialBadgesHtml}
        </div>

        ${data.ai_analysis ? `
          <div class="ai-insight-box">
            <h4>💡 Analisis AI Terakhir (${data.ai_analysis.model_used || 'Gemini'})</h4>
            <p><b>Masalah Operasional:</b> ${data.ai_analysis.operational_problems || '-'}</p>
            <p style="margin-top:6px;"><b>Peluang SI:</b> ${data.ai_analysis.info_system_opportunities || '-'}</p>
            <p style="margin-top:6px;"><b>Relevansi Riset:</b> ${data.ai_analysis.research_relevance || '-'}</p>
          </div>
        ` : `
          <div class="card" style="text-align:center; padding:16px; margin-bottom:16px;">
            <p style="color:var(--text-muted); margin-bottom:10px;">Belum ada analisis AI untuk bisnis ini.</p>
            <button class="btn btn-primary btn-sm" onclick="app.closeModal('modal-biz-detail'); app.analyzeSingleBusiness(${b.id});">Jalankan Analisis AI Sekarang</button>
          </div>
        `}

        <div style="margin-top:16px;">
          <h4 style="font-size:14px; margin-bottom:8px; font-weight:700;">Catatan Tambahan:</h4>
          <textarea id="modal-biz-notes" class="form-control" rows="3" placeholder="Tambahkan catatan khusus penelitian...">${b.notes || ''}</textarea>
          <button class="btn btn-secondary btn-sm" style="margin-top:8px;" onclick="app.saveBusinessNotes(${b.id})">Simpan Catatan</button>
        </div>
      `;
    } catch (err) {
      content.innerHTML = '<div class="empty-state">Gagal memuat detail bisnis.</div>';
    }
  }

  async saveBusinessNotes(bizId) {
    const notes = document.getElementById('modal-biz-notes')?.value || '';
    try {
      await fetch(`/api/businesses/${bizId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: notes })
      });
      this.showToast('Catatan berhasil disimpan', 'success');
    } catch (err) {
      this.showToast('Gagal menyimpan catatan', 'error');
    }
  }

  // --- 9. Settings ---
  async loadSettings() {
    const tbody = document.getElementById('settings-table-body');
    if (!tbody) return;

    try {
      const res = await fetch('/api/settings');
      const data = await res.json();

      tbody.innerHTML = `
        <tr><td><b>Status AI Provider</b></td><td><span class="badge ${data.ai_enabled ? 'badge-success' : 'badge-warning'}">${data.ai_enabled ? 'Aktif' : 'Non-aktif'}</span></td></tr>
        <tr><td><b>AI Model</b></td><td><code>${data.ai_model || '-'}</code></td></tr>
        <tr><td><b>AI Base URL</b></td><td><code>${data.ai_base_url || '-'}</code></td></tr>
        <tr><td><b>API Key</b></td><td><code>${data.ai_api_key_masked || 'Tersedia'}</code></td></tr>
        <tr><td><b>Database URL</b></td><td><code>${data.database_url || '-'}</code></td></tr>
        <tr><td><b>Default Radius Scan</b></td><td>${data.default_radius_km} km</td></tr>
      `;
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  }

  // --- Helpers ---
  formatWaUrl(phone, text = '') {
    if (!phone) return null;
    let clean = String(phone).replace(/[^0-9]/g, '');
    if (clean.startsWith('0')) clean = '62' + clean.slice(1);
    else if (clean.startsWith('8')) clean = '62' + clean;
    if (clean.length < 9) return null;
    return `https://wa.me/${clean}?text=${encodeURIComponent(text)}`;
  }

  populateBizSelectInModal(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;
    if (this.businessesCache.length === 0) {
      select.innerHTML = '<option value="">Memuat daftar bisnis...</option>';
      fetch('/api/businesses').then(r => r.json()).then(list => {
        this.businessesCache = list;
        select.innerHTML = list.map(b => `<option value="${b.id}">${b.name}</option>`).join('');
      });
    } else {
      select.innerHTML = this.businessesCache.map(b => `<option value="${b.id}">${b.name}</option>`).join('');
    }
  }

  openModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.add('active');
  }

  closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.remove('active');
  }

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${this.escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(20px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
      this.showToast('Pesan berhasil disalin ke clipboard! 📋', 'success');
    }).catch(() => {
      this.showToast('Gagal menyalin teks', 'error');
    });
  }

  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  escapeQuotes(str) {
    if (!str) return '';
    return String(str).replace(/'/g, "\\'").replace(/"/g, '&quot;');
  }
}

// Global instance initialization
document.addEventListener('DOMContentLoaded', () => {
  window.app = new App();
});
