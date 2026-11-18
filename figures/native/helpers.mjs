/** Native editable figure primitives. All geometry and font sizes use CSS px. */
import { readFileSync } from 'node:fs';

const readJson = name => JSON.parse(readFileSync(new URL(name, import.meta.url), 'utf8'));
export const design = readJson('../data/style.json');
export const contract = readJson('../data/figure_data.json');
export const palette = Object.freeze({ ...design.palette, navy: design.palette.ink });
export const colors = palette;
export const C = palette;
export const P = palette;
export const fonts = Object.freeze({ ...design.fonts });
export const fontPx = Object.freeze({ ...design.font_px });
export const W = design.canvas.width;
export const H = design.canvas.height;

// Keep the language assigned to each slide.
const languages = new Map();

const finite = (value, label) => {
  const n = Number(value);
  if (!Number.isFinite(n)) throw new TypeError(`${label} must be finite`);
  return n;
};
const positive = (value, label) => {
  const n = finite(value, label);
  if (n <= 0) throw new RangeError(`${label} must be greater than zero`);
  return n;
};
const language = value => /^(zh|cn|chinese)/i.test(String(value ?? 'en')) ? 'zh' : 'en';
const colour = (value, fallback = palette.ink) => {
  if (value === undefined || value === null) return fallback;
  return typeof value === 'string' && value in palette ? palette[value] : value;
};

export function langOf(slide, opts = {}) {
  return language(opts.lang ?? languages.get(String(slide.id)) ?? 'en');
}

export function fontFor(slide, opts = {}) {
  return opts.fontFamily ?? opts.typeface ?? fonts[langOf(slide, opts)];
}

function fontSize(slide, value, fallback, opts = {}) {
  const lang = langOf(slide, opts);
  let size = value ?? fallback;
  if (typeof size === 'string') {
    const match = size.trim().match(/^([\d.]+)\s*(px|pt)?$/i);
    if (!match) throw new TypeError(`Unsupported font size: ${size}`);
    size = Number(match[1]) * (match[2]?.toLowerCase() === 'pt' ? 96 / 72 : 1);
  }
  size = positive(size, 'font size');
  const minimum = lang === 'zh' ? 34 : 30;
  if (size < minimum) {
    throw new RangeError(`${lang} font size ${size}px is below ${minimum}px; enlarge the frame or wrap the text`);
  }
  return size;
}

function frame(x, y, w, h, allowZero = false) {
  const f = { left: finite(x, 'x'), top: finite(y, 'y'),
    width: finite(w, 'width'), height: finite(h, 'height') };
  if (f.width < 0 || f.height < 0 || (!allowZero && (f.width === 0 || f.height === 0))) {
    throw new RangeError('Shape width and height must be positive');
  }
  return f;
}

/** One common slide size for the deck; overrides must match design_system.json. */
export function canvas(presentation, lang = 'en', opts = {}) {
  const width = positive(opts.width ?? W, 'canvas width');
  const height = positive(opts.height ?? H, 'canvas height');
  if (width !== W || height !== H) {
    throw new RangeError(`Use the common ${W} x ${H} canvas for every slide`);
  }
  const slide = presentation.slides.add({
    width, height,
    background: { fill: colour(opts.fill ?? opts.background, palette.white) }
  });
  slide.background.fill = colour(opts.fill ?? opts.background, palette.white);
  languages.set(String(slide.id), language(lang));
  return slide;
}

function textStyle(slide, opts = {}, fallback = fontPx.body) {
  const align = opts.align ?? opts.alignment ?? 'left';
  let vertical = opts.verticalAlign ?? opts.verticalAlignment ?? opts.valign ?? 'middle';
  if (vertical === 'center') vertical = 'middle';
  const style = {
    typeface: fontFor(slide, opts),
    fontSize: fontSize(slide, opts.fontSize ?? opts.size, fallback, opts),
    bold: opts.bold ?? false,
    color: colour(opts.color ?? opts.fill, palette.ink),
    alignment: align,
    verticalAlignment: vertical,
    autoFit: 'none',
    wrap: opts.wrap === false || opts.wrap === 'none' ? 'none' : 'square',
    insets: opts.insets ?? 0
  };
  if (opts.italic !== undefined) style.italic = Boolean(opts.italic);
  if (opts.lineSpacing !== undefined) style.lineSpacing = finite(opts.lineSpacing, 'line spacing');
  return style;
}

/** Adds one editable textbox; no autofit or automatic font shrinking. */
export function text(slide, name, value, x, y, w, h, opts = {}) {
  const position = frame(x, y, w, h);
  if (opts.rotation !== undefined) position.rotation = finite(opts.rotation, 'rotation');
  return slide.shapes.add({
    geometry: 'textbox', name,
    position,
    fill: colour(opts.background, 'none'),
    line: { fill: 'none', width: 0, style: 'solid' },
    text: { text: value, style: textStyle(slide, opts) }
  });
}

/** Returns the editable body shape; an optional thin rail is a separate native rect. */
export function box(slide, name, x, y, w, h, opts = {}) {
  const width = finite(opts.strokeWidth ?? opts.lineWidth ?? opts.width ?? 1.5, 'stroke width');
  const radius = finite(opts.radius ?? 0, 'corner radius');
  if (width < 0 || radius < 0) throw new RangeError('Stroke width and radius cannot be negative');
  const cfg = {
    geometry: radius ? 'roundRect' : 'rect', name,
    position: frame(x, y, w, h),
    fill: colour(opts.fill, palette.white),
    line: { fill: width === 0 ? 'none' : colour(opts.stroke ?? opts.color, palette.grid),
      width, style: opts.dash ? 'dashed' : 'solid' }
  };
  if (radius) cfg.borderRadius = radius;
  if (opts.text !== undefined) {
    cfg.text = { text: opts.text, style: textStyle(slide, { ...opts, fill: undefined,
      color: opts.textColor ?? palette.ink, insets: opts.insets ?? 12 }) };
  }
  const shape = slide.shapes.add(cfg);
  const rail = opts.railColor ?? (typeof opts.rail === 'string' ? opts.rail : opts.rail ? palette.teal : undefined);
  if (rail) {
    const railHeight = positive(opts.railHeight ?? 4, 'rail height');
    if (railHeight > h) throw new RangeError('Rail height cannot exceed box height');
    slide.shapes.add({ geometry: 'rect', name: `${name}-rail`,
      position: frame(x, y, w, railHeight), fill: colour(rail),
      line: { fill: 'none', width: 0, style: 'solid' } });
  }
  return shape;
}

const endpoint = value => value?.body ?? value?.shape ?? value;

function segment(slide, name, x1, y1, x2, y2, opts = {}, arrowhead = false) {
  [x1, y1, x2, y2] = [x1, y1, x2, y2].map((v, i) => finite(v, `endpoint ${i}`));
  if (x1 === x2 && y1 === y2) throw new RangeError('A native connector needs a nonzero length');
  const width = positive(opts.width ?? opts.strokeWidth ?? opts.lineWidth ?? 2, 'line width');
  const stroke = { fill: colour(opts.color ?? opts.stroke, palette.ink), width,
    style: opts.lineStyle ?? (typeof opts.dash === 'string' ? opts.dash : opts.dash ? 'dashed' : 'solid') };
  const kind = opts.kind ?? 'straight';
  const head = opts.head ?? { type: 'none' };
  const tail = opts.tail ?? { type: arrowhead ? 'triangle' : 'none', width: 'med', length: 'med' };
  const from = endpoint(opts.from);
  const to = endpoint(opts.to);
  if (from && to) {
    return slide.shapes.connect(from, to, {
      kind, fromSide: opts.fromSide, toSide: opts.toSide,
      fromIdx: opts.fromIdx, toIdx: opts.toIdx, line: stroke, head, tail,
      cap: opts.cap ?? 'flat', join: opts.join ?? 'miter'
    });
  }
  const position = frame(Math.min(x1, x2), Math.min(y1, y2), Math.abs(x2-x1), Math.abs(y2-y1), true);
  position.horizontalFlip = x2 < x1;
  position.verticalFlip = y2 < y1;
  return slide.shapes.add({ geometry: 'connector', name, kind, position,
    from, to, fromIdx: opts.fromIdx, toIdx: opts.toIdx,
    line: stroke, head, tail, cap: opts.cap ?? 'flat', join: opts.join ?? 'miter' });
}

/** Exact endpoint segment; negative directions are represented by native flips. */
export function line(slide, name, x1, y1, x2, y2, opts = {}) {
  return segment(slide, name, x1, y1, x2, y2, opts, false);
}

/** Native source-to-target connector: the triangle belongs on tail, not head. */
export function arrow(slide, name, x1, y1, x2, y2, opts = {}) {
  return segment(slide, name, x1, y1, x2, y2, opts, true);
}

/** Flat panel heading with an optional frame and a thin horizontal separator. */
export function panel(slide, name, title, x, y, w, h, opts = {}) {
  const outer = frame(x, y, w, h);
  const titleHeight = positive(opts.titleHeight ?? 62, 'panel title height');
  const gap = finite(opts.gap ?? 18, 'panel gap');
  if (h <= titleHeight + gap) throw new RangeError('Panel is too short for its heading');
  const body = opts.border || opts.fill ? box(slide, `${name}-frame`, x, y, w, h,
    { fill: opts.fill ?? palette.white, stroke: opts.stroke ?? palette.grid,
      strokeWidth: opts.border ? opts.strokeWidth ?? 1.5 : 0 }) : null;
  const titleShape = text(slide, `${name}-title`, title, x, y, w, titleHeight,
    { ...opts, fill: undefined, color: opts.titleColor ?? opts.color ?? palette.ink,
      fontSize: opts.fontSize ?? opts.size ?? fontPx.panel, bold: opts.bold ?? true,
      verticalAlign: 'middle' });
  const separator = opts.separator === false ? null : line(slide, `${name}-separator`,
    x, y + titleHeight + 4, x + w, y + titleHeight + 4,
    { color: opts.separatorColor ?? palette.grid, width: opts.separatorWidth ?? 1.5 });
  return { title: titleShape, body, separator, frame: outer,
    contentFrame: { left: x, top: y + titleHeight + gap, width: w, height: h-titleHeight-gap } };
}

function chartTextStyle(slide, own = {}, defaultSize = fontPx.axis, opts = {}) {
  return { ...own, typeface: own.typeface ?? own.fontFamily ?? fontFor(slide, opts),
    fontSize: fontSize(slide, own.fontSize, Math.max(defaultSize, langOf(slide, opts) === 'zh' ? 34 : 30), opts),
    fill: own.fill ?? palette.ink };
}

/** Optional native-chart font/style normalization; values and axis domains are untouched. */
export function nativeChartStyle(slide, config = {}, opts = {}) {
  const cfg = { chartFill: palette.white, plotAreaFill: palette.white,
    chartLine: { fill: 'none', width: 0 }, plotAreaLine: { fill: 'none', width: 0 },
    ...config };
  for (const key of ['xAxis', 'yAxis', 'secondaryXAxis', 'secondaryYAxis']) {
    if (key.startsWith('secondary') && !config[key]) continue;
    const own = config[key] ?? {};
    cfg[key] = { ...own, textStyle: chartTextStyle(slide, own.textStyle, opts.axisSize ?? fontPx.axis, opts),
      line: own.line ?? { style: 'solid', fill: palette.muted, width: 1.5 } };
  }
  if (config.title) cfg.titleTextStyle = chartTextStyle(slide, config.titleTextStyle, fontPx.heading, opts);
  else cfg.titlePlacement = 'none';
  if (config.legend || config.hasLegend) cfg.legend = { ...config.legend,
    textStyle: chartTextStyle(slide, config.legend?.textStyle, opts.legendSize ?? fontPx.axis, opts) };
  if (config.dataLabels) cfg.dataLabels = { ...config.dataLabels,
    textStyle: chartTextStyle(slide, config.dataLabels.textStyle, opts.labelSize ?? fontPx.axis, opts) };
  if (config.series) cfg.series = config.series.map(series => ({ ...series,
    ...(series.dataLabels ? { dataLabels: { ...series.dataLabels,
      textStyle: chartTextStyle(slide, series.dataLabels.textStyle, opts.labelSize ?? fontPx.axis, opts) } } : {}),
    ...(series.dataLabelOverrides ? { dataLabelOverrides: series.dataLabelOverrides.map(label => ({ ...label,
      textStyle: chartTextStyle(slide, label.textStyle, opts.labelSize ?? fontPx.axis, opts) })) } : {})
  }));
  return cfg;
}

export function nativeChart(slide, name, type, config = {}, opts = {}) {
  return slide.charts.add(type, { name, ...nativeChartStyle(slide, config, opts) });
}
