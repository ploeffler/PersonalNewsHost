/* Shared bilingual UI foundation. No external translation service or costs. */
(function () {
  const dictionaries = {
    de: {settings:"Konfiguration (Beta)",studio:"Browser-Studio (Beta)",feed:"Video-RSS abonnieren",transcript:"Transkript",sources:"Quellen",language:"Sprache",documentation:"Dokumentation"},
    en: {settings:"Settings (Beta)",studio:"Browser Studio (Beta)",feed:"Subscribe to video RSS",transcript:"Transcript",sources:"Sources",language:"Language",documentation:"Documentation"}
  };
  const params = new URLSearchParams(location.search);
  const requested = params.get("lang");
  const saved = localStorage.getItem("pnh-ui-lang");
  const lang = ["de","en"].includes(requested) ? requested : (["de","en"].includes(saved) ? saved : "de");
  localStorage.setItem("pnh-ui-lang", lang);
  document.documentElement.lang = lang;
  const staticEnglish = {
  "PersonalNewsHost konfigurieren": "Configure PersonalNewsHost",
  "← Zur Nachrichtenseite": "← Back to news",
  "GitHub & Speichern": "GitHub & Save",
  "Automatik": "Automation",
  "Sendung": "Broadcast",
  "Stimme & Moderator": "Voice & Presenter",
  "Bilder": "Images",
  "Direkt in GitHub speichern (Beta)": "Save directly to GitHub (Beta)",
  "Wie werden Änderungen aktiv?": "How do changes take effect?",
  "Konfiguration herunterladen": "Download configuration",
  "Direkt auf GitHub speichern": "Save to GitHub",
  "Neu laden": "Reload",
  "config.json vom Computer importieren": "Import config.json from computer",
  "Produktionsversion": "Production version",
  "Welche Version soll verwendet werden?": "Which version should be used?",
  "Version 2.0 vorbereiten": "Prepare version 2.0",
  "1. Rechenstandort": "1. Processing location",
  "2. Dienste": "2. Services",
  "3. Standortnachweis": "3. Location evidence",
  "4. Kostenobergrenzen": "4. Spending limits",
  "Kontinent / Datenraum": "Continent / data region",
  "Land der Verarbeitung": "Processing country",
  "KI-Nachrichtenaufbereitung": "AI news processing",
  "Sprachausgabe": "Speech synthesis",
  "Moderator / Avatar": "Presenter / Avatar",
  "Videoproduktion": "Video production",
  "3. Standortnachweis je Anbieter": "3. Provider location evidence",
  "Fehlende Nachweise pro Anbieter": "Missing evidence by provider",
  "Verarbeitungsraum": "Processing region",
  "Land": "Country",
  "Dienst": "Service",
  "Nachweisstatus": "Evidence status",
  "Prüfdaten aktualisieren": "Refresh verification data",
  "Dokumentierte EU-Verarbeitungsoptionen (Recherche)": "Documented EU processing options (research)",
  "Maximalbetrag pro Sendung (EUR)": "Maximum cost per broadcast (EUR)",
  "Monatliches Limit (EUR)": "Monthly limit (EUR)",
  "← Zurück": "← Back",
  "Weiter →": "Next →",
  "Automatische Nachrichtensendungen": "Automatic news broadcasts",
  "Wie oft soll eine Sendung erzeugt werden?": "How often should a broadcast be generated?",
  "Zeitzone": "Time zone",
  "Startstunde (Ortszeit)": "Start hour (local time)",
  "Jetzt Nachrichtensendung erzeugen": "Generate news broadcast now",
  "Wochentage": "Weekdays",
  "Sendungstitel": "Broadcast title",
  "RSS-Feeds (eine HTTPS-Adresse pro Zeile)": "RSS feeds (one HTTPS URL per line)",
  "Anzahl Meldungen (1–10)": "Number of stories (1–10)",
  "Nachrichtenstil": "News style",
  "RSS-Medien in der Sendung": "RSS media in broadcast",
  "Maximale Beschreibungssätze im klassischen Stil (1–4)": "Maximum description sentences in classic style (1–4)",
  "Maximale Beschreibungslänge (0–300 Zeichen)": "Maximum description length (0–300 characters)",
  "Stimme und Moderation": "Voice and presentation",
  "Sprachengine": "Speech engine",
  "Piper-Sprechtempo (0,7–1,5; kleiner = schneller)": "Piper speech speed (0.7–1.5; lower = faster)",
  "Stimmlage in Halbtönen (−6 bis +6; negativ = tiefer)": "Pitch in semitones (−6 to +6; negative = lower)",
  "Name des Moderators": "Presenter name",
  "Portraitpfad im Repository": "Portrait path in repository",
  "Hintergrundpfad im Repository": "Background path in repository",
  "Intro und Outro – Darstellung und Sprechertext": "Intro and outro – visuals and spoken text",
  "Intro: Avatar oder einfärbiger Hintergrund / Bild": "Intro: avatar or solid background / image",
  "Intro-Darstellung": "Intro appearance",
  "Intro ohne Avatar – Hintergrund auswählen": "Intro without avatar – select background",
  "Hintergrundart": "Background type",
  "Hintergrundfarbe": "Background color",
  "Bildpfad im Repository (bei Bilddatei)": "Image path in repository (for image file)",
  "Intro-Sprechertext": "Intro narration text",
  "Outro-Sprechertext": "Outro narration text",
  "Telegram-Veröffentlichung (optional)": "Telegram publishing (optional)",
  "Empfängerart": "Recipient type",
  "Versandart": "Delivery mode",
  "Telegram-Nachricht (Platzhalter: {title}, {url})": "Telegram message (placeholders: {title}, {url})",
  "Eigene Bilder hochladen (Beta)": "Upload your images (Beta)",
  "Moderator-Porträt": "Presenter portrait",
  "Studiohintergrund": "Studio background",
  "Ausgewählte Bilder auf GitHub hochladen": "Upload selected images to GitHub",
  "GitHub Fine-grained Token (nur für direkten Speichervorgang)": "GitHub fine-grained token (for direct saving only)"
};
  function translateStaticText(root) {
    if (lang !== "en") return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      const parent = node.parentElement;
      if (!parent || parent.closest("script,style,textarea,option,code,pre")) continue;
      const original = node.nodeValue;
      const trimmed = original.trim();
      if (Object.prototype.hasOwnProperty.call(staticEnglish, trimmed)) {
        node.nodeValue = original.replace(trimmed, staticEnglish[trimmed]);
      }
    }
  }
  function apply() {\n    translateStaticText(document.body);
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      if (dictionaries[lang][key]) el.textContent = dictionaries[lang][key];
    });
    const holder = document.getElementById("pnh-language-switch");
    if (!holder) return;
    holder.innerHTML = "";
    const label = document.createElement("label");
    label.textContent = dictionaries[lang].language + ": ";
    const select = document.createElement("select");
    select.setAttribute("aria-label", dictionaries[lang].language);
    for (const code of ["de","en"]) {
      const option = document.createElement("option");
      option.value = code; option.textContent = code.toUpperCase(); option.selected = code === lang;
      select.appendChild(option);
    }
    select.addEventListener("change", () => {
      localStorage.setItem("pnh-ui-lang", select.value);
      const url = new URL(location.href);
      url.searchParams.set("lang", select.value);
      location.assign(url.href);
    });
    label.appendChild(select); holder.appendChild(label);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", apply);
  else apply();
  window.PersonalNewsHostI18n = {lang, dictionaries};
})();
