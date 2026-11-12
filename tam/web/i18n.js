/* ============================================================================
 * i18n + theme runtime for the TAO web console.
 *
 * Source language of the UI is Simplified Chinese. Translations live in
 * window.__TAM_I18N__ (generated into i18n.data.js by tools/i18n_build.py).
 *
 * Translation happens at the DOM level, so app.js stays untouched:
 *   - text nodes            -> dictionary lookup (exact, then %s patterns)
 *   - attributes            -> placeholder / title / alt / aria-label / value
 *   - every mutation        -> re-translated through a MutationObserver
 * Originals are remembered, so switching language re-translates instead of
 * translating a translation.
 * ==========================================================================*/
(function () {
  'use strict';

  var LANG_KEY = 'tam.lang';
  var THEME_KEY = 'tam.theme';
  var ZH = /[\u4e00-\u9fff]/;
  var ATTRS = ['placeholder', 'title', 'alt', 'aria-label'];

  var DATA = window.__TAM_I18N__ || { ru: {}, en: {}, pat: { ru: [], en: [] } };
  var DICT = { ru: DATA.ru || {}, en: DATA.en || {} };
  var PATS = { ru: [], en: [] };

  // "已保存 %s 项。" -> /^已保存 (.+?) 项。$/  (greedy-safe, non-greedy captures)
  function compile(pats) {
    return (pats || []).map(function (p) {
      var src = p[0], dst = p[1];
      var re = '^' + src.split('%s').map(function (chunk) {
        return chunk.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      }).join('([\\s\\S]+?)') + '$';
      return { re: new RegExp(re), dst: dst };
    });
  }
  // более длинный шаблон = более конкретный, его пробуем первым
  function compileSorted(pats) {
    return compile((pats || []).slice().sort(function (a, b) { return b[0].length - a[0].length; }));
  }
  PATS.ru = compileSorted(DATA.pat && DATA.pat.ru);
  PATS.en = compileSorted(DATA.pat && DATA.pat.en);

  var LANG = 'ru';
  try {
    var savedLang = localStorage.getItem(LANG_KEY);
    if (savedLang === 'ru' || savedLang === 'en') LANG = savedLang;
  } catch (e) { /* private mode */ }

  function norm(s) { return String(s).replace(/\s+/g, ' ').trim(); }

  /* Translate one bare string (no surrounding whitespace).
     Order: exact -> %s pattern -> "a · b · c" segments.
     Captured groups are translated recursively, so "5 分钟后" resolves through
     "%s 分钟后" -> "%s 分钟" -> "5 мин". */
  var PUNCT = { "\u3001": ", ", "\u3002": ".", "\uff0c": ", ", "\uff1a": ": ",
                "\uff1b": "; ", "\uff01": "!", "\uff1f": "?", "\uff08": " (",
                "\uff09": ")", "\u300c": "\u00ab", "\u300d": "\u00bb",
                "\u3010": " [", "\u3011": "]" };
  var PUNCT_ONLY = /^[\u3001\u3002\uff0c\uff1a\uff1b\uff01\uff1f\uff08\uff09\u300c\u300d\u3010\u3011]+$/;

  function tr(s, depth) {
    depth = depth || 0;
    if (!s) return s;
    if (PUNCT_ONLY.test(s)) {
      var out = "";
      for (var pi = 0; pi < s.length; pi++) out += PUNCT[s[pi]] || s[pi];
      return out;
    }
    if (!ZH.test(s) || depth > 4) return s;
    var dict = DICT[LANG] || {};
    var hit = dict[s];
    if (hit == null) hit = dict[norm(s)];
    if (hit != null) return hit;
    var list = PATS[LANG] || [];
    for (var i = 0; i < list.length; i++) {
      var m = list[i].re.exec(s);
      if (!m) continue;
      var k = 0;
      return list[i].dst.replace(/%s/g, function () {
        k++;
        var cap = m[k];
        return cap == null ? '' : tr(cap, depth + 1);
      });
    }
    if (s.indexOf(' · ') >= 0) {
      var parts = s.split(' · ');
      var changed = false;
      var mapped = parts.map(function (p) {
        var t = tr(p, depth + 1);
        if (t !== p) changed = true;
        return t;
      });
      if (changed) return mapped.join(' · ');
    }
    return s;
  }

  /* Translate keeping leading/trailing whitespace of the original. */
  function trPad(raw) {
    var m = /^(\s*)([\s\S]*?)(\s*)$/.exec(raw);
    if (!m || !m[2]) return raw;
    var out = tr(m[2]);
    return out === m[2] ? raw : m[1] + out + m[3];
  }

  /* Multi-line blocks (logs, <pre>) are translated line by line: the app builds
     them by concatenation, so each line is an independent sentence. */
  function trBlock(raw) {
    var whole = trPad(raw);
    if (whole !== raw) return whole;          // целый абзац нашёлся в словаре
    if (raw.indexOf('\n') < 0) return raw;
    // иначе — построчно (логи/сводки склеены из отдельных фраз)
    return raw.split('\n').map(function (line) { return trPad(line); }).join('\n');
  }

  /* Китайский не ставит пробелы вокруг <strong>/<code>, русский и английский —
     ставят. Поэтому на границе текстового узла с инлайн-элементом пробел
     добавляется, если с обеих сторон стоят буквы/цифры. */
  var INLINE = { STRONG: 1, EM: 1, B: 1, I: 1, CODE: 1, SPAN: 1, A: 1, SMALL: 1,
                 S: 1, U: 1, MARK: 1, SUP: 1, SUB: 1, LABEL: 1, ABBR: 1 };
  var WORD = /[0-9A-Za-z\u0400-\u04FF\u2014\u2013]/;  // буквы/цифры и тире

  function edgeText(node, dir) {
    var cur = node;
    while (cur) {
      var sib = dir === 'prev' ? cur.previousSibling : cur.nextSibling;
      while (sib) {
        var v = sib.nodeType === 3 ? sib.nodeValue : (sib.nodeType === 1 ? sib.textContent : '');
        if (v && v.trim()) return dir === 'prev' ? v.trim().slice(-1) : v.trim().charAt(0);
        sib = dir === 'prev' ? sib.previousSibling : sib.nextSibling;
      }
      var par = cur.parentNode;
      if (!par || par.nodeType !== 1 || par === document.body) return '';
      if (!INLINE[par.tagName]) return '';   // блочная граница — пробел не нужен
      cur = par;
    }
    return '';
  }

  var TEXT_ORIG = new WeakMap();  // textNode -> {orig, out}
  var ATTR_ORIG = new WeakMap();  // element  -> {name: {orig, out}}

  function doTextNode(node) {
    var cur = node.nodeValue;
    if (cur == null) return;
    var rec = TEXT_ORIG.get(node);
    if (!rec || rec.out !== cur) {          // fresh content: remember it as source
      rec = { orig: cur, out: cur };
      TEXT_ORIG.set(node, rec);
    }
    if (!ZH.test(rec.orig) && !PUNCT_ONLY.test(rec.orig.trim())) return;
    var next = trBlock(rec.orig);
    if (next !== cur) {
      var m = /^(\s*)([\s\S]*?)(\s*)$/.exec(next);
      var body = m[2];
      if (body && !ZH.test(body)) {
        if (WORD.test(edgeText(node, 'prev')) &&
            (WORD.test(body.charAt(0)) || /[(\u00ab\u201c]/.test(body.charAt(0)))) body = ' ' + body;
        if (WORD.test(edgeText(node, 'next')) && WORD.test(body.slice(-1))) body = body + ' ';
      }
      next = m[1] + body + m[3];
    }
    rec.out = next;
    if (next !== cur) node.nodeValue = next;
  }

  function doAttr(el, name) {
    var v = el.getAttribute(name);
    if (v == null) return;
    var bag = ATTR_ORIG.get(el);
    if (!bag) { bag = {}; ATTR_ORIG.set(el, bag); }
    var rec = bag[name];
    if (!rec || rec.out !== v) { rec = { orig: v, out: v }; bag[name] = rec; }
    if (!ZH.test(rec.orig) && !PUNCT_ONLY.test(rec.orig.trim())) return;
    var next = trPad(rec.orig);
    rec.out = next;
    if (next !== v) el.setAttribute(name, next);
  }

  var SKIP_TAGS = { SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, SVG: 1 };
  var NO_TEXT_TAGS = { TEXTAREA: 1 };  // атрибуты переводим, содержимое — нет

  function walk(root) {
    if (!root) return;
    if (root.nodeType === 3) { doTextNode(root); return; }
    if (root.nodeType !== 1) return;
    var tag = root.tagName;
    if (SKIP_TAGS[tag]) return;
    for (var i = 0; i < ATTRS.length; i++) doAttr(root, ATTRS[i]);
    if (tag === 'INPUT' && (root.type === 'button' || root.type === 'submit')) doAttr(root, 'value');
    if (NO_TEXT_TAGS[tag]) return;
    var kids = root.childNodes;
    for (var j = 0; j < kids.length; j++) walk(kids[j]);
  }

  var pending = new Set();
  var scheduled = false;
  function flush() {
    scheduled = false;
    var nodes = Array.from(pending);
    pending.clear();
    for (var i = 0; i < nodes.length; i++) walk(nodes[i]);
  }
  function schedule(node) {
    pending.add(node);
    if (scheduled) return;
    scheduled = true;
    (window.requestAnimationFrame || window.setTimeout)(flush, 0);
  }

  var observer = null;
  function startObserver() {
    if (observer || !window.MutationObserver) return;
    observer = new MutationObserver(function (muts) {
      for (var i = 0; i < muts.length; i++) {
        var m = muts[i];
        if (m.type === 'childList') {
          for (var j = 0; j < m.addedNodes.length; j++) schedule(m.addedNodes[j]);
        } else if (m.type === 'characterData') {
          schedule(m.target);
        } else if (m.type === 'attributes') {
          schedule(m.target);
        }
      }
    });
    observer.observe(document.documentElement, {
      childList: true, subtree: true, characterData: true,
      attributes: true, attributeFilter: ATTRS.concat(['value'])
    });
  }

  function title() {
    var t = document.documentElement.getAttribute('data-title-' + LANG);
    if (t) document.title = t;
  }

  function applyAll() {
    walk(document.body);
    title();
    // после перевода подписи меняют ширину — просим приложение пересчитать
    // «бегунок» навигации и отступы (иначе подсветка съезжает на соседний пункт)
    try {
      if (typeof TAO_FX !== 'undefined' && TAO_FX && typeof TAO_FX.syncNav === 'function') TAO_FX.syncNav();
    } catch (e) { /* ignore */ }
  }

  function setLang(lang, silent) {
    if (lang !== 'ru' && lang !== 'en') return;
    LANG = lang;
    try { localStorage.setItem(LANG_KEY, lang); } catch (e) {}
    document.documentElement.setAttribute('lang', lang === 'ru' ? 'ru' : 'en');
    document.documentElement.setAttribute('data-lang', lang);
    applyAll();
    var sel = document.getElementById('langSel');
    if (sel && sel.value !== lang) sel.value = lang;
    if (!silent) {
      document.dispatchEvent(new CustomEvent('tam:lang', { detail: { lang: lang } }));
    }
  }

  /* ---------------- boot ---------------- */
  function boot() {
    document.documentElement.setAttribute('lang', LANG === 'ru' ? 'ru' : 'en');
    document.documentElement.setAttribute('data-lang', LANG);
    var sel = document.getElementById('langSel');
    if (sel) { sel.value = LANG; sel.addEventListener('change', function () { setLang(sel.value); }); }
    applyAll();
    startObserver();
    // поздние рендеры (асинхронные панели) тоже попадают под перевод
    setTimeout(applyAll, 60);
    setTimeout(applyAll, 400);
  }

  window.tamI18n = {
    t: tr, apply: applyAll, setLang: setLang, getLang: function () { return LANG; },
    has: function (s) { return !!(DICT[LANG] || {})[s]; }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
