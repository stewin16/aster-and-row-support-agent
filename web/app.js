/**
 * Aster & Row — Apple-Grade Glass Chat Client
 * Full Markdown Support (tables, bold, italic, code, lists, blockquotes, badges)
 */

let sessionId = 'sess-' + Math.random().toString(36).slice(2, 9);

// ── Robust Markdown Engine ───────────────────────────────────

// ── Robust Markdown Engine with Marked.js Integration ────────

/**
 * Escapes HTML characters.
 */
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/**
 * Formats inline citations like 【06-international-shipping.md > Supported destinations】
 * or [06-international-shipping.md > Supported destinations] into sleek glass badges.
 */
function formatInlineCitations(text) {
  const sepPattern = '(?:&gt;|>|›)';

  // 1. Full-width Japanese/Chinese brackets: 【filename.md > Section】
  const fullWidthRegex = new RegExp(`【\\s*([a-zA-Z0-9_\\-\\.]+\\.md)\\s*(?:${sepPattern}\\s*([^】]+))?\\s*】\\s*([.,;])?`, 'g');
  text = text.replace(fullWidthRegex, (_, file, sec, punct) => {
    const cleanSec = sec ? sec.replace(/&gt;/g, '>').trim() : '';
    const section = cleanSec ? ` &rsaquo; ${escapeHtml(cleanSec)}` : '';
    const badge = `<span class="inline-cite-badge" title="${escapeHtml(file)}${cleanSec ? ' > ' + escapeHtml(cleanSec) : ''}"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg><span>${escapeHtml(file)}${section}</span></span>`;
    return badge + (punct ? punct : '');
  });

  // 2. Standard markdown bracket citations: [filename.md > Section] (when NOT a markdown link)
  const stdRegex = new RegExp(`(?<!\\!)\\[\\s*([a-zA-Z0-9_\\-\\.]+\\.md)\\s*(?:${sepPattern}\\s*([^\\]]+))?\\s*\\](?!\\()\\s*([.,;])?`, 'g');
  text = text.replace(stdRegex, (_, file, sec, punct) => {
    const cleanSec = sec ? sec.replace(/&gt;/g, '>').trim() : '';
    const section = cleanSec ? ` &rsaquo; ${escapeHtml(cleanSec)}` : '';
    const badge = `<span class="inline-cite-badge" title="${escapeHtml(file)}${cleanSec ? ' > ' + escapeHtml(cleanSec) : ''}"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg><span>${escapeHtml(file)}${section}</span></span>`;
    return badge + (punct ? punct : '');
  });

  // Clean up any stray spaces before punctuation caused by LLM output
  text = text.replace(/\s+([.,!?;:])/g, '$1');

  return text;
}

/**
 * Configure marked.js with custom table wrapper and security settings.
 */
function initMarked() {
  if (typeof marked !== 'undefined') {
    const renderer = new marked.Renderer();

    // Wrap tables in responsive glass container
    renderer.table = function (header, body) {
      return `<div class="md-table-wrap"><table class="md-table"><thead>${header}</thead><tbody>${body}</tbody></table></div>`;
    };

    renderer.tablerow = function (content) {
      return `<tr>${content}</tr>`;
    };

    renderer.tablecell = function (content, flags) {
      const type = flags.header ? 'th' : 'td';
      const align = flags.align ? ` style="text-align:${flags.align}"` : '';
      const cls = flags.header ? ' class="md-th"' : ' class="md-td"';
      return `<${type}${cls}${align}>${content}</${type}>`;
    };

    renderer.link = function (href, title, text) {
      const titleAttr = title ? ` title="${escapeHtml(title)}"` : '';
      return `<a class="md-link" href="${escapeHtml(href)}"${titleAttr} target="_blank" rel="noopener noreferrer">${text}</a>`;
    };

    renderer.code = function (code, infostring) {
      const lang = (infostring || '').match(/\S*/)[0];
      const langCls = lang ? ` class="lang-${escapeHtml(lang)}"` : '';
      return `<pre class="md-code-block"><code${langCls}>${escapeHtml(code)}</code></pre>`;
    };

    renderer.blockquote = function (quote) {
      return `<blockquote class="md-blockquote">${quote}</blockquote>`;
    };

    renderer.hr = function () {
      return '<hr class="md-hr" />';
    };

    marked.setOptions({
      renderer: renderer,
      gfm: true,
      breaks: true,
      pedantic: false
    });
  }
}

// Initialize marked on script execution
initMarked();

/**
 * Main markdown parser function that turns markdown into clean semantic HTML.
 */
function renderMarkdown(md) {
  if (!md) return '';
  let text = md.trim();

  // Clean trailing "Sources:\n- [file > heading]" block if present
  let trailingSourcesHtml = '';
  const sourcesMatch = text.match(/\n+(?:###?\s*)?Sources:\s*\n((?:[-*]\s*\[[^\]]+\](?:\n|$))+)/i);
  if (sourcesMatch) {
    const sourcesContent = sourcesMatch[1];
    const sourceItems = sourcesContent
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.startsWith('-') || line.startsWith('*'))
      .map(line => line.replace(/^[-*]\s*/, ''));

    if (sourceItems.length > 0) {
      const pills = sourceItems.map(item => {
        const clean = item.replace(/^\[|\]$/g, '');
        const parts = clean.split(/[>›]/).map(p => p.trim());
        const filename = parts[0] || '';
        const heading = parts.slice(1).join(' &rsaquo; ') || '';
        return `<span class="cite-pill"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>${escapeHtml(filename)}${heading ? ' &rsaquo; ' + escapeHtml(heading) : ''}</span>`;
      }).join('');
      trailingSourcesHtml = `<div class="sources-attached-row"><span class="cite-label">Sources</span><div class="pills-wrap">${pills}</div></div>`;
    }

    text = text.slice(0, sourcesMatch.index).trim();
  }

  let html = '';

  // Use marked.js if available
  if (typeof marked !== 'undefined') {
    try {
      html = marked.parse(text);
    } catch (e) {
      console.warn('marked.js parse failed, using fallback:', e);
      html = fallbackMarkdownParse(text);
    }
  } else {
    html = fallbackMarkdownParse(text);
  }

  // Format inline citations into sleek glass badges
  html = formatInlineCitations(html);

  if (trailingSourcesHtml) {
    html += trailingSourcesHtml;
  }

  return html;
}

/**
 * High-performance fallback parser for tables, lists, bold, code in case marked.js fails.
 */
function fallbackMarkdownParse(text) {
  let s = escapeHtml(text);
  // Bold
  s = s.replace(/\*\*([\s\S]+?)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/__([\s\S]+?)__/g, '<strong>$1</strong>');
  // Italic
  s = s.replace(/(?<!\*)\*([^*\n]+?)\*(?!\*)/g, '<em>$1</em>');
  s = s.replace(/(?<!_)_([^_\n]+?)_(?!_)/g, '<em>$1</em>');
  // Code
  s = s.replace(/`([^`]+)`/g, '<code class="md-code">$1</code>');
  // Paragraphs
  const paras = s.split(/\n{2,}/).map(p => `<p class="md-p">${p.replace(/\n/g, '<br>')}</p>`);
  return paras.join('');
}


// ── DOM refs ────────────────────────────────────────────────
const chatMessages   = document.getElementById('chat-messages');
const chatForm       = document.getElementById('chat-form');
const userInput      = document.getElementById('user-input');
const traceSidebar   = document.getElementById('trace-sidebar');
const btnToggleTrace = document.getElementById('btn-toggle-trace');
const closeTraceBtn  = document.getElementById('close-trace-btn');
const traceContent   = document.getElementById('trace-content');
const btnReset       = document.getElementById('btn-reset-session');
const btnEval        = document.getElementById('btn-eval-runner');
const evalModal      = document.getElementById('eval-modal');
const closeModalBtn  = document.getElementById('close-modal-btn');
const evalProgress   = document.getElementById('eval-progress');
const evalResults    = document.getElementById('eval-results-container');
const welcomeTime    = document.getElementById('welcome-time');

// ── Init ────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  if (welcomeTime) welcomeTime.textContent = fmt(new Date());

  // Auto-grow textarea
  userInput.addEventListener('input', () => {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 140) + 'px';
  });

  // Keyboard shortcut: Enter submits, Shift+Enter adds newline
  userInput.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      chatForm.requestSubmit();
    }
    if (e.key === 'Enter' && !e.shiftKey && window.innerWidth > 600) {
      e.preventDefault();
      chatForm.requestSubmit();
    }
  });

  // Quick suggestion chips
  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      userInput.value = chip.dataset.prompt;
      userInput.style.height = 'auto';
      userInput.focus();
    });
  });

  // Toggle telemetry drawer
  btnToggleTrace.addEventListener('click', () => {
    traceSidebar.classList.toggle('collapsed');
  });
  closeTraceBtn.addEventListener('click', () => {
    traceSidebar.classList.add('collapsed');
  });

  // Reset session
  btnReset.addEventListener('click', async () => {
    try {
      await fetch('/api/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
    } catch (_) {}
    sessionId = 'sess-' + Math.random().toString(36).slice(2, 9);
    chatMessages.innerHTML = '';
    appendMsg('assistant', 'Session reset. How may I assist you today?', [], false);
    resetTracePanel();
  });

  // Send chat message
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;

    appendMsg('user', text, [], false);
    userInput.value = '';
    userInput.style.height = 'auto';

    const typingRow = appendTyping();

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId })
      });
      const data = await res.json();
      typingRow.remove();

      if (res.ok) {
        appendMsg('assistant', data.content, data.citations || [], data.handoff_recommended || false);
        if (data.trace_id) loadTrace(data.trace_id);
      } else {
        appendMsg('assistant', `Error: ${data.detail || 'Failed to get a response.'}`);
      }
    } catch (err) {
      typingRow.remove();
      appendMsg('assistant', `Network error: ${err.message}`);
    }
  });

  // Evaluation modal
  btnEval.addEventListener('click', openEvalModal);
  closeModalBtn.addEventListener('click', closeEvalModal);
  evalModal.addEventListener('click', (e) => { if (e.target === evalModal) closeEvalModal(); });

  // Keyboard: Esc closes modal / drawer
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeEvalModal();
      if (window.innerWidth <= 900) traceSidebar.classList.add('collapsed');
    }
  });
});

// ── Message rendering ────────────────────────────────────────
function appendMsg(role, text, citations = [], handoff = false) {
  const row = document.createElement('div');
  row.className = `msg-row ${role}`;

  const avatarSvg = role === 'user'
    ? `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`
    : `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>`;

  const sender = role === 'user' ? 'You' : 'Aster & Row';

  let citesHtml = '';
  if (citations && citations.length > 0) {
    const pills = citations.map(c =>
      `<span class="cite-pill"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>${escapeHtml(c.filename)} &rsaquo; ${escapeHtml(c.heading)}</span>`
    ).join('');
    citesHtml = `<div class="citations-row"><span class="cite-label">Sources</span><div class="pills-wrap">${pills}</div></div>`;
  }

  let handoffHtml = '';
  if (handoff) {
    handoffHtml = `<div class="handoff-row">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      <span>Human specialist consultation recommended</span>
    </div>`;
  }

  // Render assistant text through full markdown pipeline; user text as escaped text
  const bodyHtml = role === 'assistant' ? renderMarkdown(text) : `<p class="md-p">${escapeHtml(text)}</p>`;

  row.innerHTML = `
    <div class="msg-avatar">${avatarSvg}</div>
    <div class="msg-bubble">
      <div class="msg-meta">
        <span class="msg-sender">${escapeHtml(sender)}</span>
        <span class="msg-time">${fmt(new Date())}</span>
      </div>
      <div class="msg-body md-content">${bodyHtml}</div>
      ${citesHtml}
      ${handoffHtml}
    </div>
  `;

  chatMessages.appendChild(row);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return row;
}

function appendTyping() {
  const row = document.createElement('div');
  row.className = 'msg-row assistant typing-bubble';
  row.innerHTML = `
    <div class="msg-avatar">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
    </div>
    <div class="msg-bubble">
      <div class="msg-body">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>
    </div>
  `;
  chatMessages.appendChild(row);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return row;
}

// ── Telemetry loading ────────────────────────────────────────
async function loadTrace(traceId) {
  try {
    const res = await fetch(`/api/trace/${traceId}`);
    if (!res.ok) return;
    const t = await res.json();

    traceContent.innerHTML = `
      <div class="trace-card">
        <div class="trace-card-title">Session Info</div>
        <p><b>Trace:</b> ${escapeHtml(t.trace_id)}</p>
        <p><b>Handoff:</b> <span style="color:${t.handoff_recommended ? '#b91c1c' : '#059669'};font-weight:700;">${t.handoff_recommended}</span></p>
      </div>
      <div class="trace-card">
        <div class="trace-card-title">Tool Calls</div>
        <pre class="trace-pre">${escapeHtml(JSON.stringify(t.tool_calls, null, 2))}</pre>
      </div>
      <div class="trace-card">
        <div class="trace-card-title">Retrieved Passages</div>
        <pre class="trace-pre">${escapeHtml(JSON.stringify(t.retrieved_passages, null, 2))}</pre>
      </div>
      <div class="trace-card">
        <div class="trace-card-title">Conflicts & Notes</div>
        <p><b>Conflicts:</b> ${escapeHtml(JSON.stringify(t.conflicts_detected))}</p>
        <p style="margin-top:6px"><b>Notes:</b> ${escapeHtml(JSON.stringify(t.notes))}</p>
      </div>
    `;

    if (window.innerWidth > 900) traceSidebar.classList.remove('collapsed');
  } catch (_) {}
}

function resetTracePanel() {
  traceContent.innerHTML = `
    <div class="trace-empty">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.35"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 14 14"/></svg>
      <p>Send a query to inspect live BM25 passage ranking, tool arguments, conflict flags, and handoff triggers.</p>
    </div>
  `;
}

// ── Evaluation suite modal ───────────────────────────────────
async function openEvalModal() {
  evalModal.classList.remove('hidden');
  evalProgress.classList.remove('hidden');
  evalResults.classList.add('hidden');
  evalResults.innerHTML = '';

  try {
    const res = await fetch('/api/evaluation/run');
    const data = await res.json();
    evalProgress.classList.add('hidden');
    evalResults.classList.remove('hidden');

    let catRows = '';
    for (const [cat, stats] of Object.entries(data.category_breakdown)) {
      const acc = ((stats.passed / stats.total) * 100).toFixed(0);
      catRows += `<tr>
        <td><strong>${escapeHtml(cat)}</strong></td>
        <td>${stats.passed} / ${stats.total}</td>
        <td class="pass-badge">${acc}%</td>
      </tr>`;
    }

    let caseRows = '';
    (data.cases || []).forEach(c => {
      const cls = c.passed ? 'pass-badge' : 'fail-badge';
      const note = c.failures && c.failures.length ? c.failures.join(' · ') : 'All assertions verified';
      caseRows += `<tr>
        <td style="font-family:var(--font-mono);font-size:0.74rem;">${escapeHtml(c.id)}</td>
        <td>${escapeHtml(c.category)}</td>
        <td class="${cls}">${c.passed ? 'PASS' : 'FAIL'}</td>
        <td style="font-size:0.78rem;color:${c.passed ? 'var(--t3)' : '#b91c1c'}">${escapeHtml(note)}</td>
      </tr>`;
    });

    evalResults.innerHTML = `
      <div class="eval-stats">
        <div class="stat-card">
          <div class="stat-number">${data.passed_cases}/${data.total_cases}</div>
          <div class="stat-label">Cases Passed</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">${data.overall_accuracy}%</div>
          <div class="stat-label">Accuracy</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">${Object.keys(data.category_breakdown).length}</div>
          <div class="stat-label">Categories</div>
        </div>
      </div>

      <p class="eval-section-title">Category Breakdown</p>
      <table class="eval-table" style="margin-bottom:24px">
        <thead><tr><th>Category</th><th>Score</th><th>Accuracy</th></tr></thead>
        <tbody>${catRows}</tbody>
      </table>

      <p class="eval-section-title">All 23 Benchmark Cases</p>
      <table class="eval-table">
        <thead><tr><th>Case ID</th><th>Category</th><th>Status</th><th>Details</th></tr></thead>
        <tbody>${caseRows}</tbody>
      </table>
    `;
  } catch (err) {
    evalProgress.innerHTML = `<span style="color:#b91c1c">Evaluation failed: ${err.message}</span>`;
  }
}

function closeEvalModal() {
  evalModal.classList.add('hidden');
}

// ── Helpers ──────────────────────────────────────────────────
function fmt(d) {
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
