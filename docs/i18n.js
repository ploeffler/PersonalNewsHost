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
  function apply() {
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
