(function (root) {
  'use strict';
  // Newest breaking update younger than `hours`, or null.
  function pick(updates, now, hours) {
    const fresh = (updates || []).filter(u => u && /^[a-f0-9]{24}$/.test(u.id || '') && typeof u.title === 'string' &&
      Number.isFinite(u.created_at) && u.created_at <= now && now - u.created_at <= hours * 3600);
    return fresh.sort((a, b) => b.created_at - a.created_at)[0] || null;
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {pick};
  if (!root.document) return;
  const banner = root.document.getElementById('breaking-banner');
  if (!banner) return;
  const hours = Number(banner.dataset.hours) || 3;
  if (!root.document.getElementById('breaking-banner-style')) {
    const style = root.document.createElement('style'); style.id = 'breaking-banner-style';
    style.textContent = '.breaking-banner{display:flex;flex-wrap:wrap;gap:.4rem .8rem;align-items:baseline;background:#b3121f;color:#fff;' +
      'padding:.7rem 1rem;border-radius:.4rem;margin:0 0 1rem}.breaking-banner[hidden]{display:none}' +
      '.breaking-banner strong{letter-spacing:.06em}.breaking-banner a{color:#fff;font-weight:600}.breaking-banner time{opacity:.85;font-size:.9em}';
    root.document.head.append(style);
  }
  async function refresh() {
    try {
      const response = await fetch('short-updates.json', {cache: 'no-store'});
      if (!response.ok) throw new Error('Unavailable');
      const update = pick((await response.json()).updates, Date.now() / 1000, hours);
      if (!update) { banner.hidden = true; return; }
      const label = root.document.createElement('strong'); label.textContent = 'EILMELDUNG';
      const link = root.document.createElement('a'); link.href = 'short-updates.html#update-' + update.id; link.textContent = update.title;
      const time = root.document.createElement('time');
      time.dateTime = new Date(update.created_at * 1000).toISOString();
      time.textContent = new Date(update.created_at * 1000).toLocaleTimeString('de-AT', {hour: '2-digit', minute: '2-digit'}) + ' Uhr';
      banner.replaceChildren(label, link, time); banner.hidden = false;
    } catch { /* Keep the page usable without the banner. */ }
  }
  refresh(); root.setInterval(refresh, 60000);
})(typeof window !== 'undefined' ? window : globalThis);
