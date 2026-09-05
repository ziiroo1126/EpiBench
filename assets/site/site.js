'use strict';

// Keep navigation useful even when JavaScript is unavailable.
const links = [...document.querySelectorAll('.contents a')];
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => {
    const visible = entries.filter(entry => entry.isIntersecting);
    if (!visible.length) return;
    const active = visible.sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0].target.id;
    links.forEach(link => {
      if (link.hash === `#${active}`) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  }, { rootMargin: '-8% 0px -65% 0px', threshold: 0 });
  document.querySelectorAll('main section').forEach(section => observer.observe(section));
}

document.querySelectorAll('[data-copy]').forEach(button => {
  button.hidden = false;
  button.addEventListener('click', async () => {
    const source = document.getElementById(button.dataset.copy);
    const status = document.getElementById('copy-status');
    const original = button.textContent;
    try {
      if (!navigator.clipboard) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(source.textContent);
      button.textContent = 'Copied!';
      status.textContent = `${original === 'Copy BibTeX' ? 'Citation' : 'Code'} copied to clipboard.`;
    } catch {
      const range = document.createRange();
      range.selectNodeContents(source);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      button.textContent = 'Text selected';
      status.textContent = 'Text selected. Use your browser’s Copy command to copy it.';
    }
    window.setTimeout(() => { button.textContent = original; }, 2500);
  });
});

const dialog = document.getElementById('figure-dialog');
const expanded = document.getElementById('expanded-figure');
if (typeof dialog.showModal === 'function') {
  document.querySelectorAll('a.zoomable').forEach(link => {
    link.addEventListener('click', event => {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      expanded.src = link.href;
      expanded.alt = link.querySelector('img').alt;
      dialog.showModal();
    });
  });
  document.getElementById('close-figure').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
  });
}
