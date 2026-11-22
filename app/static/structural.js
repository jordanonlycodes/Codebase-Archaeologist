"use strict";
let structureData = null;
let structurePage = 0;
const structurePageSize = 25;
const measured = value => value === null || value === undefined ? 'Unavailable' : number(value);

function renderStructure(data) {
  structureData = data;
  structurePage = 0;
  $('structural-results').hidden = !data;
  $('structural-state').textContent = !data ? 'Structural analysis is unavailable.' :
    ({complete:'Supported source analysis complete.',partial:'Partial analysis: review coverage and resource limits.',no_supported_files:'No supported C or Python source files.',no_functions:'Supported files parsed; no function definitions discovered.'}[data.status]);
  if (!data) return;
  const summary = data.summary;
  const coverage = data.coverage;
  $('structure-count').textContent = measured(summary.analyzed_functions);
  $('structure-average').textContent = summary.average_complexity === null ? 'Unavailable' : summary.average_complexity.toFixed(2);
  $('structure-hotspots').textContent = summary.analyzed_functions ? number(data.hotspots.length) : 'Unavailable';
  $('structure-nesting').textContent = measured(summary.maximum_nesting);
  $('structural-coverage').textContent = `${coverage.analyzed_files} fully analyzed supported files; ${coverage.partial_files} partial; ${coverage.unsupported_files} unsupported source files; ${coverage.skipped_files} skipped/unavailable; ${coverage.invalid_functions} unmeasured definitions. ${coverage.truncated ? 'Resource limits reached; undiscovered functions are unknown.' : 'Counts cover included files after existing exclusions.'} ML remains C-only.`;
  riskBars('structure-bands', summary.analyzed_functions ? Object.entries(summary.complexity_bands).map(([label,count]) => [label.replaceAll('_',' '),count]) : []);
  const c = data.composition;
  const known = c.comment_lines !== null && c.code_lines !== null;
  $('structure-composition-note').textContent = `${coverage.composition_files}/${coverage.included_files} files · ${coverage.composition_physical_lines} covered physical lines · Comment density: ${c.comment_density === null ? 'unavailable' : (c.comment_density*100).toFixed(1)+'% of covered nonblank lines'}`;
  riskBars('structure-composition', known ? [['Code (including mixed lines)',c.code_lines],['Comment-only',c.comment_lines],['Blank',coverage.composition_physical_lines-c.comment_lines-c.code_lines]] : []);
  const ranked = data.files.filter(f=>f.summary.analyzed_functions).sort((a,b)=>b.summary.total_complexity-a.summary.total_complexity || a.path.localeCompare(b.path));
  riskBars('structure-files', ranked.slice(0,8).map(f=>[f.path,f.summary.total_complexity]));
  $('structure-priority').replaceChildren();
  for (const hotspot of data.hotspots.slice(0,8)) {
    const item = node('li');
    item.append(node('strong',`${hotspot.name || '(unnamed)'} · ${hotspot.path}:${hotspot.start_line}`),node('p',hotspot.reasons.map(r=>r.explanation).join(' '),'muted'));
    $('structure-priority').append(item);
  }
  $('structure-priority').closest('.risk-review').classList.toggle('is-empty',!data.hotspots.length);
  if (!data.hotspots.length) $('structure-priority').append(node('li',summary.analyzed_functions ? 'No measured function meets the configured thresholds.' : 'No valid function metrics available for review.','risk-empty-item'));
  const issues = data.files.filter(f=>f.reasons.length || f.status==='unsupported');
  $('structure-issues').hidden = !issues.length;
  $('structure-issue-list').replaceChildren(...issues.slice(0,24).map(f=>node('li',`${f.path}: ${f.reasons.join('; ') || 'Unsupported structural language'}`)));
  if (issues.length>24) $('structure-issue-list').append(node('li',`${issues.length-24} more file issues are included in JSON export.`));
  $('structure-definitions').replaceChildren();
  for (const [name,definition] of Object.entries(data.definitions)) $('structure-definitions').append(node('dt',name),node('dd',definition));
  $('structure-definitions').append(node('dt','Configured thresholds'),node('dd',Object.entries(data.thresholds).map(([k,v])=>`${k.replaceAll('_',' ')}: ${v}`).join(' · ')));
  $('structure-search').value=''; $('structure-language').value=''; $('structure-sort').value='cyclomatic_complexity';
  renderStructureTable();
}

function renderStructureTable() {
  if (!structureData) return;
  const query=$('structure-search').value.toLowerCase();
  const language=$('structure-language').value;
  const sort=$('structure-sort').value;
  const rows=structureData.functions.filter(f=>(!language || f.language===language) && `${f.qualified_name || f.name || ''} ${f.path}`.toLowerCase().includes(query));
  rows.sort((a,b)=>(sort==='path' ? a.path.localeCompare(b.path) : (b[sort] ?? -1)-(a[sort] ?? -1)) || a.path.localeCompare(b.path) || a.start_line-b.start_line || a.start_column-b.start_column);
  const hot = new Map(structureData.hotspots.map(h=>[h.function_id,h.reasons.map(r=>r.metric.replaceAll('_',' ')).join(', ')]));
  structurePage=Math.min(structurePage,Math.max(0,Math.ceil(rows.length/structurePageSize)-1));
  $('structure-rows').replaceChildren();
  $('structure-rows').closest('.risk-table-panel').classList.toggle('is-empty',!rows.length);
  if (!rows.length) {
    const row=node('tr',undefined,'risk-table-empty');const cell=node('td',structureData.functions.length ? 'No functions match these filters.' : 'No function definitions available. Review coverage above.');cell.colSpan=8;row.append(cell);$('structure-rows').append(row);
  }
  for (const f of rows.slice(structurePage*structurePageSize,(structurePage+1)*structurePageSize)) {
    const row=node('tr');
    const values=[`${f.qualified_name || f.name || '(unnamed)'} · ${f.language}`,`${f.path}:${f.start_line}–${f.end_line}`,measured(f.cyclomatic_complexity),measured(f.max_nesting_depth),number(f.span_lines),measured(f.parameter_count),hot.get(f.id) || f.status,f.language==='C' ? f.ml_status : 'Unavailable (C-only)'];
    const labels=['Function / language','File / lines','Complexity','Nesting','Span','Parameters','Review / status','ML status'];
    values.forEach((value,i)=>{const cell=node('td',i===0?undefined:value);if(i===0){const inspect=node('button',value,'text-button');inspect.type='button';inspect.addEventListener('click',()=>showStructureDetail(f));cell.append(inspect);}cell.dataset.label=labels[i];row.append(cell);});
    $('structure-rows').append(row);
  }
  $('structure-page-label').textContent=rows.length ? `${structurePage*structurePageSize+1}–${Math.min((structurePage+1)*structurePageSize,rows.length)} of ${rows.length} functions` : 'No function rows';
  $('structure-prev').disabled=structurePage===0;
  $('structure-next').disabled=(structurePage+1)*structurePageSize>=rows.length;
}
for (const id of ['structure-search','structure-language','structure-sort']) $(id).addEventListener(id==='structure-search' ? 'input' : 'change',()=>{structurePage=0;renderStructureTable();});
$('structure-prev').addEventListener('click',()=>{structurePage--;renderStructureTable();});
$('structure-next').addEventListener('click',()=>{structurePage++;renderStructureTable();});

function showStructureDetail(f){
 let panel=$('structure-detail');if(!panel){panel=node('article',undefined,'panel structure-function-detail');panel.id='structure-detail';panel.tabIndex=-1;$('structural-results').append(panel);}panel.replaceChildren(node('h3',f.qualified_name||f.name||'(unnamed)'),node('p',`${f.path}:${f.start_line}–${f.end_line}`,'evidence-path'));
 const dl=node('dl');for(const [label,value]of Object.entries({'Language':f.language,'Parse status':f.status,'Cyclomatic complexity':f.cyclomatic_complexity,'Maximum nesting':f.max_nesting_depth,'Function span':f.span_lines,'Parameters':f.parameter_count,'Decision points':f.decision_points,'Loops':f.loop_count,'Conditionals':f.conditional_count}))dl.append(node('dt',label),node('dd',value==null?'Unavailable':String(value)));panel.append(dl);
 const hotspot=structureData.hotspots.find(h=>h.function_id===f.id);for(const reason of hotspot?.reasons||[])panel.append(node('p',reason.explanation));
 if(window.WorkspaceNavigation?.askJordan){const ask=node('button','Ask Jordan about this function','text-button');ask.type='button';ask.addEventListener('click',()=>WorkspaceNavigation.askJordan(f.id));panel.append(ask);}
 if(window.activeAnalysis?.knowledge_graph?.nodes.some(n=>n.id===f.id))for(const [page,label]of [['graph','Inspect graph relationships'],['blast-radius','Explore potential change impact']]){const link=node('button',label,'text-button');link.type='button';link.addEventListener('click',()=>WorkspaceNavigation.open(page,f.id));panel.append(link);}
 panel.focus({preventScroll:true});panel.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'nearest'});
}
