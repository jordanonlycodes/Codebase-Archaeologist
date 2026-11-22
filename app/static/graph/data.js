/* Shared, renderer-independent graph indexes, state, traversal and visual mappings. */
(function (root) {
  'use strict';
  const TYPES = ['repository', 'directory', 'file', 'function'];
  const RELATIONS = ['CONTAINS', 'DEFINES', 'CALLS', 'IMPORTS', 'INCLUDES'];
  const LIMITS = Object.freeze({nodes:180, edges:420, search:40, details:40, traversal:6000});
  const language = n => n.metadata?.language || '';
  const initial = () => ({mode:'2d', view:'knowledge', overlay:'entity', query:'', types:[...TYPES],
    relations:[...RELATIONS], language:'', selected:null, focus:null, hops:1, direction:'both'});
  function index(graph) {
    const nodes = new Map((graph?.nodes || []).map(n => [n.id,n]));
    const edges = (graph?.edges || []).filter(e => nodes.has(e.source) && nodes.has(e.target) && e.status === 'resolved_internal');
    const incoming = new Map(), outgoing = new Map(), references = new Map();
    for (const e of edges) {
      if (!incoming.has(e.target)) incoming.set(e.target,[]);
      if (!outgoing.has(e.source)) outgoing.set(e.source,[]);
      incoming.get(e.target).push(e); outgoing.get(e.source).push(e);
    }
    for (const ref of graph?.references || []) {
      if (!references.has(ref.source)) references.set(ref.source,[]);
      references.get(ref.source).push(ref);
    }
    const ordered = [...nodes.values()].sort((a,b) => TYPES.indexOf(a.type)-TYPES.indexOf(b.type) || (a.path || '').localeCompare(b.path || '') || a.name.localeCompare(b.name) || a.id.localeCompare(b.id));
    return {graph, nodes, ordered, edges, incoming, outgoing, references};
  }
  function allowedNode(n,s) {
    return s.types.includes(n.type) && (!s.language || language(n) === s.language) &&
      (s.view==='calls' ? n.type==='function' : s.view==='dependencies' ? n.type==='file' : true);
  }
  function allowedEdge(e,s) {
    return s.relations.includes(e.type) && (s.view==='calls' ? e.type==='CALLS' : s.view==='dependencies' ? ['IMPORTS','INCLUDES'].includes(e.type) : true);
  }
  function search(ix,query,limit=LIMITS.search) {
    const q=query.trim().toLowerCase();
    const matches=ix.ordered.filter(n=>`${n.name} ${n.path || ''}`.toLowerCase().includes(q));
    return {nodes:matches.slice(0,limit), total:matches.length};
  }
  function neighborhood(ix,seed,hops=1,direction='both',state=initial(),cap=LIMITS.nodes) {
    const found=new Set(); let visits=0, truncated=false;
    if (!ix.nodes.has(seed) || !allowedNode(ix.nodes.get(seed),state)) return {ids:found,truncated};
    found.add(seed); let frontier=[seed];
    outer: for(let depth=0; depth<Math.min(2,Math.max(1,hops)); depth++) {
      const next=[];
      for(const id of frontier) {
        const edges=[...(direction!=='in' ? ix.outgoing.get(id)||[] : []), ...(direction!=='out' ? ix.incoming.get(id)||[] : [])];
        for(const e of edges) {
          if (++visits>LIMITS.traversal) {truncated=true; break outer;}
          if (!allowedEdge(e,state)) continue;
          const target=e.source===id ? e.target : e.source;
          if (found.has(target) || !allowedNode(ix.nodes.get(target),state)) continue;
          if (found.size>=cap) {truncated=true; continue;}
          found.add(target); next.push(target);
        }
      }
      frontier=next;
    }
    return {ids:found,truncated};
  }
  function subset(ix,s) {
    let eligible=ix.ordered.filter(n=>allowedNode(n,s));
    const eligibleCount=eligible.length;
    let truncated=false;
    if (s.focus) {
      const near=neighborhood(ix,s.focus,s.hops,s.direction,s);
      eligible=eligible.filter(n=>near.ids.has(n.id)); truncated=near.truncated;
    } else if (s.query.trim()) {
      const q=s.query.trim().toLowerCase();
      eligible=eligible.filter(n=>`${n.name} ${n.path || ''}`.toLowerCase().includes(q));
    }
    // Selected search hits are retained even beyond the deterministic initial slice.
    const selected=eligible.find(n=>n.id===s.selected);
    const shown=eligible.slice(0,LIMITS.nodes);
    if (selected && !shown.includes(selected)) shown[shown.length-1]=selected;
    const ids=new Set(shown.map(n=>n.id));
    const allEdges=ix.edges.filter(e=>ids.has(e.source)&&ids.has(e.target)&&allowedEdge(e,s));
    return {nodes:shown, edges:allEdges.slice(0,LIMITS.edges), eligible:eligibleCount, matching:eligible.length,
      truncated:truncated || eligible.length>shown.length || allEdges.length>LIMITS.edges, matchingEdges:allEdges.length};
  }
  function overlay(n,mode='entity') {
    const m=n.metadata || {};
    let color={repository:'#F8E8EA',directory:'#a96f81',file:'#b9acb1',function:'#E54859'}[n.type] || '#827d84';
    let label=n.type;
    if (mode==='complexity') {
      const band=m.complexity_band;
      color=({low:'#88b9a9',moderate:'#d7b17d',high:'#E54859',very_high:'#b83c72'})[band] || '#67636e';
      label=band ? `${band.replace('_',' ')} complexity` : 'Complexity unavailable';
    } else if (mode==='ml') {
      const valid=n.type==='function' && m.language==='C' && m.ml?.status==='analyzed' && [0,1].includes(m.ml.predicted_class);
      color=valid ? m.ml.predicted_class===1 ? '#E54859' : '#88b9a9' : '#67636e';
      label=valid ? m.ml.predicted_class===1 ? 'Predicted defect-related' : 'Predicted non-defect-related' : 'Unscored';
    }
    return {color,label,hotspot:Array.isArray(m.hotspots)&&m.hotspots.length>0,
      size:({repository:14,directory:10,file:8,function:6})[n.type] || 6,
      shape:({repository:'diamond',directory:'square',file:'rectangle',function:'circle'})[n.type] || 'circle'};
  }
  function emphasis(ix,id,selected,direction='both',relations=RELATIONS) {
    if (!selected) return 'normal';
    if (id===selected) return 'selected';
    if (direction!=='in' && (ix.outgoing.get(selected)||[]).some(e=>e.target===id&&relations.includes(e.type))) return 'outgoing';
    if (direction!=='out' && (ix.incoming.get(selected)||[]).some(e=>e.source===id&&relations.includes(e.type))) return 'incoming';
    return 'dim';
  }
  function forceData(view) {
    // 3d-force-graph mutates its inputs. Never pass canonical backend objects.
    return {nodes:view.nodes.map(n=>({id:n.id, record:n})), links:view.edges.map(e=>({...e}))};
  }
  const api={TYPES,RELATIONS,LIMITS,language,initial,index,search,neighborhood,subset,overlay,emphasis,forceData};
  if(typeof module!=='undefined' && module.exports) module.exports=api;
  root.ArchaeologistGraph=api;
})(globalThis);
