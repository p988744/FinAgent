/**
 * FinAgent Renderer Process Application Logic
 *
 * Handles UI interactions, API calls, and result display
 */

// State management
const state = {
  isBackendReady: false,
  isQuerying: false,
  currentQuery: null
};

// DOM Elements
const elements = {
  statusDot: document.getElementById('statusDot'),
  statusText: document.getElementById('statusText'),
  queryInput: document.getElementById('queryInput'),
  submitBtn: document.getElementById('submitBtn'),
  btnText: document.querySelector('.btn-text'),
  btnLoader: document.querySelector('.btn-loader'),
  resultsContainer: document.getElementById('resultsContainer'),
  welcomeMessage: document.getElementById('welcomeMessage'),
  resultsContent: document.getElementById('resultsContent'),
  appVersion: document.getElementById('appVersion')
};

/**
 * Initialize the application
 */
async function initializeApp() {
  console.log('Initializing FinAgent application...');

  // Set app version
  const appInfo = await window.electronAPI.getAppInfo();
  elements.appVersion.textContent = `v${appInfo.version}`;

  // Check backend status
  await checkBackendStatus();

  // Set up event listeners
  setupEventListeners();

  // Start status polling
  startStatusPolling();
}

/**
 * Check backend connection status
 */
async function checkBackendStatus() {
  try {
    const result = await window.electronAPI.getBackendStatus();

    if (result.success && result.data.status === 'ready') {
      updateStatus('connected', '後端已連接');
      state.isBackendReady = true;
      elements.submitBtn.disabled = false;
    } else {
      updateStatus('error', '後端未就緒');
      state.isBackendReady = false;
      elements.submitBtn.disabled = true;
    }
  } catch (error) {
    console.error('Failed to check backend status:', error);
    updateStatus('error', '連接失敗');
    state.isBackendReady = false;
    elements.submitBtn.disabled = true;
  }
}

/**
 * Update status indicator
 */
function updateStatus(status, text) {
  elements.statusDot.className = `status-dot ${status}`;
  elements.statusText.textContent = text;
}

/**
 * Start polling backend status
 */
function startStatusPolling() {
  setInterval(async () => {
    if (!state.isQuerying) {
      await checkBackendStatus();
    }
  }, 10000); // Check every 10 seconds
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
  // Submit button click
  elements.submitBtn.addEventListener('click', handleQuerySubmit);

  // Enter key in textarea (Ctrl+Enter or Cmd+Enter)
  elements.queryInput.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleQuerySubmit();
    }
  });

  // Example query buttons
  document.querySelectorAll('.example-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      elements.queryInput.value = btn.dataset.query;
      handleQuerySubmit();
    });
  });

  // Auto-resize textarea
  elements.queryInput.addEventListener('input', () => {
    elements.queryInput.style.height = 'auto';
    elements.queryInput.style.height = `${elements.queryInput.scrollHeight}px`;
  });
}

/**
 * Handle query submission
 */
async function handleQuerySubmit() {
  const queryText = elements.queryInput.value.trim();

  if (!queryText) {
    showError('請輸入查詢內容');
    return;
  }

  if (!state.isBackendReady) {
    showError('後端未就緒，請稍候再試');
    return;
  }

  if (state.isQuerying) {
    return;
  }

  // Update UI to loading state
  state.isQuerying = true;
  state.currentQuery = queryText;
  elements.submitBtn.disabled = true;
  elements.btnText.style.display = 'none';
  elements.btnLoader.style.display = 'inline-block';
  elements.queryInput.disabled = true;

  // Hide welcome message, show loading
  elements.welcomeMessage.style.display = 'none';
  elements.resultsContent.style.display = 'block';
  elements.resultsContent.innerHTML = createLoadingHTML();

  try {
    console.log('Submitting query:', queryText);

    // Submit query to backend
    const result = await window.electronAPI.submitQuery(queryText);

    if (result.success) {
      // Display results
      displayResults(result.data);
    } else {
      throw new Error(result.error || '查詢失敗');
    }
  } catch (error) {
    console.error('Query failed:', error);
    showError(`查詢失敗: ${error.message}`);
  } finally {
    // Reset UI state
    state.isQuerying = false;
    elements.submitBtn.disabled = false;
    elements.btnText.style.display = 'inline';
    elements.btnLoader.style.display = 'none';
    elements.queryInput.disabled = false;
  }
}

/**
 * Display query results
 */
function displayResults(answer) {
  console.log('Displaying results:', answer);

  // Build HTML for results
  const html = `
    <div class="result-card">
      <div class="result-header">
        <div class="result-summary">${escapeHtml(answer.summary || '查詢結果')}</div>
        <span class="confidence-badge confidence-${getConfidenceClass(answer.confidence)}">
          ${formatConfidence(answer.confidence)}
        </span>
      </div>

      <div class="result-content">
        ${formatContent(answer.content)}
      </div>

      ${answer.citations && answer.citations.length > 0 ? formatCitations(answer.citations) : ''}
    </div>
  `;

  elements.resultsContent.innerHTML = html;
}

/**
 * Format answer content
 */
function formatContent(content) {
  if (!content) return '<p>無內容</p>';

  // Split by sections if the content contains section markers
  const sections = content.split(/\n(?=#{1,3}\s)/).filter(s => s.trim());

  if (sections.length > 1) {
    return sections.map(section => {
      const lines = section.split('\n');
      const title = lines[0].replace(/^#+\s/, '');
      const body = lines.slice(1).join('\n');

      return `
        <div class="result-section">
          <h3>${escapeHtml(title)}</h3>
          ${formatText(body)}
        </div>
      `;
    }).join('');
  }

  return `<div class="result-section">${formatText(content)}</div>`;
}

/**
 * Format text with proper line breaks and lists
 */
function formatText(text) {
  if (!text) return '';

  // Convert bullet points to HTML list
  const lines = text.split('\n').filter(l => l.trim());
  let html = '';
  let inList = false;

  for (const line of lines) {
    const trimmed = line.trim();

    if (trimmed.startsWith('•') || trimmed.startsWith('-') || trimmed.startsWith('*')) {
      if (!inList) {
        html += '<ul>';
        inList = true;
      }
      const content = trimmed.substring(1).trim();
      html += `<li>${escapeHtml(content)}</li>`;
    } else {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
      if (trimmed) {
        html += `<p>${escapeHtml(trimmed)}</p>`;
      }
    }
  }

  if (inList) {
    html += '</ul>';
  }

  return html;
}

/**
 * Format citations
 */
function formatCitations(citations) {
  if (!citations || citations.length === 0) return '';

  const citationItems = citations.map((citation, index) => {
    return `
      <div class="citation-item">
        [${index + 1}] ${escapeHtml(citation.title || citation.source || '未知來源')}
        ${citation.date ? ` (${citation.date})` : ''}
        ${citation.source_path ? `<br>來源: ${escapeHtml(citation.source_path)}` : ''}
      </div>
    `;
  }).join('');

  return `
    <div class="citations">
      <h3>引用來源</h3>
      ${citationItems}
    </div>
  `;
}

/**
 * Get confidence CSS class
 */
function getConfidenceClass(confidence) {
  if (!confidence) return 'low';

  const lower = confidence.toLowerCase();
  if (lower.includes('高') || lower === 'high') return 'high';
  if (lower.includes('中') || lower === 'medium') return 'medium';
  return 'low';
}

/**
 * Format confidence level
 */
function formatConfidence(confidence) {
  if (!confidence) return '未知信心';

  const lower = confidence.toLowerCase();
  if (lower === 'high' || lower.includes('高')) return '高信心';
  if (lower === 'medium' || lower.includes('中')) return '中信心';
  if (lower === 'low' || lower.includes('低')) return '低信心';

  return confidence;
}

/**
 * Create loading HTML
 */
function createLoadingHTML() {
  return `
    <div class="loading-message">
      <div class="loading-spinner"></div>
      <p>正在處理查詢，請稍候...</p>
      <p style="font-size: 13px; color: var(--text-tertiary);">
        多代理系統正在分析您的查詢
      </p>
    </div>
  `;
}

/**
 * Show error message
 */
function showError(message) {
  elements.resultsContent.style.display = 'block';
  elements.welcomeMessage.style.display = 'none';

  elements.resultsContent.innerHTML = `
    <div class="error-message">
      <strong>錯誤</strong><br>
      ${escapeHtml(message)}
    </div>
  `;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Initialize app when DOM is ready
 */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}
