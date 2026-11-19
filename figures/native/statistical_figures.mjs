/**
 * Editable statistical figures 3, 5, 6 and 7.
 * The runner supplies a Presentation object and the shared drawing helpers.
 * Native chart series retain raw counts and percentages.
 */
export const REQUIRED_HEIGHTS = Object.freeze({ 3: 1500, 5: 1500, 6: 1500, 7: 1500 });
export const LOG_PANEL_IMPLEMENTATION = Object.freeze({
  '3a': 'Editable shapes with exact log10(count) coordinates',
  '6a': 'Editable shapes with exact log10(count) coordinates',
  '6b': 'Editable shapes with exact log10(count) coordinates',
  reason: 'Logarithmic panels position editable shapes on exact log10 axes while retaining raw counts.',
});

const DEFAULT_PALETTE = Object.freeze({
  ink: '#17324D', muted: '#536575', teal: '#087F8C', blue: '#2F6B9A',
  orange: '#C57A32', light_teal: '#EDF7F7', light_blue: '#EEF4F9',
  light_orange: '#FBF3E9', grid: '#DCE4EA', gray: '#B7C2CB', white: '#FFFFFF',
});
let localContract;

async function getContract(helpers) {
  if (helpers.contract) return helpers.contract;
  if (helpers.figureContract) return helpers.figureContract;
  if (!localContract) {
    const { readFile } = await import('node:fs/promises');
    localContract = JSON.parse(await readFile(new URL('../data/figure_data.json', import.meta.url), 'utf8'));
  }
  return localContract;
}

const ensure = (condition, message) => { if (!condition) throw new Error(message); };
const sum = values => values.reduce((a, b) => a + b, 0);
const int = value => Number(value).toLocaleString('en-US', { maximumFractionDigits: 0 });
const choose = (lang, en, zh) => lang === 'zh' ? zh : en;
const figure = (contract, n) => contract.figures.find(f => f.number === n);

export function validateStatData(contract) {
  ensure(contract.tasks.length === 15, 'Expected 15 task categories.');
  ensure(sum(contract.tasks.map(r => r.full_n)) === 392871, 'Full-resource count changed.');
  ensure(sum(contract.tasks.map(r => r.training_n)) === 15742, 'Training count changed.');
  const f5 = figure(contract, 5), f6 = figure(contract, 6), f7 = figure(contract, 7);
  ensure(f5.panels[0].rows.length === 15, 'Expected 15 quantile rows.');
  for (const row of f5.panels[0].rows) {
    ensure(row.p10 > 0 && row.p10 <= row.p25 && row.p25 <= row.median && row.median <= row.p75 && row.p75 <= row.p90,
      `Invalid quantile ordering: ${row.stem}`);
  }
  ensure(sum(f5.panels[1].rows.map(r => r.count)) === 392871, 'Supervision counts changed.');
  ensure(sum(f6.panels[0].rows.map(r => r.count)) === 17240, 'scp counts changed.');
  ensure(sum(f6.panels[1].rows.map(r => r.count)) === 5325, 'fun counts changed.');
  ensure(sum(f6.panels[2].rows.map(r => r.count)) === 5177, 'Top-ten mod count changed.');
  ensure(f6.panels[0].rows.find(r => r.code === 'VOCC')?.count === 1, 'VOCC must remain one.');
  ensure(f7.conditions.map(r => r.valid).join(',') === '831,1116,739,999,905,1137', 'Condition order/denominators changed.');
  ensure(f7.conditions.map(r => r.display.parsable_text_consistent_percent).join(',') === '14.25,85.75,11.17,52.92,17.92,85.50', 'Text-fidelity rates changed.');
  for (const row of f7.conditions) {
    ensure(row.total === 1200 && row.valid + row.invalid === 1200, `Invalid total: ${row.id}`);
    ensure(row.text_consistent + row.text_mismatch === row.valid, `Invalid text partition: ${row.id}`);
    ensure(row.metrics.f1_percent.length === 4, `Missing F1 values: ${row.id}`);
  }
  return { figures: [3, 5, 6, 7], full: 392871, training: 15742, quantileRows: 15, modelConditions: 6 };
}

function context(slide, lang, helpers) {
  const zh = lang === 'zh';
  const palette = { ...DEFAULT_PALETTE, ...(helpers.palette || {}) };
  const font = helpers.fonts?.[lang] || (zh ? 'Microsoft YaHei' : 'Arial');
  const fs = zh ? 34 : 30;
  const txt = (name, value, x, y, w, h, opts = {}) => helpers.text(slide, name, value, x, y, w, h,
    { fontFamily: font, fontSize: fs, color: palette.ink, verticalAlign: 'middle', ...opts });
  const ln = (name, x1, y1, x2, y2, opts = {}) => helpers.line(slide, name, x1, y1, x2, y2,
    { color: palette.grid, width: 1.5, ...opts });
  const rect = (name, x, y, w, h, opts = {}) => helpers.box(slide, name, x, y, w, h,
    { fill: palette.white, stroke: 'none', strokeWidth: 0, radius: 0, ...opts });
  const heading = (name, value, x, y, w, opts = {}) => txt(name, value, x, y, w, 60,
    { fontSize: 42, bold: true, ...opts });
  return { slide, lang, zh, palette, font, fs, txt, ln, rect, heading };
}

/**
 * xAxis is the native category axis; yAxis is the native numeric axis even
 * for horizontal bars. orientation=maxMin places the first category on top.
 * Numeric percentages are already in the range 0..100: no '%' number format.
 */
function horizontalChart(ctx, position, categories, series, opts = {}) {
  const { palette: p, font, fs } = ctx;
  const textStyle = { typeface: font, fontSize: fs, fill: p.ink };
  const chart = ctx.slide.charts.add('bar', {
    position,
    categories,
    series: series.map(s => ({
      ...s,
      line: { style: 'solid', fill: 'none', width: 0 },
      valuesFormatCode: opts.format || '#,##0',
    })),
    titlePlacement: 'none',
    hasLegend: false,
    barOptions: { direction: 'bar', grouping: 'clustered', gapWidth: opts.gapWidth ?? 52, overlap: 0 },
    chartFill: p.white,
    chartLine: { style: 'solid', fill: 'none', width: 0 },
    plotAreaFill: p.white,
    plotAreaLine: { style: 'solid', fill: 'none', width: 0 },
    xAxis: {
      visible: true,
      orientation: 'maxMin',
      tickLabelPosition: opts.showCategories === false ? 'none' : 'low',
      majorTickMark: 'none',
      minorTickMark: 'none',
      majorGridlines: null,
      minorGridlines: null,
      line: { style: 'solid', fill: 'none', width: 0 },
      textStyle,
      labelOffsetPercent: 60,
    },
    yAxis: {
      visible: true,
      min: opts.min ?? 0,
      max: opts.max,
      ...(opts.log ? { logBase: 10 } : {}),
      ...(opts.majorUnit ? { majorUnit: opts.majorUnit } : {}),
      numberFormatCode: opts.axisFormat || '#,##0',
      numberFormatSourceLinked: false,
      textStyle,
      majorTickMark: 'none',
      minorTickMark: 'none',
      majorGridlines: { fill: p.grid, width: 1, style: 'solid' },
      minorGridlines: null,
      line: { style: 'solid', fill: p.grid, width: 1.5 },
    },
    dataLabels: {
      showValue: true,
      position: 'outEnd',
      numberFormatCode: opts.format || '#,##0',
      numberFormatSourceLinked: false,
      textStyle: { ...textStyle, fontSize: fs, fill: p.ink },
    },
  });
  // Verify that logarithmic axes preserve their scale when requested.
  if (opts.log) ensure(chart.yAxis?.logBase === 10, 'Native chart failed to preserve logBase=10.');
  return chart;
}

/** Exact logarithmic bars as editable native objects; all counts stay raw. */
function logarithmicBars(ctx, name, position, rows, opts) {
  const { txt, ln, rect, palette: p } = ctx;
  const min = 1, max = opts.max;
  const labelWidth = opts.labelWidth;
  const plotLeft = position.left + labelWidth;
  const plotWidth = position.width - labelWidth - 112;
  const plotTop = position.top + 10;
  const plotHeight = position.height - 88;
  const rowPitch = plotHeight / rows.length;
  const axisY = plotTop + plotHeight;
  const mapX = value => plotLeft + Math.log10(value / min) / Math.log10(max / min) * plotWidth;
  ensure(plotWidth > 0 && rows.every(r => r.count >= 1 && r.count <= max), `${name}: invalid log plot`);
  const tickText = { 1: '1', 10: '10', 100: '10²', 1000: '10³', 10000: '10⁴', 100000: '10⁵' };
  for (const value of [1, 10, 100, 1000, 10000, 100000].filter(v => v <= max)) {
    const x = mapX(value);
    ln(`${name}-grid-${value}`, x, plotTop, x, axisY, { color: p.grid, width: 1 });
    ln(`${name}-tick-${value}`, x, axisY, x, axisY + 7, { color: p.muted, width: 1.5 });
    txt(`${name}-tick-label-${value}`, tickText[value], x - 45, axisY + 11, 90, 44,
      { align: 'center', color: p.muted });
  }
  ln(`${name}-axis`, plotLeft, axisY, plotLeft + plotWidth, axisY, { color: p.muted, width: 1.5 });
  rows.forEach((r, index) => {
    const y = plotTop + (index + 0.5) * rowPitch;
    const x = mapX(r.count);
    const barHeight = Math.min(32, rowPitch * 0.58);
    const idWidth = r.taskId ? 62 : 0;
    const widenChineseTaskNumbers = ctx.zh && name === 'f3-a';
    if (r.taskId) txt(`${name}-task-id-${r.key}`, r.taskId, position.left, y - 22,
      widenChineseTaskNumbers ? 90 : idWidth, 44,
      { color: p.muted, ...(widenChineseTaskNumbers ? { wrap: false } : {}) });
    txt(`${name}-category-${r.key}`, r.label, position.left + idWidth, y - 22,
      labelWidth - idWidth - 18, 44, { align: 'right', ...(r.noWrap ? { wrap: false } : {}) });
    if (r.count === 1) {
      ln(`${name}-unit-marker-${r.key}`, plotLeft, y - barHeight / 2, plotLeft, y + barHeight / 2,
        { color: opts.fill, width: 3 });
    } else {
      rect(`${name}-bar-${r.key}`, plotLeft, y - barHeight / 2, x - plotLeft, barHeight,
        { fill: opts.fill });
    }
    txt(`${name}-count-${r.key}`, int(r.count), x + 10, y - 22,
      widenChineseTaskNumbers ? 150 : 104, 44,
      widenChineseTaskNumbers ? { wrap: false } : {});
  });
}

function addFigure3(ctx, contract) {
  const { txt, heading, ln, palette: p, lang } = ctx;
  const tasks = contract.tasks;
  const categories = tasks.map(r => r[lang === 'zh' ? 'label_zh' : 'label_en']);
  heading('f3-a-title', choose(lang, 'a  Full instruction resource', 'a  完整指令资源'), 62, 35, 1000);
  heading('f3-b-title', choose(lang, 'b  Training set', 'b  训练集'), 1080, 35, 470);
  txt('f3-a-n', 'n = 392,871', 62, 98, 1000, 44, { color: p.muted });
  txt('f3-b-n', 'n = 15,742', 1080, 98, 470, 44, { color: p.muted });
  ln('f3-divider', 1040, 50, 1040, 1195, { color: p.grid, width: 1.5 });
  logarithmicBars(ctx, 'f3-a', { left: 42, top: 210, width: 988, height: 890 },
    tasks.map((r, i) => ({ key: r.stem, taskId: r.id, label: categories[i], count: r.full_n })),
    { labelWidth: 470, max: 600000, fill: p.blue });
  // Compact task IDs independently identify native-chart rows even if its
  // automatic plot margins differ from the editable logarithmic panel.
  horizontalChart(ctx, { left: 1060, top: 160, width: 492, height: 890 }, tasks.map(r => r.id),
    [{ name: choose(lang, 'Training', '训练'), values: tasks.map(r => r.training_n), fill: p.teal }],
    { min: 0, max: 4600, majorUnit: 2000, showCategories: true, gapWidth: 45 });
  txt('f3-log-label', choose(lang, 'Records (log scale)', '样本数（对数尺度）'), 480, 1120, 530, 48, { align: 'center' });
  txt('f3-linear-label', choose(lang, 'Records (linear scale)', '样本数（线性尺度）'), 1060, 1120, 492, 48, { align: 'center' });
  txt('f3-training-composition', choose(lang,
    'Training: 3,635 main + 12,000 auxiliary + 107 symbols',
    '训练集：3,635条主任务 + 12,000条辅助任务 + 107条符号样本'),
  70, 1200, 1480, 48, { color: p.muted, align: 'center' });
}

function addFigure5(ctx, contract) {
  const { txt, heading, ln, rect, palette: p, lang, font, fs } = ctx;
  const f = figure(contract, 5);
  const rows = f.panels[0].rows;
  const taskMap = new Map(contract.tasks.map(r => [r.stem, r]));
  const plot = { x: 520, w: 840, top: 178, pitch: 43, bottom: 806 };
  const lo = Math.log10(0.8), hi = Math.log10(5500);
  const px = value => plot.x + (Math.log10(value) - lo) / (hi - lo) * plot.w;
  heading('f5-a-title', choose(lang, 'a  Target-response lengths', 'a  目标响应长度分布'), 60, 26, 1440);
  const ly = 112;
  ln('f5-range-legend', 610, ly + 15, 675, ly + 15, { color: p.muted, width: 2 });
  ln('f5-range-cap1', 610, ly + 6, 610, ly + 24, { color: p.muted, width: 2 });
  ln('f5-range-cap2', 675, ly + 6, 675, ly + 24, { color: p.muted, width: 2 });
  txt('f5-range-legend-text', 'P10–P90', 690, ly - 5, 180, 42);
  rect('f5-iqr-legend', 895, ly + 5, 64, 22, { fill: p.blue });
  txt('f5-iqr-legend-text', 'P25–P75', 975, ly - 5, 190, 42);
  ln('f5-median-legend', 1200, ly + 2, 1200, ly + 29, { color: p.ink, width: 3 });
  txt('f5-median-legend-text', choose(lang, 'Median', '中位数'), 1215, ly - 5, 180, 42);
  txt('f5-median-col', choose(lang, 'Median', '中位数'), 1410, 110, 130, 42, { align: 'right', bold: true });
  for (const tick of [1, 10, 100, 1000]) {
    const x = px(tick);
    ln(`f5-grid-${tick}`, x, plot.top - 17, x, plot.bottom, { color: p.grid, width: 1 });
    txt(`f5-tick-${tick}`, int(tick), x - 65, plot.bottom + 10, 130, 42, { align: 'center', color: p.muted });
  }
  rows.forEach((row, i) => {
    const y = plot.top + i * plot.pitch;
    const task = taskMap.get(row.stem);
    const main = row.stem === 'overall_1';
    const color = main ? p.orange : p.blue;
    txt(`f5-task-${row.stem}`, task[lang === 'zh' ? 'label_zh' : 'label_en'], 60, y - 21, 425, 42,
      { align: 'right', bold: main });
    ln(`f5-p10-p90-${row.stem}`, px(row.p10), y, px(row.p90), y, { color: p.muted, width: 2 });
    for (const q of ['p10', 'p90']) ln(`f5-${q}-${row.stem}`, px(row[q]), y - 8, px(row[q]), y + 8,
      { color: p.muted, width: 2 });
    if (row.p75 > row.p25) rect(`f5-p25-p75-${row.stem}`, px(row.p25), y - 11,
      px(row.p75) - px(row.p25), 22, { fill: color, stroke: p.ink, strokeWidth: 1 });
    ln(`f5-median-${row.stem}`, px(row.median), y - 15, px(row.median), y + 15, { color: p.ink, width: 3 });
    txt(`f5-median-value-${row.stem}`, row.median_display, 1410, y - 21, 130, 42,
      { align: 'right', bold: main });
  });
  ln('f5-log-axis', plot.x, plot.bottom, plot.x + plot.w, plot.bottom, { color: p.muted, width: 1.5 });
  txt('f5-axis-title', choose(lang, 'Output length (Unicode code points, log scale)', 'output长度（Unicode码点，对数尺度）'),
    495, 858, 900, 45, { align: 'center' });
  heading('f5-b-title', choose(lang, 'b  Supervision formats', 'b  监督目标类型'), 60, 925, 1440);
  const formats = f.panels[1].rows;
  ctx.slide.charts.add('bar', {
    position: { left: 220, top: 990, width: 1240, height: 340 },
    categories: formats.map(r => r[lang === 'zh' ? 'label_zh' : 'label_en']),
    series: [{
      name: choose(lang, 'Records', '样本数'),
      values: formats.map(r => r.count),
      fill: p.teal,
      line: { style: 'solid', fill: 'none', width: 0 },
      valuesFormatCode: '#,##0',
      points: [{ idx: 0, fill: p.teal }, { idx: 1, fill: p.blue }],
      dataLabelOverrides: formats.map((r, idx) => ({ idx, text: `${int(r.count)} (${r.display_percent}%)`,
        showValue: false, position: 'outEnd', textStyle: { typeface: font, fontSize: fs, fill: p.ink } })),
    }],
    hasLegend: false,
    titlePlacement: 'none',
    barOptions: { direction: 'column', grouping: 'clustered', gapWidth: 160 },
    chartFill: p.white, chartLine: { style: 'solid', fill: 'none', width: 0 },
    plotAreaFill: p.white, plotAreaLine: { style: 'solid', fill: 'none', width: 0 },
    xAxis: { visible: true, orientation: 'minMax', textStyle: { typeface: font, fontSize: fs, fill: p.ink },
      majorTickMark: 'none', line: { style: 'solid', fill: p.grid, width: 1 }, majorGridlines: null },
    yAxis: { visible: true, min: 0, max: 290000, majorUnit: 100000, numberFormatCode: '#,##0',
      textStyle: { typeface: font, fontSize: fs, fill: p.muted }, majorTickMark: 'none',
      majorGridlines: { style: 'solid', fill: p.grid, width: 1 }, line: { style: 'solid', fill: 'none', width: 0 } },
    dataLabels: { showValue: true, position: 'outEnd', numberFormatCode: '#,##0',
      textStyle: { typeface: font, fontSize: fs, fill: p.ink } },
  });
  txt('f5-b-unit', choose(lang, 'Records', '样本数'), 60, 1090, 150, 46, { color: p.muted });
}

function addFigure6(ctx, contract) {
  const { txt, heading, palette: p, lang } = ctx;
  const f = figure(contract, 6);
  const [scope, fun, mod] = f.panels;
  const labels = rows => rows.map(r => `${r.code}  ${r[lang === 'zh' ? 'meaning_zh' : 'meaning_en']}`);
  heading('f6-a-title', choose(lang, 'a  Governing scope (scp)', 'a  谓核辖域 scp'), 60, 28, 735);
  heading('f6-b-title', choose(lang, 'b  Structural function (fun)', 'b  结构功能 fun'), 830, 28, 710);
  const compactChineseScopes = { VO: 'VO 谓宾', VC: 'VC 谓补', VOO: 'VOO 谓双宾', OV: 'OV 宾谓', VOC: 'VOC 谓宾补', VCO: 'VCO 谓补宾', VOCC: 'VOCC 谓宾双补' };
  logarithmicBars(ctx, 'f6-a', { left: 40, top: 110, width: 750, height: 440 },
    scope.rows.map((r, i) => ({ key: r.code,
      label: lang === 'zh' && compactChineseScopes[r.code] ? compactChineseScopes[r.code] : labels(scope.rows)[i],
      noWrap: lang === 'zh' && Boolean(compactChineseScopes[r.code]), count: r.count })),
    { labelWidth: 270, max: 100000, fill: p.blue });
  logarithmicBars(ctx, 'f6-b', { left: 805, top: 110, width: 755, height: 440 },
    fun.rows.map((r, i) => ({ key: r.code,
      label: lang !== 'zh' && ['COO', 'coo'].includes(r.code) ? `${r.code} Coord.` : labels(fun.rows)[i],
      count: r.count })),
    { labelWidth: 285, max: 20000, fill: p.teal });
  txt('f6-a-axis', choose(lang, 'Occurrences (log scale)', '出现次数（对数尺度）'), 260, 555, 500, 45, { align: 'center' });
  txt('f6-b-axis', choose(lang, 'Occurrences (log scale)', '出现次数（对数尺度）'), 1030, 555, 500, 45, { align: 'center' });
  heading('f6-c-title', choose(lang, 'c  Dynamic-word patterns (mod): top 10', 'c  动态词结构模式 mod（前10种）'), 60, 615, 1480);
  horizontalChart(ctx, { left: 60, top: 685, width: 1490, height: 450 }, labels(mod.rows),
    [{ name: 'mod', values: mod.rows.map(r => r.count), fill: p.orange }],
    { min: 0, max: 1100, majorUnit: 250, gapWidth: 40 });
  txt('f6-c-axis', choose(lang, 'Pattern occurrences', '模式出现次数'), 650, 1148, 800, 45, { align: 'center' });
  txt('f6-total-note', choose(lang, '5,016 target XML records; 593 mod patterns', '5,016条目标XML；593种mod模式'),
    60, 1200, 1480, 42, { color: p.muted, align: 'center' });
}

function addFigure7(ctx, contract) {
  const { txt, heading, rect, palette: p, lang } = ctx;
  const f = figure(contract, 7);
  const rows = new Map(f.conditions.map(r => [r.id, r]));
  rect('f7-pre-legend', 430, 38, 46, 26, { fill: p.gray });
  txt('f7-pre-legend-label', choose(lang, 'No task SFT', '未SFT'), 495, 25, 280, 50);
  rect('f7-post-legend', 870, 38, 46, 26, { fill: p.blue });
  txt('f7-post-legend-label', choose(lang, 'After task SFT', 'SFT后'), 935, 25, 340, 50);
  const positions = [
    { x: 45, y: 100 }, { x: 825, y: 100 },
    { x: 45, y: 550 }, { x: 825, y: 550 },
    { x: 45, y: 1000 }, { x: 825, y: 1000 },
  ];
  const groupLabels = choose(lang, ['Qwen2.5', 'Qwen3\nThinking off', 'Qwen3\nThinking on'], ['Qwen2.5', 'Qwen3\n思考关', 'Qwen3\n思考开']);
  const f1Labels = choose(lang, ['Segmentation', 'POS', 'Dynamic words', 'Syntax'], ['分词', '词性', '动态词', '句法']);
  f.panels.forEach((panel, i) => {
    const { x, y } = positions[i];
    const width = 730;
    heading(`f7-${panel.id}-title`, `${panel.id}  ${panel[lang === 'zh' ? 'title_zh' : 'title_en']}`,
      x, y, width, { fontSize: 38 });
    const isF1 = panel.metric === 'f1_percent';
    const subtitle = isF1
      ? `F1 (%)    n = ${int(panel.denominators[0])} / ${int(panel.denominators[1])}`
      : choose(lang, panel.id === 'f' ? 'Exact matches (%)    n = 1,200' : 'Outputs (%)    n = 1,200',
        panel.id === 'f' ? '完全匹配率（%）  n = 1,200' : '输出比例（%）  n = 1,200');
    txt(`f7-${panel.id}-denominator`, subtitle, x, y + 54, width, 45, { color: p.muted });
    const categories = isF1 ? f1Labels : groupLabels;
    const series = [0, 1].map(j => {
      const values = isF1
        ? rows.get(panel.conditions[j]).metrics.f1_percent
        : panel.groups.map(g => rows.get(g.conditions[j]).metrics[panel.metric]);
      return { name: j === 0 ? choose(lang, 'No task SFT', '未SFT') : choose(lang, 'After task SFT', 'SFT后'),
        values, fill: j === 0 ? p.gray : p.blue };
    });
    horizontalChart(ctx, { left: x, top: y + 98, width, height: 340 }, categories, series,
      { min: 0, max: panel.id === 'f' ? 43 : 116, majorUnit: panel.id === 'f' ? 10 : 50,
        format: '0.00', axisFormat: '0', gapWidth: isF1 ? 0 : 25 });
  });
  txt('f7-f1-note', choose(lang,
    'F1 uses each condition’s parsable predictions, including text mismatches.',
    'F1基于各条件的可解析预测，其中包含文本不一致输出。'),
  65, 1448, 1470, 48, { color: p.muted, align: 'center' });
}

/** Add exactly one statistical figure to the supplied presentation. */
export async function addStatFigure(presentation, number, lang = 'en', helpers) {
  ensure([3, 5, 6, 7].includes(number), `Unsupported statistical figure: ${number}`);
  ensure(helpers && ['canvas', 'text', 'box', 'line'].every(k => typeof helpers[k] === 'function'),
    'Shared canvas/text/box/line helpers are required.');
  const contract = await getContract(helpers);
  validateStatData(contract);
  const slide = helpers.canvas(presentation, lang, { width: 1600, height: REQUIRED_HEIGHTS[number] });
  const ctx = context(slide, lang, helpers);
  ({ 3: addFigure3, 5: addFigure5, 6: addFigure6, 7: addFigure7 })[number](ctx, contract);
  return slide;
}
