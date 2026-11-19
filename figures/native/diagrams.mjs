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
  const columns=[{letter:'a',x:60,w:420,cn:'人工标注判断',en:'Annotator\njudgments'},
    {letter:'b',x:580,w:450,cn:'参考XML与规则',en:'Reference XML\n+ rules'},
    {letter:'c',x:1150,w:390,cn:'模板派生任务',en:'Task\ntemplates'}];
  for (const col of columns) {
    text(`f2-${col.letter}-letter`,col.letter,col.x,28,42,94,{fontSize:42,bold:true,align:'left'});
    text(`f2-${col.letter}-title`,choose(col.cn,col.en),col.x+55,28,col.w-55,94,
      {fontSize:42,bold:true,align:'left'});
    line(`f2-${col.letter}-rule`,col.x,128,col.x+col.w,128,{color:C.ink,width:2});
  }
  text('f2-recorded-note',choose('保存在源XML中','Recorded in source XML'),60,133,420,40,
    {fontSize:p.lang==='en'?30:34,color:C.muted});
  text('f2-aux-count',choose('12类语料辅助任务','12 corpus-derived types'),1150,133,390,40,
    {fontSize:p.lang==='en'?30:34,color:C.muted});
  box('f2-reference-shared',560,174,490,680,{stroke:C.teal,strokeWidth:2.5});
  box('f2-reference-rail',560,174,490,6,{fill:C.teal,stroke:C.teal,strokeWidth:0});
  box('f2-aux-shared',1130,174,430,680,{stroke:C.blue,strokeWidth:2});
  box('f2-aux-rail',1130,174,430,6,{fill:C.blue,stroke:C.blue,strokeWidth:0});
  const ys=[185,355,525,695], centers=ys.map(y=>y+72.5);
  const left=[['界定小句范围','Set clause\nboundaries'],['辨识词法单位','Identify\nlexical units'],
    ['分析局部句法','Analyze\nlocal syntax'],['标记构式关系','Mark structural\nrelations']];
  const mid=[['整句—小句层级','Sentence–clause\nhierarchy'],
    ['词类与词内关系','POS + word-internal\nrelations'],
    ['成分与谓核配置\n规则派生单核结构','Constituents + cores\nRule-derived single cores'],
    ['构式关系与完整XML','Structural relations +\ncomplete XML']];
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
  text('f2-aux-clause',choose('小句切分','Clause segmentation'),1150,201,390,62,{fontSize:36,bold:true});
  text('f2-aux-clause-id','A9',1150,268,390,42,{fontSize:34,color:C.muted});
  text('f2-aux-lexical',choose('分词与动态词','Segmentation +\ndynamic words'),1150,366,390,87,{fontSize:36,bold:true});
  text('f2-aux-lexical-id','A5 / A7 / A8',1150,460,390,42,{fontSize:34,color:C.muted});
  text('f2-aux-paired-title',choose('词性与成分','POS + constituents'),1150,520,390,44,{fontSize:36,bold:true});
  text('f2-aux-paired-id','A3 / A6 · A4 / A11',1150,565,390,40,{fontSize:p.lang==='en'?30:34,color:C.muted});
  text('f2-aux-paired-inputs',choose('给定XML：解读\n仅给原句：分析','Given XML: interpret\nText only: analyze'),
    1150,605,390,65,{fontSize:p.lang==='en'?30:34});
  text('f2-aux-syntax-title',choose('单核、辖域与结构\nXML检查与修复','Single-core + scope\nRelations + XML checks'),
    1150,704,390,90,{fontSize:p.lang==='en'?30:34,bold:true});
  text('f2-aux-syntax-id','A10 / A12 / A13 / A14',1150,801,390,42,{fontSize:p.lang==='en'?30:34,color:C.muted});
  // A single branch from the complete reference supplies all task families.
  line('f2-shared-reference-out',1050,514,1090,514,{color:C.teal});
  line('f2-shared-reference-bus',1090,centers[0],1090,centers[3],{color:C.teal});
  centers.forEach((y,i)=>arrow(`f2-reference-aux-${i}`,1090,y,1130,y,{color:C.teal}));
  node('f2-symbols','符号任务 A1/A2','Symbol tasks A1/A2',
    '独立符号释义表','Independent glossary',60,875,420,110,C.orange);
  node('f2-main','整句标注主任务 M0','Whole-sentence main task M0',
    '输入：任务要求＋原句\n目标：模板生成的分步说明\n＋同条记录的参考XML',
    'Input: instruction + sentence\nTarget: template-generated explanation\n+ the same record’s reference XML',
    60,1030,1000,210,C.orange);
  node('f2-sft','混合任务SFT','Mixed-task SFT',
    'SPS标注\n与分析说明','SPS annotation\n+ explanation',1190,1060,350,155,C.teal);
  arrow('f2-reference-main',805,854,805,1030,{color:C.teal});
  arrow('f2-aux-training',1345,854,1345,1060,{color:C.blue});
  arrow('f2-main-training',1060,1130,1190,1130,{color:C.orange});
  path('f2-symbols-training',[[60,930],[30,930],[30,1290],[1365,1290],[1365,1215]],{color:C.orange});
  text('f2-derivation-note',choose('模板按参考标注组织说明；连线表示派生和组合关系。',
    'Templates use reference annotations; connections show derivation and combination.'),
    60,1330,1480,48,{fontSize:p.lang==='en'?30:34,color:C.muted,align:'center'});
  sem('annotation_practice','reference_structure','recorded_annotation_judgments');
  sem('complete_reference','auxiliary_task_families','one_to_many_derivation');
  sem('complete_reference','main_task','direct_reference_derived_target');
  sem('auxiliary_tasks','mixed_SFT','mixed_supervision');
  sem('main_task','mixed_SFT','mixed_supervision');
  sem('independent_glossary_A1_A2','mixed_SFT','mixed_supervision');
  p.quantities={corpusAuxiliaryTypes:12,mainTaskTypes:1,staticTypesInFigure1:2};
  p.notes=['Parallel analysis concerns, not temporal stages.','Single-core representations are rule-derived.',
    'Main XML is supplied by the reference, not auxiliary predictions.',
    'Targets are filled by rule-based templates; no annotation decision trace is claimed.',
    'XML-visible/text-only pairing applies specifically to POS and constituent tasks.'];
}

function diagram4(p) {
  const {text,box,line,arrow,path,panel,node,choose,sem}=p;
  panel('a','获取入口','Access points',60,28,710);
  panel('b','公开数据重建','Reconstruction',840,28,700);
  node('f4-release-data','指令数据 · Zenodo','Instruction data · Zenodo',
    'sft_tasks/ · 15份JSON\n392,871条样本','sft_tasks/ · 15 JSON files\n392,871 examples',
    60,170,650,180,C.teal);
  node('f4-release-code','代码与评分 · GitHub','Code + scores · GitHub',
    'code/ · configs/ · evaluation/\n构建、训练与评分材料\nreference_selection.json：固定索引',
    'code/ · configs/ · evaluation/\nScripts, settings and scores\nreference_selection.json: saved index',
    60,435,650,210,C.blue);
  node('f4-release-output','模型输出 · GitHub','Model outputs · GitHub',
    'outputs/*.jsonl\n6组条件 × 1,200条最终输出\ncase_id + output',
    'outputs/*.jsonl\n6 conditions × 1,200 final outputs\ncase_id + output',
    60,705,650,225,C.blue);
  node('f4-ldc','原始树库 · LDC','Source treebank · LDC',
    '27个源XML文件\nLDC2025T06 · 单独获取',
    '27 source XML files\nLDC2025T06 · separate access',
    60,1015,650,185,C.orange);
  text('f4-access-note',choose('网址、版本与文件说明见表7。','URLs, versions and file details: Table 7.'),
    60,1250,650,80,{fontSize:p.lang==='en'?30:34,color:C.muted,align:'left'});

  node('f4-released-main','已发布整句主任务','Released main task',
    'overall_1.json · 5,016条样本','overall_1.json · 5,016 examples',
    840,170,700,125,C.teal);
  arrow('f4-release-main',710,235,840,235,{color:C.teal});
  node('f4-recovery','恢复配对与固定参考','Recover pairs + reference',
    '5,016条配对 · 1,200条测试参考\nreproduced/public_reference/',
    '5,016 source pairs · 1,200 test records\nreproduced/public_reference/',
    840,435,700,180,C.teal);
  arrow('f4-main-recovery',1190,295,1190,435,{color:C.teal});
  arrow('f4-index-recovery',710,525,840,525,{color:C.blue});
  arrow('f4-recovery-filter',1190,615,1190,705,{color:C.blue});
  node('f4-filter','排除整句文本匹配','Exclude test-text matches',
    '5,016 − 1,381 = 3,635','5,016 − 1,381 = 3,635',
    840,705,700,125,C.blue,{bodyBold:true});
  arrow('f4-filter-regenerate',1190,830,1190,925,{color:C.blue});
  node('f4-regenerate','重新生成与采样','Regenerate and sample',
    '3,635条主任务＋12,000条辅助任务\n＋107条独立符号样本',
    '3,635 main + 12,000 auxiliary\n+107 independent glossary examples',
    840,925,700,170,C.teal);
  arrow('f4-regenerate-training',1190,1095,1190,1190,{color:C.teal});
  node('f4-training','重建训练输入','Reconstructed training inputs',
    'reproduced/training_instance/\n4份JSON · 15,742条样本',
    'reproduced/training_instance/\n4 JSON files · 15,742 examples',
    840,1190,700,160,C.teal);
  sem('Zenodo_full_tasks','released_main_task','public_file_selection');
  sem('released_main_task','source_pairs','recover_final_reference_XML');
  sem('released_main_task_and_saved_index','test_reference','restore_fixed_order');
  sem('source_pairs_and_test_reference','retained_pairs','whole_text_exclusion');
  sem('retained_pairs','training_inputs','regenerate_tasks_and_sample');
  sem('independent_glossary','training_inputs','unchanged_static_examples');
  p.quantities={sourceRecords:5016,fullExamples:392871,testRecords:1200,
    excludedSourceRecords:1381,trainingSourceRecords:3635,trainingExamples:15742,
    trainingFileCounts:[3635,12000,54,53],predictionConditions:6,outputsPerCondition:1200};
  p.notes=['Public access points are distinct from locally reconstructed directories.',
    'The public model-output archive has outputs/*.jsonl with case_id and output.',
    'Reference recovery uses the archived selection index; there is no new test draw.',
    'The 107 glossary examples are an independent contribution, not extracted from source XML.',
    'LDC files provide separate access to original annotations; public task files suffice for this reconstruction route.'];
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
  return {number:p.number,lang:p.lang,width:W,height:H,contentHeight:1380,operations:p.ops,
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
