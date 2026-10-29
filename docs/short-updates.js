'use strict';
let entries = [];
let rendered = null;
const container = document.getElementById('updates');
function render() {
  const now = Date.now() / 1000;
  const current = entries.filter(u => u.created_at <= now && u.created_at > now - 86400)
    .sort((a, b) => b.created_at - a.created_at).slice(0, 5);
  const signature = JSON.stringify(current);
  if (signature === rendered) return;
  rendered = signature;
  container.replaceChildren();
  if (!current.length) { container.textContent = 'Keine aktuellen Kurzupdates.'; return; }
  for (const u of current) {
    const article = document.createElement('article');
    const title = document.createElement('h2'); title.textContent = u.title;
    const text = document.createElement('p'); text.textContent = u.text || u.title;
    const time = document.createElement('p');
    time.textContent = 'Update: ' + new Date(u.created_at * 1000).toLocaleString('de-AT') +
      ' · Quelle veröffentlicht: ' + new Date(u.published_at * 1000).toLocaleString('de-AT');
    article.append(title, time, text);
    if (/^https?:\/\//i.test(u.url)) {
      const source = document.createElement('a'); source.href = u.url;
      source.textContent = 'Quelle: ' + u.source; source.rel = 'noopener noreferrer'; article.append(source);
    }
    if (/^short-update-video\/[a-f0-9]{24}\.mp4$/.test(u.video || '')) {
      const video = document.createElement('video'); video.controls = true; video.preload = 'none'; video.src = u.video; video.style.width = '100%'; article.append(video);
    } else if (/^short-update-audio\/[a-f0-9]{24}\.wav$/.test(u.audio || '')) {
      const audio = document.createElement('audio'); audio.controls = true; audio.preload = 'none'; audio.src = u.audio; article.append(audio);
    }
    container.append(article);
  }
}
async function refresh() {
  try {
    const response = await fetch('short-updates.json', {cache: 'no-store'});
    if (!response.ok) throw new Error('Unavailable');
    entries = (await response.json()).updates || []; render();
  } catch { if (!entries.length) container.textContent = 'Kurzupdates derzeit nicht verfügbar.'; else render(); }
}
refresh(); setInterval(refresh, 60000); setInterval(render, 30000);
