/* Select dropdown — progressive enhancement for every <select>.

   The real <select> stays in the DOM (visually hidden) and remains the source of
   truth: Django renders its options, forms submit it, `required` validates it,
   Alpine `x-model` and HTMX (`hx-trigger="change"`) keep working because choosing
   an option sets select.value and dispatches a bubbling `change` event.

   Opt out with <select data-native>. Multi-selects are left alone. */
(function () {
  'use strict';

  var CHECK =
    '<svg class="dd-check" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" ' +
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8.5l3.2 3.2L13 4.8"/></svg>';
  var CHEVRON =
    '<svg class="dd-chevron" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" ' +
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 6l4 4 4-4"/></svg>';

  var uid = 0;
  var openDropdown = null; // { close() } — only one menu open at a time

  function el(tag, className, attrs) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (attrs) Object.keys(attrs).forEach(function (k) { node.setAttribute(k, attrs[k]); });
    return node;
  }

  function enhance(select) {
    if (select.dataset.ddReady || select.multiple || select.size > 1 || select.hasAttribute('data-native')) return;
    select.dataset.ddReady = '1';

    var id = 'dd-' + ++uid;
    var opts = [];
    var seen = {};
    var first = select.options[0];
    // A required field's empty "Choose…" option is a prompt, not a choice you can go back to
    var hidePrompt = select.required && first && first.value === '';
    Array.prototype.forEach.call(select.options, function (o) {
      if (seen[o.value]) return; // identical values are one choice
      seen[o.value] = true;
      if (hidePrompt && o.value === '') return;
      opts.push(o);
    });

    var isField = select.classList.contains('form-select') && !/(^|\s)w-\S+/.test(select.className);
    var widthClass = (select.className.match(/(^|\s)(w-\S+)/) || [])[2];
    var isFilter = !select.required && first && first.value === '';

    var wrap = el('div', 'dd ' + (isField ? 'dd--field' : 'dd--filter'));
    if (widthClass) { wrap.classList.add('dd--fixed', widthClass); }

    var trigger = el('button', 'dd-trigger', {
      type: 'button',
      'aria-haspopup': 'listbox',
      'aria-expanded': 'false',
      'aria-controls': id + '-menu',
      id: id + '-trigger'
    });
    var labelWrap = el('span', 'dd-label-wrap');
    var label = el('span', 'dd-label');
    labelWrap.appendChild(label);
    if (!isField && !widthClass) {
      opts.forEach(function (o) {
        var s = el('span', 'dd-sizer', { 'aria-hidden': 'true' });
        s.textContent = o.text.trim();
        labelWrap.appendChild(s);
      });
    }
    trigger.appendChild(labelWrap);
    trigger.insertAdjacentHTML('beforeend', CHEVRON);

    // Name the button after the select's <label>
    var lab = (select.id && document.querySelector('label[for="' + select.id + '"]')) ||
      (select.parentElement && select.parentElement.querySelector(':scope > label'));
    if (lab) {
      if (!lab.id) lab.id = id + '-label';
      trigger.setAttribute('aria-labelledby', lab.id + ' ' + trigger.id);
    }
    var baseName = !lab && select.getAttribute('aria-label'); // kept in sync with the value below

    var menu = el('div', 'dd-menu', { role: 'listbox', id: id + '-menu', hidden: '' });
    menu.setAttribute('aria-labelledby', trigger.id);
    var buttons = opts.map(function (o) {
      var b = el('button', 'dd-option', { type: 'button', role: 'option', tabindex: '-1' });
      b.dataset.value = o.value;
      var t = el('span');
      t.textContent = o.text.trim();
      b.appendChild(t);
      b.insertAdjacentHTML('beforeend', CHECK);
      if (o.disabled) b.setAttribute('aria-disabled', 'true');
      menu.appendChild(b);
      return b;
    });

    // Mount: wrapper takes the select's place; the select moves inside it
    select.parentNode.insertBefore(wrap, select);
    wrap.appendChild(select);
    wrap.appendChild(trigger);
    wrap.appendChild(menu);
    select.classList.add('dd-native');
    select.tabIndex = -1;
    select.setAttribute('aria-hidden', 'true');

    /* ── state ─────────────────────────────────────────────── */
    function sync() {
      var chosen = select.options[select.selectedIndex];
      var value = chosen ? chosen.value : '';
      label.textContent = chosen ? chosen.text.trim() : '';
      if (baseName) trigger.setAttribute('aria-label', baseName + ': ' + label.textContent);
      buttons.forEach(function (b) {
        b.setAttribute('aria-selected', String(b.dataset.value === value));
      });
      wrap.classList.toggle('is-active', isFilter && value !== '');
      wrap.classList.toggle('is-placeholder', !isFilter && value === '');
      trigger.disabled = select.disabled;
    }

    function isOpen() { return !menu.hidden; }

    // A menu can only paint above later content if every stacking layer between
    // it and the page is above that content. Layout wrappers (e.g. page sections
    // with their own z-index) trap it otherwise, so lift them while it is open.
    var lifted = [];
    function lift() {
      for (var n = wrap.parentElement; n && n !== document.body; n = n.parentElement) {
        var cs = getComputedStyle(n);
        if (cs.position !== 'static' && cs.zIndex !== 'auto') {
          lifted.push({ node: n, inline: n.style.zIndex });
          n.style.zIndex = '60';
        }
      }
    }
    function drop() {
      lifted.forEach(function (l) { l.node.style.zIndex = l.inline; });
      lifted = [];
    }

    function visibleBounds() {
      var top = 0;
      var bottom = window.innerHeight;
      for (var n = wrap.parentElement; n && n !== document.body; n = n.parentElement) {
        var oy = getComputedStyle(n).overflowY;
        if (oy === 'auto' || oy === 'scroll' || oy === 'hidden') {
          var r = n.getBoundingClientRect();
          top = Math.max(top, r.top);
          bottom = Math.min(bottom, r.bottom);
        }
      }
      return { top: top, bottom: bottom };
    }

    function close(returnFocus) {
      if (!isOpen()) return;
      drop();
      menu.hidden = true;
      menu.style.maxHeight = '';
      trigger.setAttribute('aria-expanded', 'false');
      wrap.classList.remove('dd--up', 'dd--right');
      if (openDropdown && openDropdown.menu === menu) openDropdown = null;
      if (returnFocus) trigger.focus();
    }

    function open() {
      if (select.disabled) return;
      if (openDropdown) openDropdown.close();
      sync();
      lift();
      menu.hidden = false;
      trigger.setAttribute('aria-expanded', 'true');
      openDropdown = { menu: menu, close: close };

      // Open toward the roomier side and shrink to fit, measured against the
      // visible area (the nearest scrolling ancestor, clipped to the viewport)
      var t = trigger.getBoundingClientRect();
      var bounds = visibleBounds();
      var gap = 12;
      var below = bounds.bottom - t.bottom - gap;
      var above = t.top - bounds.top - gap;
      menu.style.maxHeight = '';
      var natural = menu.scrollHeight + 2;
      var up = natural > below && above > below;
      wrap.classList.toggle('dd--up', up);
      menu.style.maxHeight = Math.max(120, Math.min(natural, up ? above : below)) + 'px';
      if (menu.getBoundingClientRect().right > window.innerWidth - 8) wrap.classList.add('dd--right');

      var current = buttons.filter(function (b) { return b.getAttribute('aria-selected') === 'true'; })[0] || buttons[0];
      if (current) { current.focus({ preventScroll: true }); current.scrollIntoView({ block: 'nearest' }); }
    }

    function choose(button) {
      var value = button.dataset.value;
      var changed = select.value !== value;
      select.value = value;
      sync();
      close(true);
      if (changed) {
        select.dispatchEvent(new Event('input', { bubbles: true }));
        select.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }

    function move(step) {
      var enabled = buttons.filter(function (b) { return b.getAttribute('aria-disabled') !== 'true'; });
      if (!enabled.length) return;
      var i = enabled.indexOf(document.activeElement);
      var next = i === -1 ? (step > 0 ? 0 : enabled.length - 1) : (i + step + enabled.length) % enabled.length;
      enabled[next].focus();
    }

    // Typeahead: typing letters jumps to the matching option
    var typed = '';
    var typedTimer;
    function typeahead(key) {
      typed += key.toLowerCase();
      clearTimeout(typedTimer);
      typedTimer = setTimeout(function () { typed = ''; }, 600);
      var hit = buttons.filter(function (b) {
        return b.getAttribute('aria-disabled') !== 'true' && b.textContent.trim().toLowerCase().indexOf(typed) === 0;
      })[0];
      if (!hit) return;
      if (isOpen()) hit.focus(); else choose(hit);
    }

    /* ── events ────────────────────────────────────────────── */
    trigger.addEventListener('click', function () { isOpen() ? close() : open(); });
    trigger.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); open(); }
      else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey && e.key !== ' ') typeahead(e.key);
    });
    menu.addEventListener('click', function (e) {
      var b = e.target.closest('.dd-option');
      if (b && b.getAttribute('aria-disabled') !== 'true') choose(b);
    });
    menu.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
      else if (e.key === 'Home') { e.preventDefault(); buttons[0].focus(); }
      else if (e.key === 'End') { e.preventDefault(); buttons[buttons.length - 1].focus(); }
      else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); close(true); }
      else if (e.key === 'Tab') close();
      else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey && e.key !== ' ') typeahead(e.key);
    });
    document.addEventListener('click', function (e) { if (!wrap.contains(e.target)) close(); });

    // Label click / failed `required` validation focus the hidden select → hand focus to the button
    select.addEventListener('focus', function () { trigger.focus(); });
    // Value changed from elsewhere (x-model, form reset)
    select.addEventListener('change', sync);
    if (select.form) select.form.addEventListener('reset', function () { setTimeout(sync, 0); });
    document.addEventListener('alpine:initialized', sync);

    sync();
  }

  function enhanceAll(root) {
    (root || document).querySelectorAll('select').forEach(enhance);
  }

  document.addEventListener('DOMContentLoaded', function () {
    enhanceAll();
    // Pick up selects that arrive later (HTMX swaps, Alpine templates)
    var queued = false;
    new MutationObserver(function () {
      if (queued) return;
      queued = true;
      requestAnimationFrame(function () { queued = false; enhanceAll(); });
    }).observe(document.body, { childList: true, subtree: true });
  });
})();
