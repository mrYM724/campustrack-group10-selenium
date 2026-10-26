'use strict';
(() => {
  let currentPage = 1;
  let currentQuery = '';
  let totalPages = 1;
  let records = [];
  let editId = null;
  const admin = document.body.dataset.role === 'admin';
  const $ = id => document.getElementById(id);
  const toast = (message, error = false) => {
    const node = $('toast');
    node.textContent = message;
    node.className = 'toast' + (error ? ' is-error' : '');
    node.hidden = false;
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => { node.hidden = true; }, 5000);
  };
  const text = (tag, content, cls = '') => {
    const node = document.createElement(tag);
    node.textContent = content;
    if (cls) node.className = cls;
    return node;
  };
  const request = async (url, options = {}) => {
    const response = await fetch(url, {credentials: 'same-origin', ...options});
    let data = {};
    try { data = await response.json(); } catch (_) { /* non-JSON response */ }
    if (!response.ok) {
      let reason = typeof data.detail === 'string' ? data.detail : 'Request failed';
      if (Array.isArray(data.detail)) reason = data.detail.map(x => x.msg).join('; ');
      throw new Error(reason);
    }
    return data;
  };
  const showStats = async () => {
    const s = await request('/api/stats');
    ['total', 'present', 'absent', 'late'].forEach(key => { $('stat-' + key).textContent = s[key]; });
  };
  const renderRows = () => {
    const tbody = $('record-rows');
    tbody.replaceChildren();
    if (!records.length) {
      const tr = document.createElement('tr');
      const cell = text('td', 'No matching attendance records found.', 'empty-state');
      cell.colSpan = admin ? 6 : 5;
      tr.appendChild(cell); tbody.appendChild(tr);
      return;
    }
    records.forEach(record => {
      const tr = document.createElement('tr');
      tr.dataset.code = record.student_code;
      tr.dataset.recordId = record.id;
      tr.append(text('td', record.student_code, 'student-code'));
      const name = text('td', record.student_name, 'student-name');
      tr.append(name, text('td', record.course), text('td', record.attendance_date));
      const statusCell = document.createElement('td');
      statusCell.append(text('span', record.status, 'status-pill ' + record.status.toLowerCase()));
      tr.append(statusCell);
      if (admin) {
        const cell = document.createElement('td');
        const edit = text('button', 'Edit', 'table-action');
        edit.type = 'button'; edit.dataset.action = 'edit'; edit.dataset.recordId = record.id;
        const del = text('button', 'Delete', 'table-action danger-action');
        del.type = 'button'; del.dataset.action = 'delete'; del.dataset.recordId = record.id;
        cell.append(edit, del); tr.append(cell);
      }
      tbody.appendChild(tr);
    });
  };
  const loadRecords = async () => {
    const data = await request(`/api/records?page=${currentPage}&per_page=10&q=${encodeURIComponent(currentQuery)}`);
    totalPages = data.total_pages;
    records = data.items;
    $('total-summary').textContent = `${data.total} matching records`;
    $('page-info').textContent = `Page ${currentPage} of ${totalPages}`;
    $('prev-page').disabled = currentPage <= 1;
    $('next-page').disabled = currentPage >= totalPages;
    renderRows();
    $('download-btn').href = '/api/export?q=' + encodeURIComponent(currentQuery);
  };
  const refresh = async () => {
    try { await Promise.all([showStats(), loadRecords()]); }
    catch (err) { toast(err.message, true); }
  };
  const applySearch = async () => { currentQuery = $('search-input').value.trim(); currentPage = 1; await loadRecords(); };
  $('search-button').addEventListener('click', applySearch);
  $('search-input').addEventListener('keydown', e => { if (e.key === 'Enter') applySearch(); });
  $('clear-search').addEventListener('click', async () => { $('search-input').value = ''; await applySearch(); });
  $('prev-page').addEventListener('click', async () => { if (currentPage > 1) { currentPage--; await loadRecords(); } });
  $('next-page').addEventListener('click', async () => { if (currentPage < totalPages) { currentPage++; await loadRecords(); } });
  if (admin) {
    const modal = $('record-modal');
    const fields = {student_code: $('field-code'),student_name: $('field-name'),course: $('field-course'),attendance_date: $('field-date'),status: $('field-status'),notes: $('field-notes')};
    const openModal = (record = null) => {
      editId = record?.id ?? null;
      $('modal-title').textContent = record ? 'Edit attendance record' : 'Add attendance record';
      for (const [key, field] of Object.entries(fields)) field.value = record ? record[key] : (key === 'attendance_date' ? '2026-10-26' : key === 'status' ? 'Present' : '');
      modal.showModal(); fields.student_code.focus();
    };
    $('add-record-btn').addEventListener('click', () => openModal());
    $('close-modal').addEventListener('click', () => modal.close());
    $('cancel-modal').addEventListener('click', () => modal.close());
    $('record-form').addEventListener('submit', async e => {
      e.preventDefault();
      const body = Object.fromEntries(Object.entries(fields).map(([key, field]) => [key, field.value]));
      try {
        await request(editId ? `/api/records/${editId}` : '/api/records', {method: editId ? 'PUT' : 'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
        modal.close();
        currentQuery = body.student_code; $('search-input').value = body.student_code; currentPage = 1;
        await refresh(); toast(editId ? 'Record updated successfully' : 'Record added successfully');
      } catch (err) { toast(err.message, true); }
    });
    $('record-rows').addEventListener('click', async e => {
      const action = e.target.closest('button[data-action]');
      if (!action) return;
      const id = Number(action.dataset.recordId);
      const record = records.find(x => x.id === id);
      if (!record) return;
      if (action.dataset.action === 'edit') { openModal(record); return; }
      if (!confirm(`Delete ${record.student_name}? This cannot be undone.`)) return;
      try { await request(`/api/records/${id}`, {method:'DELETE'}); currentPage = 1; await refresh(); toast('Record deleted successfully'); }
      catch (err) { toast(err.message, true); }
    });
    $('upload-btn').addEventListener('click', async () => {
      const file = $('csv-file').files[0];
      if (!file) { toast('Select a CSV file first', true); return; }
      const data = new FormData(); data.append('file', file);
      try { const result = await request('/api/import', {method:'POST',body:data}); $('csv-file').value = ''; currentQuery = ''; $('search-input').value = ''; currentPage = 1; await refresh(); toast(result.message); }
      catch (err) { toast(err.message, true); }
    });
  }
  refresh();
})();
