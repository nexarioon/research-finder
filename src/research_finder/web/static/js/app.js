/**
 * Research Prospect Finder - Modern Web UI Frontend Logic (Bahasa Indonesia)
 */

class App {
  constructor() {
    this.currentTab = 'dashboard';
    this.scannedBusinesses = [];
    this.scannedPage = 1;
    this.scannedPageSize = 25;
    const savedLat = localStorage.getItem('rf_scan_lat');
    const savedLon = localStorage.getItem('rf_scan_lon');
    this.scanOriginLat = savedLat ? parseFloat(savedLat) : null;
    this.scanOriginLon = savedLon ? parseFloat(savedLon) : null;
    this.scanMap = null;
    this.scanMarker = null;
    this.businessesCache = [];
    this.savedSortCol = 'id';
    this.savedSortDir = 'desc';
    this.savedPage = 1;
    this.savedPageSize = 50;
    this.savedTotalCount = 0;
    this.initTheme();
    this.bindEvents();
    this.loadInitialData();
    this.ensureScanMap();
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

    // Clear auto-detected coordinates when user manually types a location
    document.getElementById('scan-location')?.addEventListener('input', () => {
      const latInput = document.getElementById('scan-latitude');
      const lonInput = document.getElementById('scan-longitude');
      const infoEl = document.getElementById('scan-location-info');
      if (latInput) latInput.value = '';
      if (lonInput) lonInput.value = '';
      if (infoEl) infoEl.style.display = 'none';
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

    if (tabName === 'discover') {
      setTimeout(() => this.ensureScanMap(), 50);
      setTimeout(() => this.ensureScanMap(), 300);
    }
  }

  refreshCurrentTab() {
    if (this.currentTab === 'dashboard') this.loadDashboard();
    else if (this.currentTab === 'discover') this.ensureScanMap();
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

  async loadInitialData() {
    this.loadDashboard();
    this.checkAIStatus();
    this.loadCategoriesDropdown();
    this.loadLastScanLocationFromDB();
  }

  async loadLastScanLocationFromDB() {
    try {
      const res = await fetch('/api/discovery/last-location');
      if (res.ok) {
        const data = await res.json();
        if (data.latitude != null && data.longitude != null) {
          this.scanOriginLat = data.latitude;
          this.scanOriginLon = data.longitude;
          localStorage.setItem('rf_scan_lat', data.latitude.toString());
          localStorage.setItem('rf_scan_lon', data.longitude.toString());
        }
      }
    } catch (err) {
      console.warn('Could not load last scan location from DB:', err);
    }
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

  // --- Map & Geolocation Helpers ---

  ensureScanMap() {
    const mapContainer = document.getElementById('scan-map');
    if (!mapContainer) return;
    if (typeof L === 'undefined') {
      console.warn('Leaflet JS is not loaded yet');
      return;
    }

    // Fix Leaflet default marker icon paths for local bundling
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: '/static/css/images/marker-icon-2x.png',
      iconUrl: '/static/css/images/marker-icon.png',
      shadowUrl: '/static/css/images/marker-shadow.png',
    });

    if (!this.scanMap) {
      // Default center: Jakarta, Indonesia
      const defaultLat = -6.2088;
      const defaultLon = 106.8456;

      this.scanMap = L.map('scan-map', {
        center: [defaultLat, defaultLon],
        zoom: 12,
        zoomControl: true,
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 19,
      }).addTo(this.scanMap);

      // Click on map to set pin
      this.scanMap.on('click', async (e) => {
        const { lat, lng } = e.latlng;
        this.updateMapPin(lat, lng);

        // Update hidden fields
        document.getElementById('scan-latitude').value = lat;
        document.getElementById('scan-longitude').value = lng;

        // Reverse geocode to get address
        const infoEl = document.getElementById('scan-location-info');
        const locationInput = document.getElementById('scan-location');
        try {
          const revRes = await fetch(`/api/discovery/reverse-geocode?lat=${lat}&lon=${lng}`);
          if (revRes.ok) {
            const revData = await revRes.json();
            locationInput.value = revData.address;
          } else {
            locationInput.value = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
          }
        } catch {
          locationInput.value = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
        }
        if (infoEl) {
          infoEl.textContent = `Koordinat dipilih: ${lat.toFixed(6)}, ${lng.toFixed(6)} (via peta)`;
          infoEl.style.display = 'block';
        }
      });
    }

    // Force Leaflet to recalculate tile size in case tab was previously hidden
    setTimeout(() => {
      if (this.scanMap) {
        this.scanMap.invalidateSize();
      }
    }, 100);
  }

  updateMapPin(lat, lon) {
    this.scanOriginLat = lat;
    this.scanOriginLon = lon;
    localStorage.setItem('rf_scan_lat', lat.toString());
    localStorage.setItem('rf_scan_lon', lon.toString());
    if (!this.scanMap) {
      this.ensureScanMap();
    }
    if (!this.scanMap) return;
    if (this.scanMarker) {
      this.scanMarker.setLatLng([lat, lon]);
    } else {
      this.scanMarker = L.marker([lat, lon], { draggable: true }).addTo(this.scanMap);
      // Allow dragging the marker to fine-tune location
      this.scanMarker.on('dragend', async (e) => {
        const pos = e.target.getLatLng();
        document.getElementById('scan-latitude').value = pos.lat;
        document.getElementById('scan-longitude').value = pos.lng;
        const infoEl = document.getElementById('scan-location-info');
        const locationInput = document.getElementById('scan-location');
        try {
          const revRes = await fetch(`/api/discovery/reverse-geocode?lat=${pos.lat}&lon=${pos.lng}`);
          if (revRes.ok) {
            const revData = await revRes.json();
            locationInput.value = revData.address;
          } else {
            locationInput.value = `${pos.lat.toFixed(4)}, ${pos.lng.toFixed(4)}`;
          }
        } catch {
          locationInput.value = `${pos.lat.toFixed(4)}, ${pos.lng.toFixed(4)}`;
        }
        if (infoEl) {
          infoEl.textContent = `Koordinat dipindahkan: ${pos.lat.toFixed(6)}, ${pos.lng.toFixed(6)} (via drag pin)`;
          infoEl.style.display = 'block';
        }
      });
    }
    this.scanMap.setView([lat, lon], Math.max(this.scanMap.getZoom(), 14));
  }

  haversineDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000; // Earth radius in meters
    const toRad = (v) => v * Math.PI / 180;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  formatDistance(meters) {
    if (meters == null) return '-';
    if (meters < 1000) return `${Math.round(meters)} m`;
    return `${(meters / 1000).toFixed(1)} km`;
  }

  // --- 2. Discovery / Scanner ---

  async detectLocation() {
    const btn = document.getElementById('btn-detect-location');
    const locationInput = document.getElementById('scan-location');
    const latInput = document.getElementById('scan-latitude');
    const lonInput = document.getElementById('scan-longitude');
    const infoEl = document.getElementById('scan-location-info');

    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Mendeteksi...`;

    // Clear previous coordinates
    latInput.value = '';
    lonInput.value = '';
    infoEl.style.display = 'none';

    try {
      // Strategy 1: Browser Geolocation API (GPS / Wi-Fi / cell tower)
      if (navigator.geolocation) {
        try {
          const position = await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {
              enableHighAccuracy: true,
              timeout: 10000,
              maximumAge: 300000,  // Cache 5 minutes
            });
          });

          const lat = position.coords.latitude;
          const lon = position.coords.longitude;

          // Reverse geocode to get readable address
          try {
            const revRes = await fetch(`/api/discovery/reverse-geocode?lat=${lat}&lon=${lon}`);
            if (revRes.ok) {
              const revData = await revRes.json();
              locationInput.value = revData.address;
            } else {
              locationInput.value = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
            }
          } catch {
            locationInput.value = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
          }

          latInput.value = lat;
          lonInput.value = lon;
          this.updateMapPin(lat, lon);
          infoEl.textContent = `Koordinat terdeteksi: ${lat.toFixed(6)}, ${lon.toFixed(6)} (via GPS/perangkat)`;
          infoEl.style.display = 'block';
          this.showToast('Lokasi berhasil terdeteksi dari perangkat!', 'success');
          return;

        } catch (geoError) {
          // Browser geolocation failed, fall through to server-side
          console.warn('Browser geolocation failed:', geoError.message);
        }
      }

      // Strategy 2: Server-side IP-based geolocation (fallback)
      const res = await fetch('/api/discovery/auto-location');
      if (res.ok) {
        const data = await res.json();
        locationInput.value = data.address || `${data.latitude.toFixed(4)}, ${data.longitude.toFixed(4)}`;
        latInput.value = data.latitude;
        lonInput.value = data.longitude;
        this.updateMapPin(data.latitude, data.longitude);
        infoEl.textContent = `Koordinat terdeteksi: ${data.latitude.toFixed(6)}, ${data.longitude.toFixed(6)} (via IP address - perkiraan)`;
        infoEl.style.display = 'block';
        this.showToast('Lokasi terdeteksi dari IP (perkiraan). Untuk akurasi lebih, izinkan akses lokasi di browser.', 'info');
      } else {
        throw new Error('Gagal mendeteksi lokasi');
      }

    } catch (err) {
      console.error('Detection error:', err);
      this.showToast('Gagal mendeteksi lokasi otomatis. Pastikan server web telah direstart dan akses lokasi diizinkan.', 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/><circle cx="12" cy="12" r="9"/></svg> Lokasi Saya`;
    }
  }

  async startScan() {
    const loc = document.getElementById('scan-location').value.trim();
    const radius = parseFloat(document.getElementById('scan-radius').value) || 5;
    const catCheckboxes = document.querySelectorAll('input[name="cat"]:checked');
    const categories = Array.from(catCheckboxes).map(c => c.value);
    const lat = document.getElementById('scan-latitude').value;
    const lon = document.getElementById('scan-longitude').value;

    if (!loc && !lat) {
      this.showToast('Masukkan lokasi pencarian atau gunakan tombol "Lokasi Saya"', 'error');
      return;
    }

    const btn = document.getElementById('btn-start-scan');
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Mencari data OSM...`;

    try {
      // Build request body - include coordinates if available
      const body = { radius_km: radius, categories: categories };
      if (lat && lon) {
        body.latitude = parseFloat(lat);
        body.longitude = parseFloat(lon);
        if (loc) body.location = loc;
      } else {
        body.location = loc;
      }

      const res = await fetch('/api/discovery/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Pencarian gagal');
      }

      const data = await res.json();
      let businesses = data.businesses || [];
      this.scannedPage = 1;
      this.scanOriginLat = data.latitude;
      this.scanOriginLon = data.longitude;
      if (data.latitude != null && data.longitude != null) {
        localStorage.setItem('rf_scan_lat', data.latitude.toString());
        localStorage.setItem('rf_scan_lon', data.longitude.toString());
      }

      // Filter by value-added contact criteria if checked
      const filterPhone = document.getElementById('scan-filter-contact')?.checked;
      const filterWeb = document.getElementById('scan-filter-web')?.checked;
      const filterEmail = document.getElementById('scan-filter-email')?.checked;
      const filterHasAny = document.getElementById('scan-filter-has-any')?.checked;

      if (filterPhone) {
        businesses = businesses.filter(b => b.phone && b.phone.trim() !== '');
      }
      if (filterWeb) {
        businesses = businesses.filter(b => b.website && b.website.trim() !== '');
      }
      if (filterEmail) {
        businesses = businesses.filter(b => b.email && b.email.trim() !== '');
      }
      if (filterHasAny) {
        businesses = businesses.filter(b =>
          (b.phone && b.phone.trim() !== '') ||
          (b.website && b.website.trim() !== '') ||
          (b.email && b.email.trim() !== '') ||
          (b.rating && b.rating > 0)
        );
      }

      this.scannedBusinesses = businesses;

      // Compute distance for every business
      this.scannedBusinesses.forEach(b => {
        if (this.scanOriginLat != null && this.scanOriginLon != null && b.latitude != null && b.longitude != null) {
          const dist = this.haversineDistance(this.scanOriginLat, this.scanOriginLon, b.latitude, b.longitude);
          b.distance_m = dist;
          b.distance_text = this.formatDistance(dist);
        }
      });

      // Sort by distance (closest first)
      this.scannedBusinesses.sort((a, b) => (a.distance_m != null ? a.distance_m : Infinity) - (b.distance_m != null ? b.distance_m : Infinity));

      const resultsCard = document.getElementById('scan-results-card');
      resultsCard.style.display = 'block';

      document.getElementById('scan-summary-text').textContent =
        `Ditemukan ${this.scannedBusinesses.length} bisnis di sekitar "${data.location}" (Radius ${radius} km).`;

      this.renderScannedResults();
      this.showToast(`Berhasil menemukan ${this.scannedBusinesses.length} bisnis!`, 'success');
    } catch (err) {
      this.showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg> Mulai Scanning`;
    }
  }

  renderScannedResults() {
    const total = this.scannedBusinesses.length;
    const tbody = document.getElementById('scan-results-body');
    const rangeInfo = document.getElementById('scan-page-range-info');
    const pageIndicator = document.getElementById('scan-page-indicator');
    const btnPrev = document.getElementById('btn-scan-page-prev');
    const btnNext = document.getElementById('btn-scan-page-next');

    if (!tbody) return;

    if (total === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty-state">Tidak ada bisnis ditemukan dengan filter tersebut. Coba perbesar radius atau gunakan nama kota yang lebih umum.</td></tr>`;
      if (rangeInfo) rangeInfo.textContent = 'Menampilkan 0 dari 0 bisnis';
      if (pageIndicator) pageIndicator.textContent = 'Hal 1 / 1';
      if (btnPrev) btnPrev.disabled = true;
      if (btnNext) btnNext.disabled = true;
      return;
    }

    const pageSize = parseInt(this.scannedPageSize, 10) || 0;
    const totalPages = pageSize > 0 ? Math.ceil(total / pageSize) : 1;

    if (this.scannedPage < 1) this.scannedPage = 1;
    if (this.scannedPage > totalPages) this.scannedPage = totalPages;

    const startIdx = pageSize > 0 ? (this.scannedPage - 1) * pageSize : 0;
    const endIdx = pageSize > 0 ? Math.min(startIdx + pageSize, total) : total;
    const pageItems = this.scannedBusinesses.slice(startIdx, endIdx);

    tbody.innerHTML = pageItems.map((b, idx) => {
      // Calculate distance on the fly if needed
      let distVal = b.distance_text;
      if (!distVal && b.distance_m != null) {
        distVal = this.formatDistance(b.distance_m);
      }
      if ((!distVal || distVal === '-') && this.scanOriginLat != null && this.scanOriginLon != null && b.latitude != null && b.longitude != null) {
        const dist = this.haversineDistance(this.scanOriginLat, this.scanOriginLon, b.latitude, b.longitude);
        distVal = this.formatDistance(dist);
      }
      if (!distVal) distVal = '-';

      const gmapsQuery = encodeURIComponent(`${b.name} ${b.address || ''}`.trim());
      const gmapsUrl = `https://www.google.com/maps/search/?api=1&query=${gmapsQuery}`;
      const waLink = b.phone ? this.formatWaUrl(b.phone, `Halo Bapak/Ibu pengelola ${b.name}, perkenalkan saya mahasiswa yang sedang melakukan riset skripsi.`) : null;

      return `
      <tr>
        <td><small style="color:var(--text-muted);">${startIdx + idx + 1}</small></td>
        <td>
          <b>${this.escapeHtml(b.name)}</b>
          <div style="margin-top:4px; display:flex; gap:6px; flex-wrap:wrap;">
            <a href="${gmapsUrl}" target="_blank" class="badge-social badge-maps" title="Lihat Profil & Tempat di Google Maps">📍 Maps</a>
            ${b.website ? `<a href="${b.website}" target="_blank" class="badge-social badge-web" title="Kunjungi Website/Sosmed">🌐 Web</a>` : ''}
            ${waLink ? `<a href="${waLink}" target="_blank" class="badge-social badge-wa" title="Chat WhatsApp">💬 WA</a>` : ''}
            ${b.email ? `<a href="mailto:${b.email}" class="badge-social badge-purple" title="Kirim Email">✉️ Email</a>` : ''}
          </div>
        </td>
        <td><span class="badge badge-purple">${this.escapeHtml(b.category || '-')}</span></td>
        <td><small>${this.escapeHtml(b.address || '-')}</small></td>
        <td><span class="badge" style="background: rgba(99, 102, 241, 0.12); color: var(--accent-primary); border: 1px solid rgba(99, 102, 241, 0.3); font-weight:600; white-space:nowrap;">📍 ${distVal}</span></td>
        <td>
          ${b.website ? `<a href="${b.website}" target="_blank" style="color:var(--accent-primary); text-decoration:underline;">Website</a>` : '<span style="color:var(--text-muted)">-</span>'}
          ${b.phone ? `<br><small>${b.phone}</small>` : ''}
        </td>
      </tr>
    `}).join('');

    if (rangeInfo) {
      rangeInfo.textContent = `Menampilkan ${startIdx + 1}-${endIdx} dari ${total} bisnis`;
    }
    if (pageIndicator) {
      pageIndicator.textContent = `Hal ${this.scannedPage} / ${totalPages}`;
    }
    if (btnPrev) btnPrev.disabled = (this.scannedPage <= 1);
    if (btnNext) btnNext.disabled = (this.scannedPage >= totalPages);
  }

  changeScannedPageSize(val) {
    this.scannedPageSize = parseInt(val, 10) || 0;
    this.scannedPage = 1;
    this.renderScannedResults();
  }

  scannedPrevPage() {
    if (this.scannedPage > 1) {
      this.scannedPage--;
      this.renderScannedResults();
    }
  }

  scannedNextPage() {
    const pageSize = parseInt(this.scannedPageSize, 10) || 0;
    const totalPages = pageSize > 0 ? Math.ceil(this.scannedBusinesses.length / pageSize) : 1;
    if (this.scannedPage < totalPages) {
      this.scannedPage++;
      this.renderScannedResults();
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
      if (this.savedSortCol) params.set('sort_col', this.savedSortCol);
      if (this.savedSortDir) params.set('sort_dir', this.savedSortDir);

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
      if (tbody) tbody.innerHTML = `<tr><td colspan="8" class="empty-state" style="color:var(--accent-danger);">Gagal memuat data: ${this.escapeHtml(err.message)}</td></tr>`;
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
      this.savedSortDir = (col === 'total_score') ? 'desc' : 'asc';
    }
    this.updateSortIcons();
    this.loadSavedBusinesses(1);
  }

  updateSortIcons() {
    const cols = ['id', 'name', 'category', 'address', 'distance', 'total_score'];
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

    if (col === 'distance') {
      this.businessesCache.sort((a, b) => {
        let distA = Infinity;
        let distB = Infinity;
        if (this.scanOriginLat != null && this.scanOriginLon != null) {
          if (a.latitude != null && a.longitude != null) {
            distA = this.haversineDistance(this.scanOriginLat, this.scanOriginLon, a.latitude, a.longitude);
          }
          if (b.latitude != null && b.longitude != null) {
            distB = this.haversineDistance(this.scanOriginLat, this.scanOriginLon, b.latitude, b.longitude);
          }
        }
        return dir === 'asc' ? (distA - distB) : (distB - distA);
      });
      return;
    }

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

      // Calculate distance from scan origin if available
      let distText = '-';
      if (this.scanOriginLat != null && this.scanOriginLon != null && b.latitude != null && b.longitude != null) {
        const dist = this.haversineDistance(this.scanOriginLat, this.scanOriginLon, b.latitude, b.longitude);
        distText = this.formatDistance(dist);
      }

      return `
      <tr>
        <td><code>#${b.id}</code></td>
        <td>
          <b>${this.escapeHtml(b.name)}</b>
          <div style="margin-top:4px; display:flex; gap:6px; flex-wrap:wrap;">
            <a href="${gmapsUrl}" target="_blank" class="badge-social badge-maps" title="Lihat Profil & Tempat di Google Maps">📍 Maps</a>
            ${b.website ? `<a href="${b.website}" target="_blank" class="badge-social badge-web" title="Kunjungi Website">🌐 Web</a>` : ''}
            ${waLink ? `<a href="${waLink}" target="_blank" class="badge-social badge-wa" title="Chat WhatsApp">💬 WA</a>` : ''}
            ${b.email ? `<a href="mailto:${b.email}" class="badge-social badge-purple" title="Kirim Email">✉️ Email</a>` : ''}
          </div>
        </td>
        <td><span class="badge badge-purple">${this.escapeHtml(b.category || '-')}</span></td>
        <td><small>${this.escapeHtml(b.address || '-')}</small></td>
        <td><span class="badge" style="background: rgba(99, 102, 241, 0.12); color: var(--accent-primary); border: 1px solid rgba(99, 102, 241, 0.3); font-weight:600;">📍 ${distText}</span></td>
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
  async updateOutreachFilterCount() {
    const contactCheckboxes = document.querySelectorAll('input[name="bulk_contact"]:checked');
    const contactTypes = Array.from(contactCheckboxes).map(c => c.value);

    const catCheckboxes = document.querySelectorAll('input[name="bulk_cat"]:checked');
    const categories = Array.from(catCheckboxes).map(c => c.value);

    const minScore = parseFloat(document.getElementById('bulk-min-score')?.value) || 0;

    try {
      const res = await fetch('/api/outreach/matching-count', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          categories: categories.length > 0 ? categories : null,
          contact_types: contactTypes.length > 0 ? contactTypes : null,
          min_score: minScore
        })
      });

      if (res.ok) {
        const data = await res.json();
        const matching = data.matching_count || 0;
        const total = data.total_all || 0;

        const slider = document.getElementById('bulk-limit');
        const infoEl = document.getElementById('bulk-matching-info');
        const limitValEl = document.getElementById('bulk-limit-val');

        if (slider) {
          const maxVal = Math.max(1, matching);
          slider.max = maxVal;
          if (parseInt(slider.value, 10) > maxVal) {
            slider.value = maxVal;
          }
          if (limitValEl) {
            limitValEl.textContent = `${slider.value} bisnis`;
          }
        }

        if (infoEl) {
          infoEl.textContent = `Menemukan ${matching} bisnis yang sesuai filter (dari total ${total} bisnis tersimpan). Limit slider maks: ${matching}`;
        }
      }
    } catch (err) {
      console.error('Failed to update outreach matching count:', err);
    }
  }

  async runBulkAIGenerate() {
    const channel = document.getElementById('bulk-channel').value;
    const limit = parseInt(document.getElementById('bulk-limit').value) || 5;

    const contactCheckboxes = document.querySelectorAll('input[name="bulk_contact"]:checked');
    const contactTypes = Array.from(contactCheckboxes).map(c => c.value);

    const catCheckboxes = document.querySelectorAll('input[name="bulk_cat"]:checked');
    const categories = Array.from(catCheckboxes).map(c => c.value);

    const minScore = parseFloat(document.getElementById('bulk-min-score')?.value) || 0;

    const studentName = document.getElementById('bulk-student-name').value.trim() || 'Vega Setiawan';
    const major = document.getElementById('bulk-major').value.trim() || 'S1 Sistem Informasi';
    const university = document.getElementById('bulk-university').value.trim();
    const promptContext = document.getElementById('bulk-prompt-context')?.value.trim();

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
          categories: categories.length > 0 ? categories : null,
          contact_types: contactTypes.length > 0 ? contactTypes : null,
          min_score: minScore,
          student_name: studentName,
          major: major,
          university: university || null,
          prompt_context: promptContext || null
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Gagal generate pesan');
      }

      const data = await res.json();
      this.showToast(`Berhasil menyusun ${data.generated_count} pesan personalisasi AI!`, 'success');
      this.loadOutreach();
    } catch (err) {
      this.showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = `⚡ Generate Pesan Massal AI`;
    }
  }

  async loadOutreach() {
    this.updateOutreachFilterCount();
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
