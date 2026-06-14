/* ── STATE MANAGEMENT ── */
let selectedPlatform = 'shopee'; // Default platform awal: shopee

/* ── PLATFORM TOGGLE HANDLER ── */
document.querySelectorAll('.platform-btn').forEach(btn => {
  btn.addEventListener('click', function() {
    document.querySelectorAll('.platform-btn').forEach(b => b.classList.remove('active'));
    this.classList.add('active');
    selectedPlatform = this.getAttribute('data-platform');
    
    // Manipulasi kelas body untuk penyesuaian aksen glow dinamis
    document.body.className = `platform-${selectedPlatform}`;
    
    // Konfigurasi visual placeholder & eyebrow tekstual secara interaktif
    const eyebrow = document.querySelector('.hero-eyebrow');
    const footerBrandSpan = document.querySelector('.footer-brand');
    
    if (selectedPlatform === 'tokopedia') {
      eyebrow.textContent = 'Tokopedia Sentiment Intelligence';
      footerBrandSpan.innerHTML = 'Review<span>IN</span> AI &mdash; Tokopedia Sentiment Intelligence';
    } else {
      eyebrow.textContent = 'Shopee Sentiment Intelligence';
      footerBrandSpan.innerHTML = 'Review<span>IN</span> AI &mdash; Shopee Sentiment Intelligence';
    }
  });
});

/* ── CHAR COUNTER ── */
const reviewInput = document.getElementById('reviewInput');
const charCount   = document.getElementById('charCount');
if (reviewInput && charCount) {
  reviewInput.addEventListener('input', () => {
    charCount.textContent = reviewInput.value.length;
  });
}

/* ── CHART INSTANCE ARRAY ── */
let chartInstances = [];

/* ── TOAST ── */
function showToast(msg) {
  const t = document.getElementById('toast');
  if (t) {
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 4000);
  }
}

/* ── MAIN ANALYZE FUNCTION ── */
async function analyzeReview() {
  const text = reviewInput.value.trim();
  if (!text) {
    showToast('⚠️ Mohon masukkan teks ulasan terlebih dahulu.');
    return;
  }

  const btn      = document.getElementById('analyzeBtn');
  const btnText  = btn.querySelector('.btn-text');
  const btnIcon  = btn.querySelector('.btn-icon');

  btn.disabled = true;
  btn.classList.add('loading');
  if (btnText) btnText.textContent = 'Memproses...';
  if (btnIcon) btnIcon.textContent = '⏳';

  try {
    // Pengiriman payload data JSON secara eksplisit ke backend
    const res = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        review: text,
        platform: selectedPlatform
      })
    });

    const data = await res.json();

    // SINKRONISASI VALIDASI COUPLING ERROR HANDLING CLIENT-SERVER
    if (!res.ok || data.status === 'error' || data.error) {
      throw new Error(data.error || `Server returned status ${res.status}`);
    }

    if (data.status !== 'success') {
      throw new Error('Respons klasifikasi tidak valid dari server.');
    }

    const section = document.getElementById('result-section');
    if (section) {
      section.innerHTML = '';
      chartInstances.forEach(c => c.destroy());
      chartInstances = [];
      section.classList.remove('visible');

      if (data.mode === 'link' || data.results) {
          data.results.forEach((item, index) => {
              renderResultCard(item.original_review, item.prediction, item.confidence, item.stars || null, index);
          });
      } else {
          renderResultCard(text, data.prediction, data.confidence, null, 0);
      }

      section.classList.add('visible');
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

  } catch (err) {
    showToast('❌ ' + (err.message || 'Gagal menghubungi server. Pastikan Flask berjalan.'));
  } finally {
    btn.disabled = false;
    btn.classList.remove('loading');
    if (btnText) btnText.textContent = 'Analisis Sentimen';
    if (btnIcon) btnIcon.textContent = '→';
  }
}

/* ── RENDER RESULT MULTIPLE ── */
function renderResultCard(reviewText, prediction, confidence, stars, index) {
  const section = document.getElementById('result-section');
  if (!section) return;

  const cls = prediction === 'Positif' ? 'positive'
            : prediction === 'Negatif' ? 'negative'
            : 'neutral';

  const emoji = prediction === 'Positif' ? '😊'
              : prediction === 'Negatif' ? '😞'
              : '😐';

  let starHtml = '';
  if (stars !== null && stars !== undefined) {
      starHtml = `<div style="color:#f59e0b; font-size:1.15rem; letter-spacing:2px; margin-bottom:8px;">${'★'.repeat(stars)}${'☆'.repeat(5-stars)}</div>`;
  }

  let barsHtml = '';
  const order  = ['Positif', 'Netral', 'Negatif'];
  const clsMap = { Positif: 'positive', Netral: 'neutral', Negatif: 'negative' };

  order.forEach(key => {
    const pct = parseFloat(confidence[key] || 0).toFixed(1);
    barsHtml += `
      <div class="conf-row">
        <span class="conf-row-label">${key}</span>
        <div class="conf-bar-track">
          <div class="conf-bar-fill ${clsMap[key]}" style="width:0%" data-target="${pct}"></div>
        </div>
        <span class="conf-pct">${pct}%</span>
      </div>
    `;
  });

  const cardHtml = `
    <div class="result-card">
      <div class="result-left">
        <div class="result-label">Hasil Analisis Sentimen</div>
        ${starHtml}
        <div class="result-sentiment ${cls}">${prediction}</div>
        <div class="result-badge ${cls}" style="margin-bottom: 20px;">
          <span class="badge-dot"></span>
          <span>${emoji} ${prediction}</span>
        </div>
        
        <div style="padding-left: 14px; border-left: 3px solid var(--border); font-style: italic; color: var(--muted2); font-size: 0.95rem; line-height: 1.6; margin-bottom: 22px;">"${reviewText}"</div>
        
        <div class="confidence-bars">
          ${barsHtml}
        </div>
      </div>
      <div class="chart-wrap">
        <div class="chart-title">Confidence</div>
        <div class="chart-canvas-wrap">
          <canvas id="sentimentChart-${index}" width="160" height="160"></canvas>
        </div>
      </div>
    </div>
  `;

  section.insertAdjacentHTML('beforeend', cardHtml);

  // Trigger transisi bar animasi horizontal secara serentak
  setTimeout(() => {
    const bars = section.querySelectorAll('.conf-bar-fill');
    bars.forEach(bar => {
      bar.style.width = bar.getAttribute('data-target') + '%';
    });
  }, 300);

  renderChart(confidence, cls, index);
}

/* ── CHART RENDERER ── */
function renderChart(confidence, activeCls, index) {
  const canvasEl = document.getElementById(`sentimentChart-${index}`);
  if (!canvasEl) return;
  
  const ctx = canvasEl.getContext('2d');

  const labels = ['Positif', 'Netral', 'Negatif'];
  const values = [
    parseFloat(confidence['Positif'] || 0),
    parseFloat(confidence['Netral']  || 0),
    parseFloat(confidence['Negatif'] || 0),
  ];
  const colors = [
    'rgba(34,197,94,0.85)',
    'rgba(245,158,11,0.85)',
    'rgba(239,68,68,0.85)',
  ];
  const borders = [
    'rgba(34,197,94,1)',
    'rgba(245,158,11,1)',
    'rgba(239,68,68,1)',
  ];

  const chartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: colors,
        borderColor: borders,
        borderWidth: 2,
        hoverOffset: 6,
      }]
    },
    options: {
      cutout: '68%',
      animation: { duration: 800, easing: 'easeInOutQuart' },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.label}: ${ctx.parsed.toFixed(1)}%`
          },
          backgroundColor: '#1e2126',
          borderColor: 'rgba(255,255,255,0.08)',
          borderWidth: 1,
          titleColor: '#9199a6',
          bodyColor: '#f0f0f0',
          padding: 10,
        }
      },
    }
  });
  
  chartInstances.push(chartInstance);
}

/* ── KEYBOARD SHORTCUT Ctrl+Enter ── */
if (reviewInput) {
  reviewInput.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') analyzeReview();
  });
}