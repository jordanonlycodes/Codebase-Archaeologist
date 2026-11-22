"use strict";

const $ = (id) => document.getElementById(id);
const number = (value) => new Intl.NumberFormat().format(value);
const bytes = (value) => value < 1024 ? `${number(value)} B` : value < 1048576 ? `${(value / 1024).toFixed(1)} KiB` : `${(value / 1048576).toFixed(1)} MiB`;
let result = null;
let activeRequest = null;
let page = 0;
const pageSize = 50;

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function showError(message) {
  $("error-box").textContent = message + (result ? " Your previous analysis is still displayed below." : "");
  $("error-box").hidden = false;
}

function setInputBusy(busy) {
  for (const id of ['choose-file', 'analyze-github', 'github-url', 'mode-zip', 'mode-github']) $(id).disabled = busy;
  $('github-form').setAttribute('aria-busy', String(busy));
  $('knowledge-explorer').setAttribute('aria-busy', String(busy));
  $('architecture-intelligence').setAttribute('aria-busy', String(busy));
  $('blast-radius').setAttribute('aria-busy', String(busy));
  if(busy) $('ai-state').textContent='Repository analysis in progress. The last completed atlas remains available.';
  else if(result) $('ai-state').textContent=result.architecture?'Exploring evidence from the last completed analysis.':'Architecture intelligence is unavailable for this analysis.';
  if (busy) $('graph-state').textContent = 'Repository analysis in progress. Previous graph, if any, remains available.';
  else if (result) $('graph-state').textContent = result.knowledge_graph ? 'Exploring the last completed repository analysis.' : 'Knowledge graph unavailable for this analysis.';
}

function upload(file) {
  if (activeRequest || !file) return;
  $("error-box").hidden = true;
  if (!file.name.toLowerCase().endsWith(".zip")) return showError("Choose a ZIP archive. Other file types are not supported.");
  if (file.size > Number($("file-input").dataset.maxBytes)) return showError("This ZIP exceeds 25 MiB. Remove dependencies, builds and large assets, then try again.");
  if (!file.size) return showError("This file is empty. Choose a complete ZIP archive.");
  const request = new XMLHttpRequest();
  activeRequest = request;
  setInputBusy(true);
  $("drop-zone").classList.add("busy");
  $("upload-status").hidden = false;
  $("cancel-upload").hidden = false;
  $("upload-progress").value = 0;
  $("status-text").textContent = `Uploading ${file.name}…`;
  request.open("POST", "/api/analyze");
  request.responseType = "json";
  request.timeout = 180000;
  request.upload.onprogress = (event) => {
    if (event.lengthComputable) {
      const progress = Math.round(event.loaded / event.total * 100);
      $("upload-progress").value = progress;
      $("status-text").textContent = `Uploading ${file.name} · ${progress}%`;
    }
  };
  request.upload.onload = () => {
    $("defect-risk").setAttribute("aria-busy", "true");
    $("status-text").textContent = `Analyzing ${file.name} · validating, scanning and analyzing eligible C functions…`;
    $("upload-progress").removeAttribute("value");
    $("cancel-upload").hidden = true;
  };
  request.onload = () => {
    if (request.status >= 200 && request.status < 300 && request.response?.summary) {
      result = request.response;
      renderResult();
      $("status-text").textContent = `Analysis complete · ${number(result.summary.files)} files scanned. Temporary files deleted.`;
      $("upload-progress").value = 100;
    } else {
      showError(request.response?.error?.message || `Analysis failed (HTTP ${request.status}). Please try another ZIP.`);
      $("upload-status").hidden = true;
    }
  };
  request.onerror = () => { showError("Could not reach the server. Check that the application is running, then retry."); $("upload-status").hidden = true; };
  request.ontimeout = () => { showError("Analysis timed out. Try a smaller archive. The server will clean up its temporary files when processing finishes."); $("upload-status").hidden = true; };
  request.onabort = () => { $("upload-status").hidden = true; showError("Upload canceled. You can choose another ZIP."); };
  request.onloadend = () => {
    $("defect-risk").setAttribute("aria-busy", "false");
    activeRequest = null;
    setInputBusy(false);
    $("drop-zone").classList.remove("busy");
    $("cancel-upload").hidden = true;
    $("file-input").value = "";
  };
  const form = new FormData();
  form.append("file", file);
  request.send(form);
}

function renderResult() {
  renderImpact(result.knowledge_graph, result.architecture, result.structural);
  renderKnowledgeGraph(result.knowledge_graph);
  renderArchitecture(result.architecture, result.knowledge_graph, result.structural);
  renderStructure(result.structural);
  renderDefectRisk(result.defect_risk);
  const source = result.source;
  $('source-meta').replaceChildren();
  $('source-meta').hidden = source?.type !== 'github';
  if (source?.type === 'github') {
    const link = node('a', `${source.owner}/${source.name}`);
    // Display only canonical GitHub links returned by our source contract.
    if (/^https:\/\/github\.com\/[A-Za-z0-9-]+\/[A-Za-z0-9_.-]+$/.test(source.url || '')) {
      link.href = source.url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
    }
    $('source-meta').append(link, node('span', ` · Default branch: ${source.default_branch || 'unavailable'} · Snapshot: ${source.snapshot_commit || 'unavailable'}`));
  }
  const s = result.summary;
  $("result-title").textContent = result.repository;
  $("result-badge").textContent = "Analysis complete";
  $("result-badge").classList.add("complete");
  $("result-meta").textContent = `Analyzed ${new Date(result.analyzed_at).toLocaleString()} · ${number(result.archive_entries)} archive entries · ${bytes(s.bytes)} included text`;
  for (const [id, value] of Object.entries({"stat-files": s.files, "stat-lines": s.source_lines, "stat-languages": s.languages, "stat-directories": s.directories, "metric-total": s.total_lines, "metric-blank": s.blank_lines, "metric-comments": s.known_comment_lines, "metric-skipped": s.skipped_files})) $(id).textContent = number(value);
  $("stat-files-note").textContent = `${number(s.source_files)} source files · ${number(s.skipped_files)} skipped`;
  $("stat-lines-note").textContent = `Across ${number(s.source_files)} recognized source files`;
  $("stat-languages-note").textContent = `Most files: ${result.languages[0].language}`;
  $("stat-directories-note").textContent = "Excludes the extraction root";
  $("metric-size").textContent = bytes(s.bytes);
  $("comment-coverage").textContent = `Comment coverage: ${number(s.comment_counted_files)} of ${number(s.files)} files. ${number(s.comment_uncounted_files)} files have unavailable comment counts; this is a partial total.`;
  $("language-empty").hidden = true;
  $("language-content").hidden = false;
  $("language-content").replaceChildren();
  $("language-filter").replaceChildren(new Option("All languages", ""));
  for (const language of result.languages) {
    const row = node("div", undefined, "language-row");
    const label = node("div", undefined, "language-label");
    label.append(node("span", language.language), node("span", `${number(language.files)} files · ${language.percentage}%`));
    const bar = node("progress", undefined, "language-bar");
    bar.max = s.files;
    bar.value = language.files;
    bar.setAttribute("aria-label", `${language.language}: ${language.percentage}% of files`);
    row.append(label, bar);
    $("language-content").append(row);
    $("language-filter").append(new Option(language.language, language.language));
  }
  $("file-search").value = "";
  $("file-sort").value = "path";
  page = 0;
  $("inventory-empty").hidden = true;
  $("inventory-toolbar").hidden = false;
  $("download-json").hidden = false;
  $("largest-panel").hidden = false;
  $("largest-files").replaceChildren();
  for (const file of result.largest_files) {
    const item = node("li");
    item.append(node("span", file.path), node("span", bytes(file.bytes)));
    $("largest-files").append(item);
  }
  $("skip-details").textContent = Object.entries(result.skipped).length ? `Skipped files: ${Object.entries(result.skipped).map(([reason, count]) => `${reason.replaceAll("_", " ")}: ${number(count)}`).join("; ")}.` : "No files were skipped in this archive.";
  renderInventory();
}

function renderInventory() {
  if (!result) return;
  const query = $("file-search").value.toLowerCase();
  const language = $("language-filter").value;
  const sort = $("file-sort").value;
  const files = result.files.filter((file) => file.path.toLowerCase().includes(query) && (!language || file.language === language));
  files.sort((a, b) => (sort === "path" ? 0 : b[sort] - a[sort]) || a.path.localeCompare(b.path));
  page = Math.min(page, Math.max(0, Math.ceil(files.length / pageSize) - 1));
  const start = page * pageSize;
  $("file-table-body").replaceChildren();
  const fragment = document.createDocumentFragment();
  for (const file of files.slice(start, start + pageSize)) {
    const row = node("tr");
    const path = node("td", file.path);
    path.title = file.path;
    row.append(path, node("td", file.language), node("td", number(file.lines), "number"), node("td", number(file.blank_lines), "number"));
    const comment = node("td", file.comment_lines === null ? "—" : number(file.comment_lines), "number");
    if (file.comment_lines === null) { comment.classList.add("unavailable"); comment.title = "Comment count unavailable for this file"; comment.setAttribute("aria-label", "Comment count unavailable"); }
    row.append(comment, node("td", bytes(file.bytes), "number"));
    fragment.append(row);
  }
  $("file-table-body").append(fragment);
  $("inventory-count").textContent = `${number(files.length)} of ${number(result.files.length)} included files · — means unavailable`;
  $("file-table-wrap").hidden = files.length === 0;
  $("no-matches").hidden = files.length !== 0;
  $("pagination").hidden = files.length === 0;
  $("page-label").textContent = `${number(start + 1)}–${number(Math.min(start + pageSize, files.length))} of ${number(files.length)} files`;
  $("previous-page").disabled = page === 0;
  $("next-page").disabled = start + pageSize >= files.length;
}

$("choose-file").addEventListener("click", () => $("file-input").click());
$("file-input").addEventListener("change", (event) => upload(event.target.files[0]));
$("cancel-upload").addEventListener("click", () => activeRequest?.abort());
for (const name of ["dragenter", "dragover"]) $("drop-zone").addEventListener(name, (event) => { event.preventDefault(); if (!activeRequest) $("drop-zone").classList.add("dragging"); });
for (const name of ["dragleave", "drop"]) $("drop-zone").addEventListener(name, (event) => { event.preventDefault(); $("drop-zone").classList.remove("dragging"); });
$("drop-zone").addEventListener("drop", (event) => { if (activeRequest) return; if (event.dataTransfer.files.length !== 1) return showError("Drop one ZIP archive at a time."); upload(event.dataTransfer.files[0]); });
window.addEventListener("dragover", (event) => event.preventDefault());
window.addEventListener("drop", (event) => event.preventDefault());
$("file-search").addEventListener("input", () => { page = 0; renderInventory(); });
for (const id of ["language-filter", "file-sort"]) $(id).addEventListener("change", () => { page = 0; renderInventory(); });
$("previous-page").addEventListener("click", () => { page--; renderInventory(); });
$("next-page").addEventListener("click", () => { page++; renderInventory(); });
$("download-json").addEventListener("click", () => {
  if (!result) return;
  if (window.impactExplorer?.result) result.blast_radius = window.impactExplorer.result;
  else delete result.blast_radius;
  const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], {type: "application/json"}));
  const link = node("a");
  link.href = url;
  link.download = "codebase-analysis.json";
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
for (const link of document.querySelectorAll('.nav-link[href^="#"]')) link.addEventListener("click", () => {
  document.querySelectorAll(".nav-link").forEach((item) => item.classList.remove("active"));
  link.classList.add("active");
});


for (const mode of ['zip', 'github']) $(`mode-${mode}`).addEventListener('click', () => {
  if (activeRequest) return;
  $('drop-zone').hidden = mode !== 'zip';
  $('github-form').hidden = mode !== 'github';
  $('mode-zip').setAttribute('aria-pressed', String(mode === 'zip'));
  $('mode-github').setAttribute('aria-pressed', String(mode === 'github'));
});

$('github-form').addEventListener('submit', event => {
  event.preventDefault();
  if (activeRequest) return;
  const url = $('github-url').value.trim();
  $('error-box').hidden = true;
  if (!/^https:\/\/github\.com\/[A-Za-z0-9-]+\/[A-Za-z0-9_.-]+\/?$/i.test(url)) return showError('Use https://github.com/owner/repository without extra paths or query parameters.');
  const request = new XMLHttpRequest();
  activeRequest = request;
  setInputBusy(true);
  $('upload-status').hidden = false;
  $('cancel-upload').hidden = true;
  $('upload-progress').removeAttribute('value');
  $('defect-risk').setAttribute('aria-busy', 'true');
  $('status-text').textContent = 'Importing from GitHub · downloading a default-branch snapshot, validating and analyzing…';
  request.open('POST', '/api/analyze/github');
  request.setRequestHeader('Content-Type', 'application/json');
  request.responseType = 'json';
  request.timeout = 180000;
  request.onload = () => {
    if (request.status >= 200 && request.status < 300 && request.response?.summary) {
      result = request.response;
      renderResult();
      $('status-text').textContent = `Analysis complete · ${number(result.summary.files)} files scanned. Temporary files deleted.`;
      $('upload-progress').value = 100;
    } else {
      showError(request.response?.error?.message || `GitHub import failed (HTTP ${request.status}). Please retry.`);
      $('upload-status').hidden = true;
    }
  };
  request.onerror = () => { showError('Could not reach the server. Check the connection and retry.'); $('upload-status').hidden = true; };
  request.ontimeout = () => { showError('GitHub import timed out. Try a smaller repository or retry later.'); $('upload-status').hidden = true; };
  request.onloadend = () => {
    activeRequest = null;
    setInputBusy(false);
    $('defect-risk').setAttribute('aria-busy', 'false');
  };
  request.send(JSON.stringify({url}));
});
