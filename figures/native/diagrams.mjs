/** Editable native-object definitions for Figures 2 and 4. */
const W = 1600;
const H = 1500;
const C = {
  ink: '#17324D', muted: '#536575', teal: '#087F8C', blue: '#2F6B9A',
  orange: '#C57A32', lightTeal: '#EDF7F7', lightBlue: '#EEF4F9',
  lightOrange: '#FBF3E9', grid: '#DCE4EA', gray: '#B7C2CB', white: '#FFFFFF'
};

function makePlan(number, language, fonts = {}) {
  const lang = /^en/i.test(language || '') ? 'en' : 'zh';
  const fontFamily = fonts[lang] || (lang === 'en' ? 'Arial' : 'Microsoft YaHei');
  const ops = [];
  const labels = [];
  const semanticEdges = [];
  const choose = (cn, en) => lang === 'en' ? en : cn;
  const min = lang === 'en' ? 30 : 34;
  const text = (name, value, x, y, w, h, opts = {}) => {
    const settings = {fontSize: 34, bold: false, color: C.ink,
      align: 'center', verticalAlign: 'middle', fontFamily,
      insets: {top: 0, bottom: 0, left: 0, right: 0}, wrap: true, ...opts};
    if (settings.fontSize < min) throw new Error(`${name}: text below minimum size`);
    ops.push({kind: 'text', name, value, x, y, w, h, opts: settings});
    labels.push({name, text: value, fontSize: settings.fontSize, x, y, w, h});
  };
  const box = (name, x, y, w, h, opts = {}) => ops.push({kind: 'box', name, x, y, w, h,
    opts: {fill: C.white, stroke: C.grid, strokeWidth: 2, radius: 0, ...opts}});
  const line = (name, x1, y1, x2, y2, opts = {}) => ops.push({kind: 'line', name, x1, y1, x2, y2,
    opts: {color: C.ink, width: 2.5, ...opts}});
  const arrow = (name, x1, y1, x2, y2, opts = {}) => ops.push({kind: 'arrow', name, x1, y1, x2, y2,
    opts: {color: C.ink, width: 2.5, ...opts}});
  const path = (name, points, opts = {}) => {
    points.slice(1).forEach((p, i) => {
      const a = points[i];
      (i === points.length - 2 ? arrow : line)(`${name}-${i}`, a[0], a[1], p[0], p[1], opts);
    });
  };
  const panel = (letter, cn, en, x, y, width) => {
    text(`panel-${letter}-letter`, letter, x, y, 48, 56, {fontSize: 42, bold: true, align: 'left'});
    box(`panel-${letter}-accent`, x + 58, y + 6, 5, 42, {fill: C.teal, stroke: C.teal, strokeWidth: 0});
    text(`panel-${letter}-title`, choose(cn, en), x + 82, y, width - 82, 56,
      {fontSize: 42, bold: true, align: 'left'});
  };
  const node = (name, cn, en, bodyCn, bodyEn, x, y, width, height, color = C.teal, extra = {}) => {
    const railHeight = extra.railHeight || 46;
    box(`${name}-frame`, x, y, width, height, {stroke: color, fill: C.white});
    box(`${name}-rail`, x, y, width, railHeight, {fill: color, stroke: color, strokeWidth: 0});
    text(`${name}-heading`, choose(cn, en), x + 14, y + 2, width - 28, railHeight - 4,
      {fontSize: 36, bold: true, color: C.white});
    text(`${name}-body`, choose(bodyCn, bodyEn), x + 18, y + railHeight + 7,
      width - 36, height - railHeight - 14, {fontSize: extra.bodySize || 34, bold: extra.bodyBold || false});
  };
  const sem = (from, to, kind) => semanticEdges.push({from, to, kind});
  return {number, lang, fontFamily, ops, labels, semanticEdges, choose, text, box,
    line, arrow, path, panel, node, sem};
}

function diagram2(p) {
  const {text, box, line, arrow, path, node, choose, sem} = p;
  const columns=[{letter:'a',x:60,w:420,cn:'人工标注经验',en:'Annotation\npractice'},
    {letter:'b',x:580,w:450,cn:'参考结构与规则',en:'Reference\nstructures'},
    {letter:'c',x:1150,w:390,cn:'辅助任务监督',en:'Auxiliary\ntasks'}];
  for (const col of columns) {
    text(`f2-${col.letter}-letter`,col.letter,col.x,28,42,94,{fontSize:42,bold:true,align:'left'});
    text(`f2-${col.letter}-title`,choose(col.cn,col.en),col.x+55,28,col.w-55,94,
      {fontSize:42,bold:true,align:'left'});
    line(`f2-${col.letter}-rule`,col.x,128,col.x+col.w,128,{color:C.ink,width:2});
  }
  text('f2-aux-count',choose('12类语料辅助任务','12 corpus-derived types'),1150,133,390,40,
    {fontSize:p.lang==='en'?30:34,color:C.muted});
  box('f2-reference-shared',560,174,490,680,{stroke:C.teal,strokeWidth:2.5});
  box('f2-reference-rail',560,174,490,6,{fill:C.teal,stroke:C.teal,strokeWidth:0});
  box('f2-aux-shared',1130,174,430,680,{stroke:C.blue,strokeWidth:2});
  box('f2-aux-rail',1130,174,430,6,{fill:C.blue,stroke:C.blue,strokeWidth:0});
  const ys=[185,355,525,695], centers=ys.map(y=>y+72.5);
  const left=[['界定小句范围','Set clause\nboundaries'],['辨识词法单位','Identify\nlexical units'],
    ['分析局部句法','Analyze\nlocal syntax'],['说明构式关系','Relate\nconstructions']];
  const mid=[['整句—小句层级','Sentence–clause\nhierarchy'],
    ['词类与词内关系','POS + word-internal\nrelations'],
    ['成分与谓核配置\n规则派生单核结构','Constituents + predicate cores\nSingle-core derivation'],
    ['构式关系与完整XML','Constructions +\ncomplete XML']];
  for(let i=0;i<4;i++) {
    const y=ys[i];
    box(`f2-operation-${i}`,60,y,420,145,{stroke:C.grid,strokeWidth:2});
    text(`f2-operation-text-${i}`,choose(...left[i]),78,y+16,384,113,{fontSize:36,bold:true});
    text(`f2-reference-text-${i}`,choose(...mid[i]),580,y+12,450,120,
      {fontSize:i===2 && p.lang==='en'?32:34,bold:true});
    arrow(`f2-correspondence-${i}`,480,centers[i],560,centers[i],{color:C.gray,width:2});
    if(i<3) {
      line(`f2-reference-divider-${i}`,580,y+157,1030,y+157,{color:C.grid,width:1.5});
      line(`f2-aux-divider-${i}`,1150,y+157,1540,y+157,{color:C.grid,width:1.5});
    }
  }
  text('f2-aux-clause',choose('小句切分','Clause segmentation'),1150,205,390,106,{fontSize:36,bold:true});
  text('f2-aux-lexical',choose('分词与动态词','Segmentation +\ndynamic words'),1150,370,390,114,{fontSize:36,bold:true});
  text('f2-aux-paired-title',choose('词性与成分','POS + constituents'),1150,534,390,46,{fontSize:36,bold:true});
  text('f2-aux-paired-inputs',choose('给定XML：解读\n仅给原句：分析','Given XML: interpret\nText only: analyze'),
    1150,584,390,84,{fontSize:p.lang==='en'?30:34});
  text('f2-aux-syntax-title',choose('句法与XML检查','Syntax + XML checks'),1150,704,390,47,{fontSize:36,bold:true});
  text('f2-aux-syntax-body',choose('单核、辖域、句式\nXML检查与修复','Single-core, scope, patterns\nXML checking and repair'),
    1150,756,390,84,{fontSize:p.lang==='en'?30:34});
  // A single branch from the complete reference supplies all task families.
  line('f2-shared-reference-out',1050,514,1090,514,{color:C.teal});
  line('f2-shared-reference-bus',1090,centers[0],1090,centers[3],{color:C.teal});
  centers.forEach((y,i)=>arrow(`f2-reference-aux-${i}`,1090,y,1130,y,{color:C.teal}));
  text('f2-static-note',choose('静态符号任务见图1','Symbol tasks: see Fig. 1'),60,872,420,58,
    {fontSize:p.lang==='en'?30:34,color:C.muted,align:'left'});
  node('f2-main','整句标注主任务','Whole-sentence main task',
    '输入：任务要求＋原句\n目标：分步说明＋最终XML',
    'Input: instruction + source sentence\nTarget: explanation + final XML',
    60,975,970,190,C.orange);
  node('f2-sft','混合监督微调','Mixed-task SFT',
    'SPS标注\n与分析说明','SPS annotation\n+ explanation',1180,995,360,155,C.teal);
  path('f2-reference-main',[[805,854],[805,920],[545,920],[545,975]],{color:C.teal});
  path('f2-aux-training',[[1345,854],[1345,925],[1360,925],[1360,995]],{color:C.blue});
  arrow('f2-main-training',1030,1072,1180,1072,{color:C.orange});
  sem('annotation_practice','reference_structure','conceptual_correspondence');
  sem('complete_reference','auxiliary_task_families','one_to_many_derivation');
  sem('complete_reference','main_task','direct_reference_derived_target');
  sem('auxiliary_tasks','mixed_SFT','mixed_supervision');
  sem('main_task','mixed_SFT','mixed_supervision');
  p.quantities={corpusAuxiliaryTypes:12,mainTaskTypes:1,staticTypesInFigure1:2};
  p.notes=['Parallel analysis concerns, not temporal stages.','Single-core representations are rule-derived.',
    'Main XML is supplied by the reference, not auxiliary predictions.',
    'XML-visible/text-only pairing applies specifically to POS and constituent tasks.'];
}

function diagram4(p) {
  const {text,box,line,arrow,path,panel,node,choose,sem}=p;
  panel('a','文件组织','File organization',60,28,710);
  panel('b','数据关系','Data relationships',840,28,700);
  text('f4-root','jubenwei_instructions/',100,115,680,54,{fontSize:36,bold:true,align:'left'});
  const treeColor=C.gray;
  line('f4-tree-trunk',104,174,104,852,{color:treeColor,width:2});
  const branch=(id,label,y,detailCn='',detailEn='')=>{
    line(`${id}-branch`,104,y+23,140,y+23,{color:treeColor,width:2});
    text(`${id}-path`,label,150,y,620,46,{fontSize:34,bold:true,align:'left'});
    if(detailCn||detailEn)text(`${id}-detail`,choose(detailCn,detailEn),150,y+48,620,46,
      {fontSize:p.lang==='en'?32:34,color:C.muted,align:'left'});
  };
  const leaf=(id,label,y,parentY)=>{
    // The training subtree stays left of the detail text, which starts at x=150.
    const stemX=id.startsWith('f4-training-')?128:132;
    line(`${id}-stem`,stemX,parentY+23,stemX,y+22,{color:treeColor,width:1.6});
    line(`${id}-twig`,stemX,y+22,192,y+22,{color:treeColor,width:1.6});
    text(`${id}-label`,label,202,y,580,44,{fontSize:p.lang==='en'?30:34,align:'left'});
  };
  branch('f4-sources','source_annotations/',195,'27个XML · 5,016条整句','27 XML files · 5,016 sentences');
  branch('f4-normalized','normalized/',310);
  leaf('f4-normalized-pairs','sentence_xml_pairs.json  (5,016)',360,310);
  branch('f4-full','sft_tasks/',435,'15类任务 · 392,871条','15 task files · 392,871 records');
  branch('f4-training','training_instance/',555,'4个训练JSON · 15,742条','4 training JSONs · 15,742 records');
  leaf('f4-training-main','overall_1.json  (3,635)',655,555);
  leaf('f4-training-aux','integrated_data.json  (12,000)',707,555);
  leaf('f4-training-symbol1','learn_tag_1.json  (54)',759,555);
  leaf('f4-training-symbol2','learn_tag_2.json  (53)',811,555);
  // Continue the root trunk below the training-file subtree.
  line('f4-tree-trunk-extension',104,852,104,922,{color:treeColor,width:2});
  branch('f4-evaluation','evaluation/',899);
  leaf('f4-reference','reference.json  (1,200)',951,899);
  leaf('f4-predictions','predictions/  (6 × 1,200)',1003,899);
  leaf('f4-scores',choose('scores/  (6份报告)','scores/  (6 reports)'),1055,899);
  text('f4-tree-note',choose('其余文件与完整路径见表7','Other files and full paths: Table 7'),
    100,1130,680,50,{fontSize:p.lang==='en'?30:34,color:C.muted,align:'left'});
  // Compact derivation graph, independent from directory-containment lines.
  node('f4-source-graph','来源记录','Source records','5,016条配对','5,016 pairs',
    1010,150,510,115,C.teal);
  node('f4-full-graph','完整任务','Full tasks','392,871条','392,871 records',
    840,355,330,120,C.teal,{bodySize:p.lang==='en'?32:34});
  node('f4-test-graph','固定测试参考','Fixed reference','1,200条记录\n1,100种整句','1,200 records\n1,100 texts',
    1210,355,330,145,C.blue,{bodySize:p.lang==='en'?32:34});
  path('f4-source-full',[[1265,265],[1265,307],[1005,307],[1005,355]]);
  path('f4-source-test',[[1265,265],[1265,307],[1375,307],[1375,355]],{color:C.blue});
  node('f4-definitions','符号释义表','Definitions','107条符号样本','107 symbol records',
    840,560,330,115,C.orange,{bodySize:p.lang==='en'?32:34});
  node('f4-remaining','整句文本筛选','Text exclusion','排除1,381条\n保留3,635条','Exclude 1,381\nKeep 3,635',
    1210,560,330,155,C.blue);
  arrow('f4-reference-exclusion',1375,500,1375,560,{color:C.blue});
  path('f4-source-remaining',[[1520,207],[1570,207],[1570,520],[1375,520],[1375,560]],{color:C.blue});
  arrow('f4-definitions-full',1005,560,1005,475,{color:C.orange});
  box('f4-regenerate-frame',1210,760,330,120,{stroke:C.blue});
  text('f4-regenerate-label',choose('重新派生任务\n并采样','Regenerate tasks\nand sample'),
    1226,774,298,92,{fontSize:36,bold:true});
  arrow('f4-remaining-regenerate',1375,715,1375,760,{color:C.blue});
  // Static definitions remain an independent input to both collections.
  line('f4-symbols-train-a',1005,675,1005,935,{color:C.orange});
  line('f4-symbols-train-b',1005,935,1240,935,{color:C.orange});
  line('f4-tasks-train-a',1375,880,1375,935,{color:C.blue});
  line('f4-tasks-train-b',1375,935,1240,935,{color:C.blue});
  arrow('f4-merged-training',1240,935,1240,1010);
  node('f4-train-graph','训练集','Training set','15,742条\ntraining_instance/',
    '15,742 records\ntraining_instance/',900,1010,640,145,C.teal);
  sem('root','source_annotations/','directory_containment');
  sem('root','normalized/','directory_containment');
  sem('root','sft_tasks/','directory_containment');
  sem('root','training_instance/','directory_containment');
  sem('root','evaluation/','directory_containment');
  sem('source_records','full_tasks','generate_corpus_tasks');
  sem('symbol_definitions','full_tasks','independent_static_merge');
  sem('source_records','test_reference','record_allocation');
  sem('source_records','remaining_records','whole_text_exclusion');
  sem('test_reference','remaining_records','whitespace_normalized_text_match');
  sem('remaining_records','training_set','regenerate_then_sample');
  sem('symbol_definitions','training_set','independent_static_merge');
  p.quantities={sourceRecords:5016,fullRecords:392871,testRecords:1200,uniqueTestTexts:1100,excludedSourceRecords:1381,
    trainingSourceRecords:3635,trainingRecords:15742,trainingFileCounts:[3635,12000,54,53],
    predictionConditions:6,predictionsPerCondition:1200};
  p.notes=['Four training JSON files is not the total file count of training_instance/.',
    'No full-task-row sampling edge connects sft_tasks to training_instance.',
    'The directory tree lists principal data files; other paths remain in Table7.'];
}
export function buildDiagramPlan(number, lang='en', fonts={}) {
  const p=makePlan(Number(number),lang,fonts);
  if (Number(number)===2) diagram2(p);
  else if (Number(number)===4) diagram4(p);
  else throw new Error(`Diagram ${number} is not implemented yet`);
  const bounds=[];
  p.ops.forEach(o=>{
    const xs=o.kind==='line'||o.kind==='arrow'?[o.x1,o.x2]:[o.x,o.x+o.w];
    const ys=o.kind==='line'||o.kind==='arrow'?[o.y1,o.y2]:[o.y,o.y+o.h];
    if(Math.min(...xs)<0||Math.max(...xs)>W||Math.min(...ys)<0||Math.max(...ys)>H)bounds.push(o.name);
  });
  if(bounds.length)throw new Error(`Objects outside canvas: ${bounds.join(', ')}`);
  return {number:p.number,lang:p.lang,width:W,height:H,contentHeight:1200,operations:p.ops,
    verificationData:{nativeOnly:true,containsRaster:false,
      labelCount:p.labels.length,operationCount:p.ops.length,minFontSize:Math.min(...p.labels.map(t=>t.fontSize)),
      labels:p.labels,semanticEdges:p.semanticEdges,quantities:p.quantities,notes:p.notes||[],boundsPassed:true}};
}

export async function addDiagram(presentation, number, lang, helpers) {
  const plan=buildDiagramPlan(number,lang,helpers.fonts || {});
  const slide=await helpers.canvas(presentation,plan.lang);
  for(const o of plan.operations){
    if(o.kind==='text')await helpers.text(slide,o.name,o.value,o.x,o.y,o.w,o.h,o.opts);
    else if(o.kind==='box')await helpers.box(slide,o.name,o.x,o.y,o.w,o.h,o.opts);
    else await helpers[o.kind](slide,o.name,o.x1,o.y1,o.x2,o.y2,o.opts);
  }
  return {slideId:slide.id,verificationData:plan.verificationData};
}
