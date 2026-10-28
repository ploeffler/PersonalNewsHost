/* Researched feed selection. The textarea remains the canonical saved value. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PNHFeedPicker = api;
})(typeof window !== "undefined" ? window : globalThis, function () {
  "use strict";
  const COUNTRIES = {AT:"Österreich", DE:"Deutschland", CH:"Schweiz", GB:"Großbritannien", US:"USA", CA:"Kanada", NZ:"Neuseeland", AU:"Australien", QA:"Katar", FR:"Frankreich", SG:"Singapur", IN:"Indien", JP:"Japan", HK:"Hongkong"};
  const REGIONS = {
    AT:["Burgenland","Kärnten","Niederösterreich","Oberösterreich","Salzburg","Steiermark","Tirol","Vorarlberg","Wien"],
    DE:["Baden-Württemberg","Bayern","Berlin","Brandenburg","Bremen","Hamburg","Hessen","Mecklenburg-Vorpommern","Niedersachsen","Nordrhein-Westfalen","Rheinland-Pfalz","Saarland","Sachsen","Sachsen-Anhalt","Schleswig-Holstein","Thüringen"]
  };
  function publicUrl(raw) {
    try {
      const url = new URL(raw);
      return url.protocol === "https:" && !url.username && !url.password && !/^(localhost|127\.|10\.|192\.168\.)/.test(url.hostname) ? url.href : null;
    } catch { return null; }
  }
  function selections(text) {
    return [...new Set(String(text || "").split(/\r?\n/).map(x => x.trim()).filter(Boolean).map(x => publicUrl(x) || x))];
  }
  function regionOf(entry) {
    if (entry.region) return entry.region;
    let path;
    try { path = new URL(entry.url).pathname; } catch { return "Überregional"; }
    const orf = {burgenland:"Burgenland",kaernten:"Kärnten",noe:"Niederösterreich",ooe:"Oberösterreich",salzburg:"Salzburg",steiermark:"Steiermark",tirol:"Tirol",vorarlberg:"Vorarlberg",wien:"Wien"};
    const match = path.match(/^\/(burgenland|kaernten|noe|ooe|salzburg|steiermark|tirol|vorarlberg|wien)\.xml$/);
    if (new URL(entry.url).hostname === "rss.orf.at" && match) return orf[match[1]];
    if (entry.publisher_country === "AT") {
      if (/\/rss\/steiermark\/?$/.test(path)) return "Steiermark";
      if (/\/rss\/kaernten\/?$/.test(path)) return "Kärnten";
    }
    const de = {badenwuerttemberg:"Baden-Württemberg",bayern:"Bayern",berlin:"Berlin",brandenburg:"Brandenburg",bremen:"Bremen",hamburg:"Hamburg",hessen:"Hessen",mecklenburgvorpommern:"Mecklenburg-Vorpommern",niedersachsen:"Niedersachsen",nordrheinwestfalen:"Nordrhein-Westfalen",rheinlandpfalz:"Rheinland-Pfalz",saarland:"Saarland",sachsen:"Sachsen",sachsenanhalt:"Sachsen-Anhalt",schleswigholstein:"Schleswig-Holstein",thueringen:"Thüringen"};
    const regional = path.match(/\/inland\/regional\/([^/]+)\//);
    return regional && de[regional[1]] || "Überregional";
  }
  function catalogueEntries(data, group) {
    const sets = [[data.feeds,"feed"],[data.mixed_feeds,"mixed"],[data.related_authority_feeds,"related"],[data.non_feed_sources,"web"]];
    const result = [];
    for (const [entries, kind] of sets) {
      for (const entry of Array.isArray(entries) ? entries : []) {
        const url = publicUrl(entry.url);
        if (!url) continue;
        result.push({...entry,url,group,kind,language:entry.language || (group === "authorities" ? "de" : ""),region:regionOf(entry),category:entry.category || (kind === "mixed" ? "Blaulicht gemischt" : kind === "related" ? "Innenressort" : entry.topic || "Allgemein"),blocked:kind === "web" || entry.requires_warning_adapter === true});
      }
    }
    return result;
  }
  function matches(entry, filters, selected) {
    if (filters.group && entry.group !== filters.group) return false;
    if (filters.country && entry.publisher_country !== filters.country) return false;
    if (filters.language && entry.language !== filters.language) return false;
    if (filters.region && !entry.region.split("/").includes(filters.region)) return false;
    if (filters.selected && !selected.has(entry.url)) return false;
    if (!filters.review && entry.status === "review" && !selected.has(entry.url)) return false;
    const haystack = [entry.name,entry.publisher,entry.region,entry.category,COUNTRIES[entry.publisher_country],entry.url,entry.group === "news" ? "Nachrichten" : "Behörden Blaulicht"].join(" ").toLocaleLowerCase("de");
    return !filters.search || haystack.includes(filters.search.toLocaleLowerCase("de"));
  }
  class FeedPicker {
    constructor(document, fetcher) {
      this.document = document;
      this.fetcher = fetcher || window.fetch.bind(window);
      this.catalogues = {};
      this.icons = {};
      this.entries = [];
      this.openGroups = new Set();
      this.knownGroups = new Set();
      this.$ = id => document.getElementById(id);
      this.textarea = this.$("feeds");
      for (const id of ["feed_search","feed_group","feed_country","feed_language","feed_region","feed_selected","feed_review"]) {
        this.$(id).addEventListener(id === "feed_search" ? "input" : "change", () => {
          if (id === "feed_country") this.populateRegions();
          this.render();
        });
      }
      this.textarea.addEventListener("input", () => this.render());
      this.$("feed_reload").addEventListener("click", () => this.load());
      this.render();
    }
    node(tag, text, className) {
      const node = this.document.createElement(tag);
      if (text !== undefined) node.textContent = text;
      if (className) node.className = className;
      return node;
    }
    setSelected(urls) {
      this.textarea.value = selections((urls || []).join("\n")).join("\n");
      this.render();
    }
    populateRegions() {
      const select = this.$("feed_region"), old = select.value;
      select.replaceChildren(this.node("option","Alle Bundesländer / Regionen"));
      select.firstChild.value = "";
      const country = this.$("feed_country").value;
      const names = [...new Set(this.entries.filter(e => !country || e.publisher_country === country).map(e => e.region).concat(country ? REGIONS[country] || [] : []))].sort((a,b) => a.localeCompare(b,"de"));
      for (const name of names) { const option = this.node("option",name); option.value = name; select.append(option); }
      select.value = names.includes(old) ? old : "";
    }
    async load() {
      this.$("feed_reload").disabled = true;
      this.$("feed_load_status").textContent = "Lade recherchierte Quellen …";
      const requests = [["news","feed-catalog.json"],["authorities","police-feed-catalog.json"],["icons","assets/regions/index.json"]];
      const results = await Promise.allSettled(requests.map(async ([key,url]) => {
        const response = await this.fetcher(url,{cache:"no-store"});
        if (!response.ok) throw Error("HTTP " + response.status);
        const data = await response.json();
        if (key !== "icons" && !Array.isArray(data.feeds)) throw Error("Ungültiger Katalog");
        return data;
      }));
      const failures = [];
      results.forEach((result,index) => {
        const key = requests[index][0];
        if (result.status === "fulfilled") {
          if (key === "icons") this.icons = result.value;
          else this.catalogues[key] = result.value;
        } else failures.push(key === "news" ? "Nachrichten" : key === "authorities" ? "Behörden/Blaulicht" : "Wappen");
      });
      const unique = new Map();
      for (const [group,data] of Object.entries(this.catalogues)) for (const entry of catalogueEntries(data,group)) if (!unique.has(entry.url)) unique.set(entry.url,entry);
      this.entries = [...unique.values()];
      const countrySelect = this.$("feed_country"), oldCountry = countrySelect.value;
      countrySelect.replaceChildren(this.node("option","Alle Länder")); countrySelect.firstChild.value = "";
      const countries = [...new Set(this.entries.map(e => e.publisher_country).filter(Boolean))].sort((a,b) => (COUNTRIES[a] || a).localeCompare(COUNTRIES[b] || b,"de"));
      for (const country of countries) { const option = this.node("option",COUNTRIES[country] || country); option.value = country; countrySelect.append(option); }
      countrySelect.value = countries.includes(oldCountry) ? oldCountry : "";
      this.populateRegions(); this.render();
      const dates = Object.entries(this.catalogues).map(([key,data]) => (key === "news" ? "Nachrichten" : "Behörden/Blaulicht") + ": " + (data.researched_on || "ohne Datum"));
      this.$("feed_load_status").textContent = (dates.length ? "Recherchestand " + dates.join(" · ") + ". " : "") + (failures.length ? "Nicht geladen: " + failures.join(", ") + ". Bestehende Auswahl und eigene Adressen bleiben nutzbar." : this.entries.length + " Quellen im Katalog.");
      this.$("feed_reload").disabled = false;
    }
    regionLabel(country, region) {
      const span = this.node("span",undefined,"feed-region-label");
      for (const part of region.split("/")) {
        const asset = this.icons?.[country]?.[part.trim()];
        if (asset && /^assets\/regions\/[a-z0-9-]+\.png$/.test(asset.icon)) {
          const image = this.node("img"); image.src = asset.icon; image.alt = "Wappen " + part.trim(); image.width = 23; image.height = 28; image.loading = "lazy"; span.append(image);
        }
      }
      span.append(this.node("span",region));
      return span;
    }
    row(entry, selected) {
      const checked = selected.has(entry.url);
      const row = this.node("div",undefined,"feed-item" + (checked ? " is-selected" : ""));
      const label = this.node("label",undefined,"feed-choice"), checkbox = this.node("input");
      checkbox.type = "checkbox"; checkbox.dataset.feedUrl = entry.url; checkbox.checked = checked; checkbox.disabled = entry.blocked && !checked;
      checkbox.setAttribute("aria-label",entry.name || entry.publisher || entry.url);
      const content = this.node("span",undefined,"feed-choice-copy");
      content.append(this.node("span",entry.name || entry.publisher || entry.url,"feed-name"));
      const meta = [entry.language === "en" ? "Englisch" : entry.language === "de" ? "Deutsch" : "", entry.category];
      if (entry.kind === "web") meta.push("Web/API · noch nicht als Feed verfügbar");
      else if (entry.blocked) meta.push("Warnquelle · noch nicht für die Sendung verfügbar");
      else if (entry.status === "review") meta.push("Aktualität prüfen");
      else if (entry.kind === "custom") meta.push("Eigene / bisherige Adresse");
      content.append(this.node("small",meta.filter(Boolean).join(" · "),"feed-meta"));
      label.append(checkbox,content); row.append(label);
      if (publicUrl(entry.url)) { const link = this.node("a",entry.kind === "web" ? "Webseite ↗" : "Feed ↗","feed-link"); link.href = entry.url; link.target = "_blank"; link.rel = "noopener noreferrer"; link.setAttribute("aria-label",(entry.name || entry.url) + " öffnen"); row.append(link); }
      checkbox.addEventListener("change", () => {
        const values = selections(this.textarea.value), current = new Set(values);
        if (checkbox.checked && !current.has(entry.url) && current.size >= 30) {
          checkbox.checked = false; this.$("feed_selection_status").textContent = "Maximal 30 Quellen auswählbar. Bitte zuerst eine Quelle abwählen."; return;
        }
        if (checkbox.checked) current.add(entry.url); else current.delete(entry.url);
        this.textarea.value = [...current].join("\n");
        this.textarea.dispatchEvent(new Event("change",{bubbles:true}));
        this.render();
      });
      return row;
    }
    render() {
      const focusedUrl = this.document.activeElement?.dataset?.feedUrl;
      const selected = new Set(selections(this.textarea.value));
      const filters = {search:this.$("feed_search").value.trim(),group:this.$("feed_group").value,country:this.$("feed_country").value,language:this.$("feed_language").value,region:this.$("feed_region").value,selected:this.$("feed_selected").checked,review:this.$("feed_review").checked};
      const known = new Set(this.entries.map(e => e.url));
      const custom = [...selected].filter(url => !known.has(url)).map(url => ({url,name:url,group:"custom",kind:"custom",region:"Eigene Quellen",category:"",blocked:false}));
      const entries = [...custom,...this.entries].filter(e => matches(e,filters,selected));
      const list = this.$("feed_list");
      // Capture disclosure state before replacing the list, including filtered views.
      for (const detail of list.querySelectorAll("details[data-group-key]")) {
        if (detail.open) this.openGroups.add(detail.dataset.groupKey); else this.openGroups.delete(detail.dataset.groupKey);
      }
      list.replaceChildren();
      if (custom.length && !this.$("feed_load_status").textContent) this.$("feed_load_status").textContent = "Die Quellenliste wird geladen. Bisherige Adressen sind bereits auswählbar.";
      const groups = new Map();
      for (const e of entries) { const key = e.group + ":" + (e.publisher_country || "custom"); if (!groups.has(key)) groups.set(key,[]); groups.get(key).push(e); }
      for (const [key,rows] of groups) {
        const first = rows[0], detail = this.node("details",undefined,"feed-group"); detail.dataset.groupKey = key;
        const count = rows.filter(e => selected.has(e.url)).length;
        const summary = this.node("summary");
        summary.append(this.node("span",first.group === "custom" ? "Eigene und bisherige Quellen" : (first.group === "news" ? "Nachrichten" : "Behörden & Blaulicht") + " · " + (COUNTRIES[first.publisher_country] || first.publisher_country)),this.node("span",count + " / " + rows.length,"feed-count"));
        detail.append(summary); detail.open = this.openGroups.has(key) || !this.knownGroups.has(key) && (first.publisher_country === "AT" || first.group === "custom") || Boolean(filters.search || filters.region || filters.selected);
        this.knownGroups.add(key);
        const regions = new Map();
        for (const e of rows) { if (!regions.has(e.region)) regions.set(e.region,[]); regions.get(e.region).push(e); }
        for (const [region,regional] of [...regions].sort(([a],[b]) => a.localeCompare(b,"de"))) {
          const section = this.node("section",undefined,"feed-region");
          const heading = this.node("h4"); heading.append(this.regionLabel(first.publisher_country,region)); section.append(heading);
          regional.sort((a,b) => a.category.localeCompare(b.category,"de") || (a.name || a.url).localeCompare(b.name || b.url,"de"));
          let category = null;
          for (const entry of regional) {
            if (entry.category && entry.category !== category) { section.append(this.node("p",entry.category,"feed-category")); category = entry.category; }
            section.append(this.row(entry,selected));
          }
          detail.append(section);
        }
        list.append(detail);
      }
      if (!entries.length) list.append(this.node("p","Keine Quellen für diese Filter gefunden. Eigene Adressen können unten ergänzt werden.","muted"));
      this.$("feed_selection_status").textContent = selected.size + " von 30 Quellen ausgewählt · " + entries.length + " angezeigt" + (!selected.size ? ". Mindestens eine Quelle ist erforderlich." : selected.size > 30 ? ". Bitte die Auswahl auf 30 Quellen reduzieren." : ".");
      this.$("feed_selection_status").className = selected.size > 30 || !selected.size ? "error" : "muted";
      if (focusedUrl) {
        const next = [...list.querySelectorAll("input[data-feed-url]")].find(input => input.dataset.feedUrl === focusedUrl);
        (next || this.$("feed_search")).focus({preventScroll:true});
      }
    }
  }
  return {FeedPicker,selections,publicUrl,regionOf,catalogueEntries,matches,COUNTRIES,REGIONS};
});
