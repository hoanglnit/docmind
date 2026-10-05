/* DocMind — app.js */
'use strict';

// ── API helpers ──────────────────────────────────────────────────────────────

const api = {
  async get(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async post(url, body) {
    const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async put(url, body) {
    const r = await fetch(url, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async patch(url, body) {
    const r = await fetch(url, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async del(url) {
    const r = await fetch(url, { method: 'DELETE' });
    if (!r.ok) throw new Error(await r.text());
  },
};

// ── Toast ────────────────────────────────────────────────────────────────────

function toast(msg, type = 'ok') {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.className = `toast ${type} show`;
  setTimeout(() => { el.classList.remove('show'); }, 3200);
}

// ── Health check ─────────────────────────────────────────────────────────────

async function checkHealth() {
  const badge = document.getElementById('health-badge');
  if (!badge) return;
  try {
    const h = await api.get('/api/v1/health');
    badge.className = 'health-badge ' + (h.ollama?.ok ? 'ok' : 'err');
    badge.title = h.ollama?.ok
      ? `Ollama OK — ${h.ollama.models?.join(', ')}`
      : `Ollama lỗi: ${h.ollama?.error}`;
  } catch {
    badge.className = 'health-badge err';
  }
}

// ── Markdown-lite renderer ───────────────────────────────────────────────────

function renderMd(text) {
  // Very simple: escape HTML, render code blocks and inline code, newlines to <br>
  const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  let out = esc(text);
  // Code blocks
  out = out.replace(/```[\w]*\n?([\s\S]*?)```/g, (_, code) =>
    `<pre><code>${code}</code></pre>`);
  // Inline code
  out = out.replace(/`([^`]+)`/g, (_, c) => `<code>${c}</code>`);
  // Bold
  out = out.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Line breaks
  out = out.replace(/\n/g, '<br>');
  return out;
}

// ═══════════════════════════════════════════════════════════════════════════
// CHAT PAGE
// ═══════════════════════════════════════════════════════════════════════════

if (document.getElementById('session-list')) {
  let currentSession = null;
  let isStreaming = false;
  let allDocs = [];
  let allScenarios = [];

  // ── Load sessions ──────────────────────────────────────────────────────

  async function loadSessions() {
    const sessions = await api.get('/api/v1/sessions');
    renderSessionList(sessions);
  }

  function renderSessionList(sessions) {
    const list = document.getElementById('session-list');
    if (!sessions.length) {
      list.innerHTML = '<div class="empty-state-small">Chưa có phiên nào</div>';
      return;
    }
    list.innerHTML = sessions.map(s => `
      <div class="session-item ${currentSession?.id === s.id ? 'active' : ''}"
           data-id="${s.id}" onclick="openSession('${s.id}')">
        <div class="session-item-name">${esc(s.name)}</div>
        <div class="session-item-meta">
          <span>${s.documents.length} tài liệu</span>
          <span>${s.message_count} tin</span>
        </div>
      </div>
    `).join('');
  }

  const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

  // ── Open session ───────────────────────────────────────────────────────

  window.openSession = async function(sessionId) {
    try {
      const session = await api.get(`/api/v1/sessions/${sessionId}`);
      currentSession = session;

      document.getElementById('chat-empty').style.display = 'none';
      document.getElementById('chat-active').style.display = 'flex';
      document.getElementById('chat-session-name').textContent = session.name;
      document.getElementById('chat-session-meta').textContent =
        `${session.documents.length} tài liệu · Kịch bản: ${session.scenario?.name || 'mặc định'}`;

      // Reload session list to update active state
      const sessions = await api.get('/api/v1/sessions');
      renderSessionList(sessions);

      // Load messages
      await loadMessages(sessionId);

      // Enable input
      const input = document.getElementById('msg-input');
      const btnSend = document.getElementById('btn-send');
      input.disabled = false;
      btnSend.disabled = false;
      input.focus();
    } catch (e) {
      toast('Lỗi mở phiên: ' + e.message, 'err');
    }
  };

  // ── Load messages ──────────────────────────────────────────────────────

  async function loadMessages(sessionId) {
    const msgs = await api.get(`/api/v1/sessions/${sessionId}/messages`);
    const area = document.getElementById('messages-area');
    area.innerHTML = '';
    msgs.forEach(m => appendMessage(m.role, m.content, m.sources || []));
    scrollToBottom();
  }

  function appendMessage(role, content, sources = []) {
    const area = document.getElementById('messages-area');
    const el = document.createElement('div');
    el.className = `message ${role}`;
    const avatar = role === 'user'
      ? '<div class="msg-avatar">U</div>'
      : '<div class="msg-avatar">AI</div>';
    const sourcesHtml = buildSourcesHtml(sources);
    el.innerHTML = `
      ${avatar}
      <div class="msg-body">
        <div class="msg-bubble">${renderMd(content)}</div>
        ${sourcesHtml}
      </div>
    `;
    area.appendChild(el);
    return el;
  }

  function buildSourcesHtml(sources) {
    if (!sources || !sources.length) return '';
    const items = sources.map((s, i) => `
      <div class="source-card">
        <div class="source-ref">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          ${esc(s.source)}${s.page ? ` — tr. ${s.page}` : ''}
        </div>
        <div class="source-text">${esc(s.text)}</div>
      </div>
    `).join('');
    const id = 'src-' + Math.random().toString(36).slice(2);
    return `
      <div class="msg-sources">
        <button class="sources-toggle" onclick="toggleSources(this, '${id}')">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
          ${sources.length} nguồn tham khảo
        </button>
        <div class="sources-list" id="${id}">${items}</div>
      </div>
    `;
  }

  window.toggleSources = function(btn, id) {
    btn.classList.toggle('open');
    document.getElementById(id).classList.toggle('open');
  };

  function scrollToBottom() {
    const area = document.getElementById('messages-area');
    area.scrollTop = area.scrollHeight;
  }

  // ── Send message (SSE streaming) ───────────────────────────────────────

  async function sendMessage() {
    if (!currentSession || isStreaming) return;
    const input = document.getElementById('msg-input');
    const content = input.value.trim();
    if (!content) return;

    isStreaming = true;
    input.value = '';
    input.style.height = 'auto';
    document.getElementById('btn-send').disabled = true;

    appendMessage('user', content);
    scrollToBottom();

    // Create streaming assistant bubble
    const area = document.getElementById('messages-area');
    const el = document.createElement('div');
    el.className = 'message assistant';
    el.innerHTML = `
      <div class="msg-avatar">AI</div>
      <div class="msg-body">
        <div class="msg-bubble" id="streaming-bubble"><span class="msg-cursor"></span></div>
      </div>
    `;
    area.appendChild(el);
    scrollToBottom();

    const bubble = document.getElementById('streaming-bubble');
    let fullText = '';
    let sources = [];

    try {
      const response = await fetch(`/api/v1/sessions/${currentSession.id}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      });

      if (!response.ok) throw new Error('Lỗi server: ' + response.status);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;
          try {
            const event = JSON.parse(raw);
            if (event.type === 'token') {
              fullText += event.content;
              bubble.innerHTML = renderMd(fullText) + '<span class="msg-cursor"></span>';
              scrollToBottom();
            } else if (event.type === 'done') {
              sources = event.sources || [];
            }
          } catch { /* ignore parse errors */ }
        }
      }
    } catch (e) {
      fullText += `\n[Lỗi: ${e.message}]`;
      toast('Lỗi kết nối: ' + e.message, 'err');
    }

    // Finalize bubble
    bubble.innerHTML = renderMd(fullText);
    const msgBody = el.querySelector('.msg-body');
    if (sources.length) {
      const div = document.createElement('div');
      div.innerHTML = buildSourcesHtml(sources);
      msgBody.appendChild(div.firstElementChild);
    }

    isStreaming = false;
    document.getElementById('btn-send').disabled = false;
    input.focus();
    scrollToBottom();

    // Refresh session list (message count updated)
    const sessions = await api.get('/api/v1/sessions');
    renderSessionList(sessions);
  }

  // ── Input handling ─────────────────────────────────────────────────────

  const msgInput = document.getElementById('msg-input');
  const btnSend = document.getElementById('btn-send');

  if (msgInput) {
    msgInput.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
    msgInput.addEventListener('input', () => {
      msgInput.style.height = 'auto';
      msgInput.style.height = Math.min(msgInput.scrollHeight, 160) + 'px';
    });
  }
  if (btnSend) btnSend.addEventListener('click', sendMessage);

  // ── New session modal ──────────────────────────────────────────────────

  async function openNewSessionModal() {
    [allDocs, allScenarios] = await Promise.all([
      api.get('/api/v1/documents'),
      api.get('/api/v1/scenarios'),
    ]);

    // Populate scenario dropdown
    const sel = document.getElementById('ns-scenario');
    sel.innerHTML = '<option value="">— Không dùng kịch bản —</option>';
    allScenarios.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.id;
      opt.textContent = s.name + (s.is_default ? ' (mặc định)' : '');
      if (s.is_default) opt.selected = true;
      sel.appendChild(opt);
    });

    // Populate doc checklist
    const list = document.getElementById('ns-docs');
    const readyDocs = allDocs.filter(d => d.status === 'ready');
    if (!readyDocs.length) {
      list.innerHTML = '<div class="empty-state-small">Không có tài liệu nào (hãy upload trước)</div>';
    } else {
      list.innerHTML = readyDocs.map(d => `
        <label class="doc-check-item" onclick="this.classList.toggle('checked')">
          <input type="checkbox" value="${d.id}" onchange="this.closest('.doc-check-item').classList.toggle('checked', this.checked)">
          <div>
            <div class="doc-check-name">${esc(d.original_filename)}</div>
            <div class="doc-check-meta">${d.chunk_count} chunks</div>
          </div>
        </label>
      `).join('');
    }

    openModal('modal-new-session');
  }

  document.getElementById('btn-new-session')?.addEventListener('click', openNewSessionModal);
  document.getElementById('btn-new-session-center')?.addEventListener('click', openNewSessionModal);

  document.getElementById('btn-create-session')?.addEventListener('click', async () => {
    const name = document.getElementById('ns-name').value.trim() || 'Phiên mới';
    const scenarioId = document.getElementById('ns-scenario').value || null;
    const topK = parseInt(document.getElementById('ns-topk').value) || 5;
    const temp = parseFloat(document.getElementById('ns-temp').value) || 0.7;
    const docIds = [...document.querySelectorAll('#ns-docs input:checked')].map(el => el.value);

    try {
      const session = await api.post('/api/v1/sessions', {
        name, scenario_id: scenarioId, document_ids: docIds, top_k: topK, temperature: temp,
      });
      closeModal('modal-new-session');
      toast('Tạo phiên thành công');
      await openSession(session.id);
    } catch (e) {
      toast('Lỗi tạo phiên: ' + e.message, 'err');
    }
  });

  // ── Manage docs modal ──────────────────────────────────────────────────

  document.getElementById('btn-manage-docs')?.addEventListener('click', async () => {
    if (!currentSession) return;
    allDocs = await api.get('/api/v1/documents');
    const readyDocs = allDocs.filter(d => d.status === 'ready');
    const sessionDocIds = new Set(currentSession.documents.map(d => d.id));

    const list = document.getElementById('md-docs');
    list.innerHTML = readyDocs.map(d => `
      <label class="doc-check-item ${sessionDocIds.has(d.id) ? 'checked' : ''}">
        <input type="checkbox" value="${d.id}" ${sessionDocIds.has(d.id) ? 'checked' : ''}
          onchange="this.closest('.doc-check-item').classList.toggle('checked', this.checked)">
        <div>
          <div class="doc-check-name">${esc(d.original_filename)}</div>
          <div class="doc-check-meta">${d.chunk_count} chunks</div>
        </div>
      </label>
    `).join('') || '<div class="empty-state-small">Không có tài liệu</div>';

    openModal('modal-manage-docs');
  });

  document.getElementById('btn-save-docs')?.addEventListener('click', async () => {
    if (!currentSession) return;
    const checkedIds = new Set([...document.querySelectorAll('#md-docs input:checked')].map(el => el.value));
    const sessionDocIds = new Set(currentSession.documents.map(d => d.id));
    const addIds = [...checkedIds].filter(id => !sessionDocIds.has(id));
    const removeIds = [...sessionDocIds].filter(id => !checkedIds.has(id));

    try {
      await api.patch(`/api/v1/sessions/${currentSession.id}/documents`, { add_ids: addIds, remove_ids: removeIds });
      currentSession = await api.get(`/api/v1/sessions/${currentSession.id}`);
      document.getElementById('chat-session-meta').textContent =
        `${currentSession.documents.length} tài liệu · Kịch bản: ${currentSession.scenario?.name || 'mặc định'}`;
      closeModal('modal-manage-docs');
      toast('Cập nhật tài liệu thành công');
    } catch (e) {
      toast('Lỗi: ' + e.message, 'err');
    }
  });

  // ── Delete session ─────────────────────────────────────────────────────

  document.getElementById('btn-delete-session')?.addEventListener('click', async () => {
    if (!currentSession) return;
    if (!confirm(`Xóa phiên "${currentSession.name}"?`)) return;
    try {
      await api.del(`/api/v1/sessions/${currentSession.id}`);
      currentSession = null;
      document.getElementById('chat-empty').style.display = 'flex';
      document.getElementById('chat-active').style.display = 'none';
      toast('Đã xóa phiên');
      loadSessions();
    } catch (e) {
      toast('Lỗi xóa: ' + e.message, 'err');
    }
  });

  // ── Init ───────────────────────────────────────────────────────────────
  loadSessions();
  checkHealth();
  setInterval(checkHealth, 30000);
}

// ═══════════════════════════════════════════════════════════════════════════
// DOCUMENTS PAGE
// ═══════════════════════════════════════════════════════════════════════════

if (document.getElementById('doc-list')) {
  let pollingTimers = {};

  async function loadDocuments() {
    try {
      const docs = await api.get('/api/v1/documents');
      renderDocList(docs);
    } catch (e) {
      toast('Lỗi tải danh sách: ' + e.message, 'err');
    }
  }

  function renderDocList(docs) {
    const list = document.getElementById('doc-list');
    const countEl = document.getElementById('doc-count');
    countEl.textContent = `${docs.length} tài liệu`;
    if (!docs.length) {
      list.innerHTML = '<div class="empty-state"><p>Chưa có tài liệu nào. Hãy upload tài liệu đầu tiên!</p></div>';
      return;
    }
    list.innerHTML = docs.map(d => docCardHtml(d)).join('');
  }

  function badgeClass(ct) {
    if (ct.includes('pdf')) return 'badge-pdf';
    if (ct.includes('word') || ct.includes('docx')) return 'badge-docx';
    return 'badge-txt';
  }
  function badgeName(ct) {
    if (ct.includes('pdf')) return 'PDF';
    if (ct.includes('word') || ct.includes('docx')) return 'DOCX';
    return 'TXT';
  }

  function docCardHtml(d) {
    const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    const size = d.file_size > 1024*1024
      ? (d.file_size/1024/1024).toFixed(1)+'MB'
      : (d.file_size/1024).toFixed(0)+'KB';
    const statusHtml = {
      ready:      `<span class="doc-status status-ready">✓ Sẵn sàng · ${d.chunk_count} chunks</span>`,
      processing: `<span class="doc-status status-processing"><span class="status-dot-anim"></span> Đang xử lý...</span>`,
      error:      `<span class="doc-status status-error" title="${esc(d.error_message || '')}">✗ Lỗi</span>`,
    }[d.status] || '';

    return `
      <div class="doc-card" id="doc-${d.id}">
        <span class="doc-type-badge ${badgeClass(d.content_type)}">${badgeName(d.content_type)}</span>
        <div class="doc-info">
          <div class="doc-name">${esc(d.original_filename)}</div>
          <div class="doc-meta">${size} · ${new Date(d.created_at).toLocaleDateString('vi-VN')}</div>
        </div>
        ${statusHtml}
        <button class="btn-icon btn-sm" onclick="deleteDoc('${d.id}', this)" title="Xóa">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
        </button>
      </div>
    `;
  }

  window.deleteDoc = async function(docId, btn) {
    if (!confirm('Xóa tài liệu này?')) return;
    try {
      await api.del(`/api/v1/documents/${docId}`);
      document.getElementById(`doc-${docId}`)?.remove();
      toast('Đã xóa tài liệu');
      loadDocuments();
    } catch (e) {
      toast('Lỗi xóa: ' + e.message, 'err');
    }
  };

  // Poll processing documents
  function pollDocument(docId) {
    if (pollingTimers[docId]) return;
    pollingTimers[docId] = setInterval(async () => {
      try {
        const d = await api.get(`/api/v1/documents/${docId}`);
        const card = document.getElementById(`doc-${docId}`);
        if (card) card.outerHTML = docCardHtml(d);
        if (d.status !== 'processing') {
          clearInterval(pollingTimers[docId]);
          delete pollingTimers[docId];
        }
      } catch { clearInterval(pollingTimers[docId]); delete pollingTimers[docId]; }
    }, 2000);
  }

  // ── Upload ─────────────────────────────────────────────────────────────

  async function uploadFile(file) {
    const progressList = document.getElementById('upload-progress-list');
    const itemId = 'up-' + Math.random().toString(36).slice(2);
    progressList.insertAdjacentHTML('beforeend', `
      <div class="upload-progress-item" id="${itemId}">
        <div class="up-filename">${file.name}</div>
        <div class="up-bar-wrap"><div class="up-bar" style="width:30%"></div></div>
        <div class="up-status">Đang upload...</div>
      </div>
    `);

    const formData = new FormData();
    formData.append('file', file);
    try {
      const r = await fetch('/api/v1/documents/upload', { method: 'POST', body: formData });
      if (!r.ok) throw new Error(await r.text());
      const doc = await r.json();
      document.getElementById(itemId)?.remove();
      toast(`Upload thành công: ${file.name}`);
      await loadDocuments();
      pollDocument(doc.id);
    } catch (e) {
      const item = document.getElementById(itemId);
      if (item) item.querySelector('.up-status').textContent = 'Lỗi: ' + e.message;
      toast('Upload thất bại: ' + e.message, 'err');
    }
  }

  // File input
  document.getElementById('file-input')?.addEventListener('change', e => {
    [...e.target.files].forEach(uploadFile);
    e.target.value = '';
  });

  // Drag & drop
  const zone = document.getElementById('upload-zone');
  if (zone) {
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', e => {
      e.preventDefault();
      zone.classList.remove('drag-over');
      [...e.dataTransfer.files].forEach(uploadFile);
    });
  }

  // Poll any documents still processing
  loadDocuments().then(async () => {
    const docs = await api.get('/api/v1/documents');
    docs.filter(d => d.status === 'processing').forEach(d => pollDocument(d.id));
  });
  checkHealth();
}

// ═══════════════════════════════════════════════════════════════════════════
// SCENARIOS PAGE
// ═══════════════════════════════════════════════════════════════════════════

if (document.getElementById('scenario-list')) {
  let currentScenarioId = null;

  async function loadScenarios() {
    const scenarios = await api.get('/api/v1/scenarios');
    renderScenarios(scenarios);
  }

  function renderScenarios(scenarios) {
    const list = document.getElementById('scenario-list');
    if (!scenarios.length) {
      list.innerHTML = '<div class="empty-state">Chưa có kịch bản nào</div>';
      return;
    }
    list.innerHTML = scenarios.map(s => `
      <div class="scenario-card ${currentScenarioId === s.id ? 'active' : ''}"
           onclick="openScenario('${s.id}')">
        <div class="sc-name">${esc(s.name)}</div>
        ${s.description ? `<div class="sc-desc">${esc(s.description)}</div>` : ''}
        ${s.is_default ? '<div class="sc-default-badge">DEFAULT</div>' : ''}
      </div>
    `).join('');
  }

  const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

  window.openScenario = async function(id) {
    const s = await api.get(`/api/v1/scenarios/${id}`);
    currentScenarioId = id;
    document.getElementById('sc-id').value = id;
    document.getElementById('sc-name').value = s.name;
    document.getElementById('sc-desc').value = s.description || '';
    document.getElementById('sc-tone').value = s.tone;
    document.getElementById('sc-lang').value = s.language;
    document.getElementById('sc-default').checked = s.is_default;
    document.getElementById('sc-prompt').value = s.system_prompt;
    document.getElementById('scenario-editor').style.display = 'block';
    loadScenarios();
  };

  document.getElementById('btn-new-scenario')?.addEventListener('click', () => {
    currentScenarioId = null;
    document.getElementById('sc-id').value = '';
    document.getElementById('sc-name').value = '';
    document.getElementById('sc-desc').value = '';
    document.getElementById('sc-tone').value = 'professional';
    document.getElementById('sc-lang').value = 'vi';
    document.getElementById('sc-default').checked = false;
    document.getElementById('sc-prompt').value = `Bạn là trợ lý AI chuyên nghiệp, hỗ trợ tra cứu tài liệu.

{% if documents %}Tài liệu có sẵn:
{% for doc in documents %}- {{ doc }}
{% endfor %}{% endif %}

Trả lời chính xác, ngắn gọn và có trích dẫn nguồn.`;
    document.getElementById('scenario-editor').style.display = 'block';
  });

  document.getElementById('btn-cancel-scenario')?.addEventListener('click', () => {
    document.getElementById('scenario-editor').style.display = 'none';
    currentScenarioId = null;
  });

  document.getElementById('btn-save-scenario')?.addEventListener('click', async () => {
    const body = {
      name: document.getElementById('sc-name').value.trim() || 'Kịch bản mới',
      description: document.getElementById('sc-desc').value.trim() || null,
      system_prompt: document.getElementById('sc-prompt').value,
      tone: document.getElementById('sc-tone').value,
      language: document.getElementById('sc-lang').value,
      is_default: document.getElementById('sc-default').checked,
    };
    try {
      const id = document.getElementById('sc-id').value;
      if (id) {
        await api.put(`/api/v1/scenarios/${id}`, body);
        toast('Đã cập nhật kịch bản');
      } else {
        const s = await api.post('/api/v1/scenarios', body);
        currentScenarioId = s.id;
        document.getElementById('sc-id').value = s.id;
        toast('Đã tạo kịch bản mới');
      }
      loadScenarios();
    } catch (e) {
      toast('Lỗi lưu: ' + e.message, 'err');
    }
  });

  loadScenarios();
  checkHealth();
}

// ═══════════════════════════════════════════════════════════════════════════
// MODAL HELPERS
// ═══════════════════════════════════════════════════════════════════════════

function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

document.querySelectorAll('.modal-close, [data-modal]').forEach(el => {
  el.addEventListener('click', () => closeModal(el.dataset.modal));
});
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', e => {
    if (e.target === overlay) overlay.classList.remove('open');
  });
});
