/* mdsite theme: dark mode, mobile drawer, copy buttons, scroll-spy, command-palette search */
(function () {
  'use strict';
  var root = document.body.getAttribute('data-root') || '';
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ---- dark mode ---- */
  var themeBtn = $('.theme-btn');
  if (themeBtn) themeBtn.addEventListener('click', function () {
    var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('mdsite-theme', next); } catch (e) {}
  });

  /* ---- top bar gets more solid once the page scrolls ---- */
  var onScroll = function () { document.body.classList.toggle('scrolled', window.scrollY > 8); };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---- mobile navigation drawer ---- */
  var menuBtn = $('.menu-btn');
  if (menuBtn) menuBtn.addEventListener('click', function () { document.body.classList.toggle('nav-open'); });
  var scrim = $('.scrim');
  if (scrim) scrim.addEventListener('click', function () { document.body.classList.remove('nav-open'); });
  var active = $('.sidebar a.active');
  if (active && active.scrollIntoView && !document.body.classList.contains('is-home')) active.scrollIntoView({ block: 'center' });

  /* ---- copy buttons ---- */
  $$('.md .highlight').forEach(function (block) {
    var pre = $('pre', block);
    if (!pre) return;
    var btn = document.createElement('button');
    btn.type = 'button'; btn.className = 'copy-btn'; btn.textContent = 'Copy';
    btn.addEventListener('click', function () {
      var text = pre.innerText;
      var done = function () { btn.textContent = 'Copied'; setTimeout(function () { btn.textContent = 'Copy'; }, 1400); };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { fallback(text); done(); });
      } else { fallback(text); done(); }
    });
    block.appendChild(btn);
  });
  function fallback(text) {
    var ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(ta);
  }

  /* ---- scroll-spy for the table of contents ---- */
  var links = $$('.toc a');
  if (links.length) {
    var map = [];
    links.forEach(function (a) {
      var h = document.getElementById(decodeURIComponent(a.hash.slice(1)));
      if (h) map.push([h, a]);
    });
    var ticking = false;
    var spy = function () {
      ticking = false;
      var cur = map[0];
      for (var i = 0; i < map.length; i++) {
        if (map[i][0].getBoundingClientRect().top <= 120) cur = map[i]; else break;
      }
      links.forEach(function (a) { a.classList.remove('active'); });
      if (cur) cur[1].classList.add('active');
    };
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(spy); }
    }, { passive: true });
    spy();
  }

  /* ---- search (command palette) ---- */
  var cmdk = $('#cmdk'), input = $('#search-input'), box = $('#search-results');
  if (!cmdk || !input || !box) return;
  var index = window.__SEARCH_INDEX__ || [];
  var results = [], sel = -1, opener = null;
  var isMac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);
  $$('.mod-key').forEach(function (el) { el.textContent = isMac ? '⌘' : 'Ctrl'; });

  function esc(s) {
    return s.replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function escRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

  function search(q) {
    var terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) return { terms: terms, hits: [] };
    var hits = [];
    index.forEach(function (d) {
      var t = d.t.toLowerCase(), p = d.p.toLowerCase(), x = d.x.toLowerCase(), score = 0;
      for (var i = 0; i < terms.length; i++) {
        var w = terms[i], s = 0;
        if (t.indexOf(w) >= 0) s += 10;
        if (p.indexOf(w) >= 0) s += 4;
        if (x.indexOf(w) >= 0) s += 1;
        if (!s) return;
        score += s;
      }
      hits.push({ d: d, score: score });
    });
    hits.sort(function (a, b) { return b.score - a.score; });
    return { terms: terms, hits: hits.slice(0, 12) };
  }

  function highlight(text, re) {
    return text.split(re).map(function (part, i) {
      return i % 2 ? '<mark>' + esc(part) + '</mark>' : esc(part);
    }).join('');
  }

  function snippet(d, terms, re) {
    var x = d.x, lx = x.toLowerCase(), pos = -1;
    terms.forEach(function (w) {
      var i = lx.indexOf(w);
      if (i >= 0 && (pos < 0 || i < pos)) pos = i;
    });
    if (pos < 0) pos = 0;
    var start = Math.max(0, pos - 40), end = Math.min(x.length, pos + 120);
    return (start > 0 ? '…' : '') + highlight(x.slice(start, end), re) + (end < x.length ? '…' : '');
  }

  function select(i) {
    var items = $$('.cmdk-item', box);
    if (!items.length) return;
    if (sel >= 0 && items[sel]) items[sel].classList.remove('sel');
    sel = (i + items.length) % items.length;
    items[sel].classList.add('sel');
    items[sel].scrollIntoView({ block: 'nearest' });
  }

  function render() {
    var q = input.value.trim();
    results = []; sel = -1;
    if (!q) { box.innerHTML = '<div class="cmdk-hint">Type to search pages and sections.</div>'; return; }
    var r = search(q);
    results = r.hits;
    if (!results.length) {
      box.innerHTML = '<div class="cmdk-hint">No results for “' + esc(q) + '”. Check the spelling or try fewer words.</div>';
      return;
    }
    var re = new RegExp('(' + r.terms.map(escRe).join('|') + ')', 'gi');
    box.innerHTML = results.map(function (h) {
      var d = h.d, same = d.t === d.p;
      return '<a class="cmdk-item" href="' + esc(root + d.u) + '">' +
        '<div class="r-title">' + highlight(d.t, re) + (same ? '' : '<span class="r-page">in ' + esc(d.p) + '</span>') + '</div>' +
        '<div class="r-snip">' + snippet(d, r.terms, re) + '</div></a>';
    }).join('');
    select(0);
  }

  function openSearch() {
    if (!cmdk.hidden) return;
    opener = document.activeElement;
    document.body.classList.remove('nav-open');
    cmdk.hidden = false;
    document.body.classList.add('modal-open');
    render();
    input.focus(); input.select();
  }
  function closeSearch() {
    if (cmdk.hidden) return;
    cmdk.hidden = true;
    document.body.classList.remove('modal-open');
    if (opener && opener.focus) opener.focus();
  }

  $$('[data-search-open]').forEach(function (b) { b.addEventListener('click', openSearch); });
  $$('[data-search-close]').forEach(function (b) { b.addEventListener('click', closeSearch); });
  input.addEventListener('input', render);
  box.addEventListener('mousemove', function (e) {
    var item = e.target.closest ? e.target.closest('.cmdk-item') : null;
    if (!item) return;
    var items = $$('.cmdk-item', box), i = items.indexOf(item);
    if (i >= 0 && i !== sel) select(i);
  });
  box.addEventListener('click', function () { closeSearch(); });

  document.addEventListener('keydown', function (e) {
    var tag = (document.activeElement && document.activeElement.tagName) || '';
    var typing = /INPUT|TEXTAREA|SELECT/.test(tag) || (document.activeElement && document.activeElement.isContentEditable);
    if (((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') || (e.key === '/' && !typing && cmdk.hidden)) {
      e.preventDefault(); openSearch(); return;
    }
    if (cmdk.hidden) {
      if (e.key === 'Escape') document.body.classList.remove('nav-open');
      return;
    }
    if (e.key === 'Escape') { e.preventDefault(); closeSearch(); }
    else if (e.key === 'ArrowDown') { e.preventDefault(); select(sel + 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); select(sel - 1); }
    else if (e.key === 'Enter' && sel >= 0 && results[sel]) { e.preventDefault(); window.location.href = root + results[sel].d.u; }
    else if (e.key === 'Tab') { e.preventDefault(); input.focus(); }
  });
})();
