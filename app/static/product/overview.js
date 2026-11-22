(function(root){
"use strict";
let result=null;let heatIds=new Map();let page=0;const pageSize=50;
function renderOverview(data){result=data;heatIds=new Map((data.architecture?.heatmap||[]).filter(n=>n.type==='file').map(n=>[n.path,n.id]));
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
  $("stat-languages-note").textContent = `Most files: ${(result.languages[0]?.language || 'unavailable')}`;
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
  const motion=root.WorkspaceMotion;
  motion?.watch(document.querySelectorAll('.stat-card'),{key:'overview-cards'});
  for(const [id,value]of Object.entries({'stat-files':s.files,'stat-lines':s.source_lines,'stat-languages':s.languages,'stat-directories':s.directories}))motion?.count($(id),value,{key:'count:'+id,format:number});
  motion?.reveal($('result-badge'),{key:'analysis-ready',kind:'fade'});
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
    const path = node("td");
    const identity=heatIds.get(file.path);
    if(identity){const link=node('button',file.path,'text-button');link.type='button';link.addEventListener('click',()=>WorkspaceNavigation.open('heatmaps',identity));path.append(link);}else path.textContent=file.path;
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

for(const id of ['file-search','language-filter','file-sort'])$(id).addEventListener(id==='file-search'?'input':'change',()=>{page=0;renderInventory();});
$('previous-page').addEventListener('click',()=>{page--;renderInventory();});$('next-page').addEventListener('click',()=>{page++;renderInventory();});

root.renderOverview=renderOverview;
})(globalThis);
