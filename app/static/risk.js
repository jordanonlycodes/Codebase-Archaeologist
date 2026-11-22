"use strict";
let riskData = null;
let riskPage = 0;
const riskPageSize = 25;
const riskLabel = f => f.predicted_class === null ? 'Unavailable' : f.predicted_class === 1 ? 'Defect-related' : 'Non-defect-related';
const riskScore = f => f.model_probability === null ? '—' : `${(f.model_probability * 100).toFixed(1)}%`;

function renderDefectRisk(data) {
  riskData = data;
  riskPage = 0;
  $('risk-detail').hidden = true;
  $('risk-results').hidden = !data;
  $('risk-state').textContent = data?.message || 'C-function model results are unavailable.';
  if (!data) return;
  $('risk-search').value = '';
  $('risk-filter').value = 'all';
  $('risk-sort').value = 'score';
  for (const [id, value] of [['risk-analyzed', data.analyzed_functions], ['risk-positive', data.defect_related], ['risk-negative', data.non_defect_related], ['risk-skipped', data.skipped_functions]]) $(id).textContent = number(value);
  $('risk-coverage').textContent = `${data.eligible_files} eligible .c files · ${data.unsupported_source_files} source files outside C-only ML scope · ${data.file_issues.length} file issues. Unparsed or unprocessed functions are not counted as zero defects. Model: ${data.model_version || 'unavailable'}.`;
  const scored = data.functions.filter(f => f.status === 'analyzed');
  riskBars('risk-classes', scored.length ? [['Defect-related', data.defect_related], ['Non-defect-related', data.non_defect_related]] : []);
  const bins = [0, 0, 0, 0, 0];
  const grouped = new Map();
  for (const f of scored) {
    bins[Math.min(4, Math.floor(f.model_probability * 5))]++;
    grouped.set(f.path, (grouped.get(f.path) || 0) + (f.predicted_class === 1 ? 1 : 0));
  }
  riskBars('risk-histogram', scored.length ? bins.map((count, i) => [`${i * 20}–${(i + 1) * 20}%${i === 4 ? ' inclusive' : ' (upper excluded)'}`, count]) : []);
  riskBars('risk-files', [...grouped].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 8));
  $('risk-priority').replaceChildren();
  for (const f of [...scored].sort((a, b) => b.model_probability - a.model_probability).slice(0, 5)) {
    const item = node('li');
    const button = node('button', `${f.name || '(unnamed)'} · ${f.path}:${f.start_line} · ${riskScore(f)}`, 'text-button');
    button.type = 'button';
    button.addEventListener('click', () => showRiskDetail(f));
    item.append(button);
    $('risk-priority').append(item);
  }
  $('risk-priority').closest('.risk-review').classList.toggle('is-empty', !scored.length);
  if (!scored.length) $('risk-priority').append(node('li', 'No scored functions to prioritize.', 'risk-empty-item'));
  $('risk-issues').hidden = !data.file_issues.length;
  $('risk-issue-list').replaceChildren(...data.file_issues.map(issue => node('li', `${issue.path}: ${issue.reason.replaceAll('_', ' ')}`)));
  renderRiskTable();
}

function renderRiskTable() {
  if (!riskData) return;
  const query = $('risk-search').value.toLowerCase();
  const filter = $('risk-filter').value;
  const sort = $('risk-sort').value;
  const rows = riskData.functions.filter(f => `${f.name || ''} ${f.path}`.toLowerCase().includes(query) &&
    (filter === 'all' || (filter === 'skipped' ? f.status !== 'analyzed' : f.predicted_class !== null && String(f.predicted_class) === filter)));
  rows.sort((a, b) => (sort === 'score' ? (b.model_probability ?? -1) - (a.model_probability ?? -1) : sort === 'name' ? (a.name || '').localeCompare(b.name || '') : a.path.localeCompare(b.path)) || a.path.localeCompare(b.path) || a.start_line - b.start_line);
  riskPage = Math.min(riskPage, Math.max(0, Math.ceil(rows.length / riskPageSize) - 1));
  $('risk-rows').closest('.risk-table-panel').classList.toggle('is-empty', !rows.length);
  $('risk-rows').replaceChildren();
  if (!rows.length) {
    const empty = node('tr', undefined, 'risk-table-empty');
    const cell = node('td', riskData.functions.length ? 'No functions match these filters.' : 'No C functions were extracted for this upload.');
    cell.colSpan = 6;
    empty.append(cell);
    $('risk-rows').append(empty);
  }
  for (const f of rows.slice(riskPage * riskPageSize, (riskPage + 1) * riskPageSize)) {
    const row = node('tr');
    const name = node('td');
    const button = node('button', f.name || '(unnamed)', 'text-button');
    button.type = 'button';
    button.addEventListener('click', () => showRiskDetail(f));
    name.append(button);
    row.append(name, node('td', f.path), node('td', `${f.start_line}–${f.end_line}`), node('td', riskLabel(f)), node('td', riskScore(f)), node('td', f.status.replaceAll('_', ' ')));
    for (const [index, cell] of [...row.cells].entries()) cell.dataset.label = ['Function', 'File', 'Lines', 'Predicted class', 'Model score', 'Status'][index];
    $('risk-rows').append(row);
  }
  $('risk-page-label').textContent = rows.length ? `${riskPage * riskPageSize + 1}–${Math.min((riskPage + 1) * riskPageSize, rows.length)} of ${rows.length} functions` : 'No functions match these filters.';
  $('risk-prev').disabled = riskPage === 0;
  $('risk-next').disabled = (riskPage + 1) * riskPageSize >= rows.length;
}

function showRiskDetail(f) {
  $('risk-detail').hidden = false;
  $('risk-detail-title').textContent = f.name || 'Unnamed C function';
  $('risk-detail-location').textContent = `${f.path} · lines ${f.start_line}–${f.end_line}`;
  $('risk-detail-prediction').textContent = `${riskLabel(f)} · Estimated model probability: ${riskScore(f)} · ${f.status.replaceAll('_', ' ')}`;
  $('risk-feature-list').replaceChildren();
  for (const [name, value] of Object.entries(f.features)) {
    const row = node('div');
    row.append(node('dt', name.replaceAll('_', ' ')), node('dd', value === null ? 'Unavailable' : number(value)));
    $('risk-feature-list').append(row);
  }
  let links=$('risk-navigation');if(!links){links=node('div');links.id='risk-navigation';$('risk-detail').append(links);}links.replaceChildren();const index=riskData.functions.indexOf(f),structure=window.activeAnalysis?.structural?.functions.find(n=>n.ml_result_index===index&&n.path===f.path&&n.start_line===f.start_line&&n.end_line===f.end_line);if(structure)for(const [page,label]of [['structure','Inspect source structure'],['graph','Inspect graph relationships'],['blast-radius','Explore potential impact']]){const button=node('button',label,'text-button');button.type='button';button.disabled=page!=='structure'&&!window.activeAnalysis?.knowledge_graph?.nodes.some(n=>n.id===structure.id);button.addEventListener('click',()=>WorkspaceNavigation.open(page,structure.id));links.append(button);}
  $('risk-detail').focus({preventScroll: true});
  $('risk-detail').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth', block: 'nearest'});
}
for (const id of ['risk-search', 'risk-filter', 'risk-sort']) $(id).addEventListener(id === 'risk-search' ? 'input' : 'change', () => { riskPage = 0; renderRiskTable(); });
$('risk-prev').addEventListener('click', () => { riskPage--; renderRiskTable(); });
$('risk-next').addEventListener('click', () => { riskPage++; renderRiskTable(); });
