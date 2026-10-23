#!/usr/bin/env python3
"""Zero-cost RSS -> narrated static-image video -> podcast-style video RSS."""
import datetime as dt
import email.utils
import html
import json
import re
import subprocess
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
BASE = "https://ploeffler.github.io/PersonalNewsHost/"
UA = "PersonalNewsHost/0.4-scenes (RSS news reader)"
ATOM = "{http://www.w3.org/2005/Atom}"

GERMAN_MONTHS = ("Jänner", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember")
GERMAN_ORDINALS = ("", "ersten", "zweiten", "dritten", "vierten", "fünften", "sechsten", "siebten", "achten", "neunten", "zehnten", "elften", "zwölften", "dreizehnten", "vierzehnten", "fünfzehnten", "sechzehnten", "siebzehnten", "achtzehnten", "neunzehnten")

def german_number(n):
    """German spoken cardinal numbers, suitable for dates and clock times."""
    n = int(n)
    units = ("null", "eins", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun", "zehn", "elf", "zwölf", "dreizehn", "vierzehn", "fünfzehn", "sechzehn", "siebzehn", "achtzehn", "neunzehn")
    if n < 20:
        return units[n]
    if n < 100:
        tens = ("", "", "zwanzig", "dreißig", "vierzig", "fünfzig", "sechzig", "siebzig", "achtzig", "neunzig")
        return tens[n // 10] if n % 10 == 0 else ("ein" if n % 10 == 1 else units[n % 10]) + "und" + tens[n // 10]
    if n < 1000:
        return ("ein" if n // 100 == 1 else units[n // 100]) + "hundert" + (german_number(n % 100) if n % 100 else "")
    if n < 10000:
        return ("ein" if n // 1000 == 1 else german_number(n // 1000)) + "tausend" + (german_number(n % 1000) if n % 1000 else "")
    raise ValueError("Number outside supported spoken date range")

def spoken_timestamp(local):
    """Write the German date and time as words for offline speech synthesis."""
    day = local.day
    ordinal = GERMAN_ORDINALS[day] if day < 20 else german_number(day) + "sten"
    # 20th and 30th are irregular: zwanzigsten, dreißigsten.
    if day in (20, 30):
        ordinal = german_number(day) + "sten"
    elif day > 20:
        ordinal = german_number(day) + "sten"
    year = german_number(local.year)
    hours = german_number(local.hour)
    if local.minute == 0:
        clock = hours + " Uhr"
    else:
        clock = hours + " Uhr " + german_number(local.minute)
    return f"Heute ist der {ordinal[:-1]} {GERMAN_MONTHS[local.month - 1]}. Es ist {clock}. Nachrichten aus dem Jahr {year}."

def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()

def fetch(url):
    if not url.startswith(("https://", "http://")):
        raise ValueError("Only HTTP(S) RSS URLs allowed")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=12) as resp:
        return resp.read(1_500_000)

MEDIA_NS = "{http://search.yahoo.com/mrss/}"

def media_candidates(node):
    """Return image/video URLs explicitly attached to a feed entry."""
    found = []
    def add(url, kind):
        if url:
            found.append((url, kind))
    for tag in ("enclosure", MEDIA_NS + "content", MEDIA_NS + "thumbnail"):
        for el in node.findall(tag):
            url = el.get("url", "")
            mime = el.get("type", "").lower()
            medium = el.get("medium", "").lower()
            kind = "video" if mime.startswith("video/") or medium == "video" else "image" if mime.startswith("image/") or medium == "image" or tag.endswith("thumbnail") else None
            if kind:
                add(url, kind)
    raw = node.findtext("description") or node.findtext(ATOM + "content") or node.findtext(ATOM + "summary") or ""
    for tag, kind in (("img", "image"), ("video", "video"), ("source", "video")):
        for match in re.finditer(r"<" + tag + r"\b[^>]*?\bsrc\s*=\s*['\"]([^'\"]+)", raw, re.I):
            add(html.unescape(match.group(1)), kind)
    return found

def download_media(candidates, mode, directory, index, max_bytes):
    """Download only directly linked, small media files; reject non-media responses."""
    from urllib.parse import urlparse
    if mode == "off":
        return None
    allowed = {"image"} if mode == "images" else {"image", "video"}
    for url, kind in candidates:
        if kind not in allowed:
            continue
        parsed = urlparse(url)
        if parsed.scheme not in ("https", "http") or not parsed.hostname:
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/*,video/*"})
            with urllib.request.urlopen(req, timeout=12) as response:
                mime = response.headers.get_content_type()
                if not mime.startswith(kind + "/"):
                    continue
                if int(response.headers.get("Content-Length", "0")) > max_bytes:
                    continue
                path = directory / f"rss_media_{index}.{ 'mp4' if kind == 'video' else 'img' }"
                with path.open("wb") as output:
                    size = 0
                    while True:
                        chunk = response.read(65536)
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > max_bytes:
                            raise ValueError("RSS media too large")
                        output.write(chunk)
            subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=12)
            return (path, kind)
        except Exception as exc:
            print(f"RSS media skipped: {type(exc).__name__}: {exc}")
    return None

def article_image_candidates(url):
    """Read publisher's article image metadata without paid services."""
    from html.parser import HTMLParser
    from urllib.parse import urljoin, urlparse

    class ArticleImages(HTMLParser):
        def __init__(self):
            super().__init__()
            self.images = []
        def handle_starttag(self, tag, attrs):
            if tag.lower() != "meta":
                return
            values = dict((k.lower(), v or "") for k, v in attrs)
            key = (values.get("property") or values.get("name") or "").lower()
            if key in ("og:image", "og:image:url", "twitter:image", "twitter:image:src"):
                candidate = urljoin(url, html.unescape(values.get("content", "")))
                if urlparse(candidate).scheme in ("https", "http"):
                    self.images.append((candidate, "image"))

    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
        with urllib.request.urlopen(req, timeout=8) as response:
            if "html" not in response.headers.get_content_type():
                return []
            body = response.read(500_000).decode("utf-8", errors="replace")
        parser = ArticleImages()
        parser.feed(body)
        return list(dict.fromkeys(parser.images))
    except Exception as exc:
        print(f"Article image metadata unavailable: {type(exc).__name__}: {exc}")
        return []


def improve_news_image(path, settings):
    """Offline CPU neural upscaling with FSRCNN x2; conservative fallback."""
    from PIL import Image, ImageEnhance, ImageOps
    mode = settings.get("enhancement", "ai")
    if mode == "off":
        return path, "original"
    try:
        with Image.open(path) as src:
            image = ImageOps.exif_transpose(src).convert("RGB")
            width, height = image.size
            if width < 64 or height < 64:
                return path, "original"
            if mode == "ai":
                model = ROOT / "models" / "FSRCNN_x2.pb"
                if model.is_file() and model.stat().st_size > 1000:
                    try:
                        import cv2
                        import numpy as np
                        # Keep CPU processing bounded on GitHub's free runners.
                        if max(image.size) > 1100:
                            image = ImageOps.contain(image, (1100, 1100),
                                                     method=Image.Resampling.LANCZOS)
                        network = cv2.dnn_superres.DnnSuperResImpl_create()
                        network.readModel(str(model))
                        network.setModel("fsrcnn", 2)
                        rgb = np.asarray(image)
                        enhanced = network.upsample(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
                        output = path.with_name(path.stem + "_ai.png")
                        Image.fromarray(cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)).save(output)
                        print(f"Neural FSRCNN x2 enhancement: {path.name}")
                        return output, "neural_fsrcnn_x2"
                    except Exception as exc:
                        print(f"Neural image enhancement fallback: {type(exc).__name__}: {exc}")
                else:
                    print("FSRCNN model unavailable; using conservative enhancement")
            factor = min(2.0, 1100 / min(width, height))
            if factor > 1.05:
                image = image.resize((round(width * factor), round(height * factor)),
                                     Image.Resampling.LANCZOS)
            image = ImageEnhance.Contrast(image).enhance(1.045)
            image = ImageEnhance.Sharpness(image).enhance(1.12)
            output = path.with_name(path.stem + "_enhanced.png")
            image.save(output, optimize=True)
            return output, "conservative"
    except Exception as exc:
        print(f"Image enhancement skipped: {type(exc).__name__}: {exc}")
        return path, "original"


def search_commons_image(title):
    """Find a conservatively matched, public-domain/CC0 illustrative photo."""
    from urllib.parse import urlencode
    words = re.findall(r"[^\\W_]{4,}", title, flags=re.UNICODE)
    stop = {"diese", "einer", "einem", "einen", "wegen", "heute", "nach", "über", "gegen", "mehr", "beim", "durch", "sowie", "neuen", "neuer", "nicht", "wird", "sind"}
    terms = [w for w in words if w.casefold() not in stop][:5]
    if len(terms) < 2:
        return None
    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": " ".join(terms), "gsrnamespace": "6", "gsrlimit": "8",
        "prop": "imageinfo", "iiprop": "url|extmetadata|mime",
        "iiurlwidth": "1280"
    }
    api = "https://commons.wikimedia.org/w/api.php?" + urlencode(params)
    try:
        req = urllib.request.Request(api, headers={"User-Agent": UA + " (free-image fallback)"})
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read(350_000))
        pages = result.get("query", {}).get("pages", {})
        for page in pages.values():
            filename = page.get("title", "").casefold()
            matched = sum(1 for word in terms if word.casefold() in filename)
            if matched < 2:
                continue
            info = (page.get("imageinfo") or [{}])[0]
            license_name = info.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "").lower()
            if not (license_name == "cc0" or "public domain" in license_name or license_name.startswith("pd-")):
                continue
            if not info.get("mime", "").startswith("image/"):
                continue
            image_url = info.get("thumburl") or info.get("url")
            if image_url and image_url.startswith("https://"):
                return image_url, page.get("title", ""), info.get("descriptionurl", "")
    except Exception as exc:
        print(f"Commons image search unavailable: {exc}")
    return None

def items_from_feed(url):
    root = ET.fromstring(fetch(url))
    result = []
    for node in root.findall(".//item")[:15]:
        title = clean(node.findtext("title"))
        desc = clean(node.findtext("description"))
        link = clean(node.findtext("link"))
        if title:
            result.append((title, desc, link, media_candidates(node)))
    if not result:
        for node in root.findall(".//" + ATOM + "entry")[:15]:
            title = clean(node.findtext(ATOM + "title"))
            summary = clean(node.findtext(ATOM + "summary") or node.findtext(ATOM + "content"))
            link_node = node.find(ATOM + "link")
            link = link_node.get("href", "") if link_node is not None else ""
            if title:
                result.append((title, summary, link, media_candidates(node)))
    return result

def run(args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, timeout=480)

def adjust_voice_pitch(wav):
    """Lower or raise voice pitch with FFmpeg while preserving speech duration."""
    import math
    import wave
    semitones = float(CONFIG.get("voice_pitch_semitones", 0))
    if not math.isfinite(semitones) or not -6 <= semitones <= 6:
        raise ValueError("voice_pitch_semitones must be between -6 and 6")
    if abs(semitones) < 0.01:
        return
    with wave.open(str(wav), "rb") as audio:
        rate = audio.getframerate()
    factor = 2 ** (semitones / 12)
    target = Path(wav).with_name(Path(wav).stem + "-pitch.wav")
    try:
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
            "-af", f"asetrate={rate}*{factor:.8f},aresample={rate},atempo={1/factor:.8f}",
            "-ar", str(rate), "-c:a", "pcm_s16le", str(target)
        ], check=True)
        target.replace(wav)
        print(f"Voice pitch adjusted: {semitones:+.1f} semitones (tempo preserved)")
    finally:
        target.unlink(missing_ok=True)

def synthesize(script, wav):
    """Use local Piper neural TTS if available; retain eSpeak as safe fallback."""
    import os
    model = ROOT / "models" / "de_DE-thorsten-high.onnx"
    engine = CONFIG.get("tts_engine", "piper")
    if engine not in ("piper", "espeak"):
        raise ValueError("Unsupported tts_engine")
    if engine == "piper" and model.is_file():
        try:
            subprocess.run(
                ["piper", "--model", str(model), "--length_scale", str(CONFIG.get("piper_length_scale", 1.13)), "--sentence_silence", "0.38", "--output_file", str(wav)],
                input=script, text=True, check=True, timeout=180,
                stdout=subprocess.DEVNULL
            )
            if wav.is_file() and wav.stat().st_size > 44:
                print("Speech engine: Piper (de_DE-thorsten-high)")
                adjust_voice_pitch(wav)
                return
        except (OSError, subprocess.SubprocessError) as exc:
            print(f"Piper failed; falling back to eSpeak-NG: {exc}")
    run(["espeak-ng", "-v", CONFIG.get("voice", "de"), "-s", "145", "-w", str(wav), script])
    print("Speech engine: eSpeak-NG fallback")
    adjust_voice_pitch(wav)

def referenced_sources(text):
    """Find explicitly attributed third-party sources in RSS text.

    Detection is deliberately conservative: it reports mentions, not
    independent verification or confirmation of the underlying claims.
    """
    text = clean(text)
    patterns = (
        r"\\b(?:laut|nach Angaben von|nach Angaben des|nach Angaben der|wie|berichtet|meldet|meldete)\\s+"
        r"(?:der\\s+|des\\s+|dem\\s+|die\\s+|das\\s+)?"
        r"([A-ZÄÖÜ][\\wÄÖÜäöüß&.-]*(?:\\s+[A-ZÄÖÜ][\\wÄÖÜäöüß&.-]*){0,3})",
        r"\\b(?:gegenüber|unter Berufung auf)\\s+"
        r"([A-ZÄÖÜ][\\wÄÖÜäöüß&.-]*(?:\\s+[A-ZÄÖÜ][\\wÄÖÜäöüß&.-]*){0,3})",
    )
    stop = {"Die", "Der", "Das", "Dem", "Den", "Einem", "Einer", "Angaben",
            "Heute", "Gestern", "Montag", "Dienstag", "Mittwoch",
            "Donnerstag", "Freitag", "Samstag", "Sonntag"}
    found = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            candidate = match.group(1).strip(" ,.;:")
            if candidate.split()[0] in stop or len(candidate) < 3:
                continue
            if candidate not in found:
                found.append(candidate)
    return found[:8]


def crosscheck_headline(title, original_url, max_results=2):
    """Look for independently published coverage using free Google News RSS.

    This is corroboration of the *topic/headline*, not verification of every
    claim. Publisher domains must differ from the original and each other.
    Fail closed on unavailable search services.
    """
    from urllib.parse import urlencode, urlparse
    from difflib import SequenceMatcher
    stop = {"und", "oder", "eine", "einer", "eines", "einem", "einen",
            "über", "nach", "beim", "sich", "dass", "wird", "sind",
            "auch", "mehr", "gegen", "wegen", "durch", "heute", "neue"}
    def terms(value):
        return {w.casefold() for w in re.findall(r"[^\\W_]{4,}", value, re.UNICODE)
                if w.casefold() not in stop}
    original_terms = terms(title)
    result = {"status": "unavailable", "matches": [], "scope": "headline/topic",
              "claim_verified": False}
    if len(original_terms) < 2:
        result["status"] = "insufficient_terms"
        return result
    query = " ".join(list(dict.fromkeys(re.findall(r"[^\\W_]{4,}", title, re.UNICODE)))[:7])
    url = "https://news.google.com/rss/search?" + urlencode(
        {"q": query, "hl": "de", "gl": "AT", "ceid": "AT:de"})
    original_host = (urlparse(original_url).hostname or "").removeprefix("www.")
    seen = {original_host}
    try:
        root = ET.fromstring(fetch(url))
        for item in root.findall(".//item")[:20]:
            candidate_title = clean(item.findtext("title"))
            publisher = item.find("source")
            publisher_name = clean(publisher.text) if publisher is not None else ""
            publisher_url = publisher.get("url", "") if publisher is not None else ""
            publisher_host = (urlparse(publisher_url).hostname or "").removeprefix("www.")
            candidate_url = clean(item.findtext("link"))
            candidate_terms = terms(candidate_title)
            overlap = len(original_terms & candidate_terms) / max(1, min(len(original_terms), len(candidate_terms)))
            similarity = SequenceMatcher(None, title.casefold(), candidate_title.casefold()).ratio()
            if not publisher_host or publisher_host in seen or (overlap < 0.5 and similarity < 0.55):
                continue
            seen.add(publisher_host)
            result["matches"].append({
                "publisher": publisher_name or publisher_host,
                "publisher_domain": publisher_host,
                "headline": candidate_title,
                "url": candidate_url,
                "overlap": round(overlap, 2)
            })
            if len(result["matches"]) >= max_results:
                break
        result["status"] = "other_coverage_found" if result["matches"] else "no_matching_coverage"
    except Exception as exc:
        result["error"] = type(exc).__name__
        print(f"Cross-check unavailable: {type(exc).__name__}: {exc}")
    return result


def edit_news(title, description, style, max_sentences, limit):
    """Offline, conservative editorial formatting without inventing facts."""
    title = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", title))).strip()
    description = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", description))).strip()
    if style == "original":
        clipped = description[:limit].rsplit(" ", 1)[0] if len(description) > limit else description
        return title.rstrip(".!?") + ".\n" + clipped
    if style not in ("classic", "brief"):
        raise ValueError("Unknown editorial style")
    # Only complete sentences; never invent context or paraphrase factual claims.
    sentences = re.split(r"(?<=[.!?])\s+", description)
    sentences = [x.strip() for x in sentences if x.strip() and x.strip()[-1] in ".!?"]
    sentences = [x for x in sentences if x.casefold().rstrip(".!?") != title.casefold().rstrip(".!?")]
    count = 1 if style == "brief" else max_sentences
    selected = sentences[:count]
    return title.rstrip(".!?") + "." + ("\n" + " ".join(selected) if selected else "")

def main():
    DOCS.mkdir(exist_ok=True)
    collected, seen = [], set()
    for url in CONFIG["feeds"]:
        try:
            for entry in items_from_feed(url):
                title, desc, link = entry[:3]
                media = entry[3] if len(entry) > 3 else []
                key = title.casefold()
                if key not in seen:
                    seen.add(key)
                    collected.append((title, desc, link, media))
        except Exception as exc:
            print(f"Feed skipped: {url}: {exc}")
    if not collected:
        raise RuntimeError("No RSS entries available; previous published edition remains unchanged")
    selected = collected[:max(1, min(int(CONFIG.get("max_items", 5)), 10))]
    now = dt.datetime.now(dt.timezone.utc)
    local_now = now.astimezone(ZoneInfo("Europe/Vienna"))
    timestamp = local_now.strftime("%d.%m.%Y um %H:%M Uhr")
    settings = CONFIG.get("presenter_settings", {})
    scenes = settings.get("scenes", {})
    moderator = str(settings.get("name") or "NewsHost")
    def expand_scene_text(value):
        return str(value).replace("{title}", str(CONFIG["title"])).replace("{moderator}", moderator)
    intro_text = expand_scene_text(scenes.get("intro_text") or "Willkommen bei {title}. Hier sind die Nachrichten.")
    outro_text = expand_scene_text(scenes.get("outro_text") or "Das waren die Schlagzeilen. Quellen und Links finden Sie auf unserer Webseite.")
    parts = [intro_text, spoken_timestamp(local_now)]
    limit = max(0, min(int(CONFIG.get("max_description_chars", 180)), 300))
    editorial = CONFIG.get("editorial", {})
    style = editorial.get("style", "classic")
    max_sentences = max(1, min(4, int(editorial.get("max_sentences", 2))))
    source_mentions = []
    crosschecks = []
    verification = editorial.get("crosscheck", {})
    verify_enabled = verification.get("enabled", True)
    max_results = max(1, min(3, int(verification.get("max_sources", 2))))
    for title, desc, link, _ in selected:
        mentions = referenced_sources(title + ". " + desc)
        source_mentions.append({"title": title, "article_url": link,
                                "mentioned_sources": mentions,
                                "checked_scope": "RSS title and description only",
                                "independently_verified": False})
        checked = (crosscheck_headline(title, link, max_results)
                   if verify_enabled else {"status": "disabled", "matches": [],
                                           "scope": "headline/topic", "claim_verified": False})
        checked["original_title"] = title
        checked["original_url"] = link
        crosschecks.append(checked)
        edited = edit_news(title, desc, style, max_sentences, limit)
        if mentions:
            edited += "\n" + "Im RSS-Beitrag werden als weitere Quellen genannt: " + ", ".join(mentions) + "."
        if checked["matches"]:
            publishers = ", ".join(match["publisher"] for match in checked["matches"])
            edited += "\n" + "Auch " + publishers + " berichten über das Thema. Einzelne Aussagen wurden nicht unabhängig verifiziert."
        elif checked["status"] == "no_matching_coverage":
            edited += "\n" + "Bei der automatischen Gegenrecherche wurde keine ausreichend ähnliche Meldung einer anderen Quelle gefunden."
        elif checked["status"] == "unavailable":
            edited += "\n" + "Eine unabhängige Gegenrecherche war technisch nicht möglich."
        parts.append(edited)
    (DOCS / "source-mentions.json").write_text(
        json.dumps(source_mentions, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (DOCS / "crosschecks.json").write_text(
        json.dumps(crosschecks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    parts.append(outro_text)
    script = "\n\n".join(parts)
    (DOCS / "transcript.txt").write_text(script + "\n", encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        # Render each spoken segment independently, then concatenate losslessly.
        # The measured WAV sample counts become authoritative scene boundaries.
        import wave
        wav = Path(tmp) / "speech.wav"
        segment_paths = []
        segment_durations = []
        sample_params = None
        with wave.open(str(wav), "wb") as combined:
            for idx, part in enumerate(parts):
                segment = Path(tmp) / f"segment_{idx:02d}.wav"
                synthesize(part, segment)
                segment_paths.append(segment)
                with wave.open(str(segment), "rb") as source:
                    params = (source.getnchannels(), source.getsampwidth(), source.getframerate(), source.getcomptype())
                    if sample_params is None:
                        sample_params = params
                        combined.setnchannels(params[0])
                        combined.setsampwidth(params[1])
                        combined.setframerate(params[2])
                    elif params != sample_params:
                        raise RuntimeError("Speech segments have incompatible WAV formats")
                    segment_durations.append(source.getnframes() / source.getframerate())
                    while True:
                        data = source.readframes(65536)
                        if not data:
                            break
                        combined.writeframesraw(data)
        boundaries = [0.0]
        for seconds in segment_durations:
            boundaries.append(boundaries[-1] + seconds)
        timeline = {
            "version": 1,
            "segments": [
                {"type": "intro" if idx < 2 else "outro" if idx == len(parts)-1 else "story",
                 "story_index": idx-2 if 2 <= idx < len(parts)-1 else None,
                 "start": round(boundaries[idx], 4), "end": round(boundaries[idx+1], 4)}
                for idx in range(len(parts))
            ],
            "duration": round(boundaries[-1], 4)
        }
        (DOCS / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
        settings = CONFIG.get("presenter_settings", {})
        bg = ROOT / settings.get("background", CONFIG.get("background", "assets/background.jpg"))
        presenter = ROOT / settings.get("portrait", CONFIG.get("presenter", "assets/presenter.png"))
        if settings.get("lip_sync", {}).get("enabled", False):
            print("Lip sync requested but no validated engine is installed; using static portrait fallback")
        media_settings = CONFIG.get("media", {})
        media_mode = media_settings.get("mode", "images_and_videos")
        if media_mode not in ("off", "images", "images_and_videos"):
            raise ValueError("Unsupported RSS media mode")
        max_media_bytes = max(1, min(25, int(media_settings.get("max_download_mb", 12)))) * 1024 * 1024
        story_media = []
        media_credits = []
        for i, entry in enumerate(selected):
            article_images = (article_image_candidates(entry[2])
                              if media_mode != "off" and media_settings.get("prefer_article_images", True)
                              else [])
            # Prefer original article image metadata to small RSS thumbnails.
            videos = [candidate for candidate in entry[3] if candidate[1] == "video"]
            candidates = (videos if media_mode == "images_and_videos" else []) + article_images + entry[3]
            asset = download_media(candidates, media_mode, Path(tmp), i, max_media_bytes)
            credit = {"source": entry[2], "image_origin": "article_metadata_or_rss"}
            if asset is None and media_mode != "off" and media_settings.get("web_image_fallback", True):
                result = search_commons_image(entry[0])
                if result:
                    url, image_title, source_url = result
                    asset = download_media([(url, "image")], "images", Path(tmp), i, max_media_bytes)
                    if asset:
                        credit = {"title": image_title, "source": source_url, "note": "Illustrationsbild, nicht zwingend Aufnahme des Ereignisses"}
                        print(f"Commons fallback for story {i + 1}: {image_title}")
            if asset and asset[1] == "image":
                improved_path, method = improve_news_image(asset[0], media_settings)
                asset = (improved_path, "image")
                if credit is None:
                    credit = {}
                credit["image_processing"] = method
                credit["original_media_retained"] = True
            story_media.append(asset)
            media_credits.append(credit)
        (DOCS / "media-credits.json").write_text(json.dumps(media_credits, ensure_ascii=False, indent=2), encoding="utf-8")
        # Studio stays as background; story media appears on a tilted virtual screen.
        duration_text = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(wav)], text=True
        ).strip()
        duration = float(duration_text)
        scenes = settings.get("scenes", {})
        intro = boundaries[2]
        outro_start = boundaries[-2]
        outro = duration - outro_start
        print(f"Scenes: intro={intro:.1f}s, headlines={outro_start-intro:.1f}s, outro={outro:.1f}s")
        args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        if not bg.is_file():
            print(f"WARNING: studio image missing: {bg}; using solid background")
        if bg.is_file():
            args += ["-loop", "1", "-i", str(bg)]
        else:
            args += ["-f", "lavfi", "-i", "color=c=0x13243a:s=1280x720:r=1"]
        args += ["-i", str(wav)]
        filters = ["[0:v]fps=5,scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,format=yuv420p,setpts=PTS-STARTPTS[bg]"]
        current = "bg"
        intro_mode = scenes.get("intro_mode", "avatar")
        if intro_mode not in ("avatar", "static"):
            raise ValueError("Unsupported intro mode")
        if intro_mode == "static":
            kind = scenes.get("intro_static_type", "color")
            if kind == "color":
                color = str(scenes.get("intro_static_color", "#13243a"))
                if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                    raise ValueError("Invalid intro color")
                args += ["-f", "lavfi", "-i", f"color=c=0x{color[1:]}:s=1280x720:r=5"]
            elif kind == "image":
                relative = str(scenes.get("intro_static_image", "assets/background.jpg"))
                if not re.fullmatch(r"assets/[A-Za-z0-9_./-]+", relative) or ".." in relative:
                    raise ValueError("Invalid intro image path")
                still = ROOT / relative
                if not still.is_file():
                    raise FileNotFoundError("Intro image missing")
                args += ["-loop", "1", "-i", str(still)]
            else:
                raise ValueError("Invalid intro type")
            filters.append("[2:v]fps=5,scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,format=yuv420p[introframe]")
            filters.append(f"[{current}][introframe]overlay=0:0:enable='lt(t,{intro:.3f})'[introcomposed]")
            current = "introcomposed"
        if False and presenter.is_file():  # Legacy portrait disabled
            args += ["-loop", "1", "-i", str(presenter)]
            presenter_visibility = (
                f"gte(t,{outro_start:.3f})" if intro_mode == "static"
                else f"gte(t,{outro_start:.3f})"
            )
            filters += [
                f"[{3 if intro_mode == 'static' else 2}:v]scale=440:600:force_original_aspect_ratio=decrease[person]",
                f"[{current}][person]overlay=x=W-w-55:y=H-h-30:"
                f"enable=\'{presenter_visibility}\'[composed]"
            ]
            current = "composed"
        # Show source media only during the corresponding narrated story.
        for idx, asset in enumerate(story_media):
            if asset is None:
                continue
            path, kind = asset
            input_index = len([a for a in args if a == "-i"])
            if kind == "image":
                args += ["-loop", "1", "-i", str(path)]
            else:
                args += ["-stream_loop", "-1", "-i", str(path)]
            start_time = boundaries[idx + 2]
            end_time = boundaries[idx + 3]
            media_label = f"rssmedia{idx}"
            next_label = f"rssscene{idx}"
            filters.append(
                f"[{input_index}:v]fps=20,scale=620:384:flags=lanczos:"
                f"force_original_aspect_ratio=decrease:force_divisible_by=2,"
                f"pad=620:384:(ow-iw)/2:(oh-ih)/2:color=0x07182b,"
                f"setsar=1,format=yuv420p,setpts=PTS-STARTPTS[{media_label}]"
            )
            filters.append(
                f"[{current}][{media_label}]overlay=x=60:y=60:"
                f"enable='gte(t,{start_time:.3f})*lt(t,{end_time:.3f})':"
                f"eof_action=repeat:shortest=0[{next_label}]"
            )
            current = next_label
            print(f"RSS {kind} used for story {idx + 1}: {path.name}")
        # Animate the transparent host with the final narrated WAV.
        # If the optional animation fails, keep the proven static overlay.
        story_host = ROOT / "assets/host.png"
        story_host_input = None
        lip_render_fps = 5
        lip_settings = settings.get("lip_sync", {})
        if story_host.is_file():
            if lip_settings.get("enabled", False):
                try:
                    from lipsync import generate_frames
                    frame_dir = Path(tmp) / "lipframes"
                    lip_fps = max(5, min(24, int(lip_settings.get("fps", 20))))
                    count = generate_frames(
                        story_host, wav, frame_dir, fps=lip_fps,
                        mouth=lip_settings.get("mouth")
                    )
                    if count:
                        lip_render_fps = lip_fps
                        story_host_input = len([arg for arg in args if arg == "-i"])
                        args += ["-framerate", str(lip_fps), "-i", str(frame_dir / "lip_%06d.png")]
                        print(f"Audio-driven lip animation: {count} frames")
                except Exception as exc:
                    print(f"WARNING: lip animation failed; static host fallback: {exc}")
            if story_host_input is None:
                story_host_input = len([arg for arg in args if arg == "-i"])
                args += ["-loop", "1", "-i", str(story_host)]
        else:
            print("WARNING: assets/host.png missing; no story presenter overlay")
        # Keep the presenter on the right, with the lower body hidden behind the desk line.
        if story_host_input is not None:
            # Split the presenter stream so each story gets an independent
            # filter input; avoid reusing an already consumed FFmpeg pad.
            labels = "".join(f"[hostinput{idx}]" for idx in range(len(selected)))
            filters.append(f"[{story_host_input}:v]split={len(selected)}{labels}")
            for idx in range(len(selected)):
                start_time = boundaries[idx + 2]
                end_time = duration if idx == len(selected) - 1 else boundaries[idx + 3]
                x = "W-w-35"
                label = f"hoststory{idx}"
                filters.append(
                    f"[hostinput{idx}]fps={lip_render_fps},scale=610:765:"
                    f"force_original_aspect_ratio=decrease,format=rgba,"
                    f"crop=iw:min(ih\\,340):0:0"
                    f"[personstory{idx}]"
                )
                filters.append(
                    f"[{current}][personstory{idx}]overlay=x={x}:y=200:"
                    f"enable='gte(t,{start_time:.3f})*lt(t,{end_time:.3f})':"
                    f"eof_action=repeat[{label}]"
                )
                current = label
        # An independent transparent desk image is the correct foreground.
        # Unlike cropping the studio photo, it can cover the presenter's hands
        # without copying unwanted background pixels over the presenter.
        desk_path = ROOT / settings.get("desk_foreground", "assets/desk_foreground.png")
        if desk_path.is_file():
            desk_input = len([arg for arg in args if arg == "-i"])
            args += ["-loop", "1", "-i", str(desk_path)]
            filters.append(
                f"[{desk_input}:v]fps=5,scale=1280:720,format=rgba,"
                "setpts=PTS-STARTPTS[deskforeground]"
            )
            filters.append(
                f"[{current}][deskforeground]overlay=x=0:y=0:"
                f"enable='gte(t,{intro:.3f})':eof_action=repeat:shortest=0[behinddesk]"
            )
            current = "behinddesk"
        else:
            # Compatibility with existing studios until the separate desk
            # PNG is uploaded. Never treat the whole background as foreground.
            filters.append(
                "[0:v]fps=5,scale=1280:720:force_original_aspect_ratio=increase,"
                "crop=1280:720,crop=560:190:720:530,format=rgba,"
                "geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
                "a='255*min(1,max(0,Y/8))',"
                "setpts=PTS-STARTPTS[deskforeground]"
            )
            filters.append(
                f"[{current}][deskforeground]overlay=x=720:y=530:"
                f"enable='gte(t,{intro:.3f})':eof_action=repeat:shortest=0[behinddesk]"
            )
            current = "behinddesk"
        # Technical / AI broadcast identity: all graphics are rendered locally by FFmpeg.
        # Use text files so feed titles and brand names cannot inject filter syntax.
        font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        brand_file = Path(tmp) / "brand.txt"
        brand_file.write_text(str(CONFIG["title"]), encoding="utf-8")
        outro_file = Path(tmp) / "outro.txt"
        outro_file.write_text("QUELLEN & WEITERE NACHRICHTEN", encoding="utf-8")
        filters.append(
            f"[{current}]drawgrid=width=80:height=80:thickness=1:color=0x36d9ff@0.12:"
            f"enable='lt(t,{intro:.3f})'[grid]"
        )
        current = "grid"
        filters.append(
            f"[{current}]drawbox=x=0:y=0:w=iw:h=12:color=0x30d8ff@0.95:t=fill:"
            f"enable='lt(t,{intro:.3f})'[accent]"
        )
        current = "accent"
        filters.append(
            f"[{current}]drawtext=fontfile={font}:textfile={brand_file}:"
            f"fontcolor=white:fontsize=68:x=(w-text_w)/2:y=(h-text_h)/2-35:"
            f"borderw=2:bordercolor=0x0a1830:"
            f"enable='lt(t,{intro:.3f})'[brand]"
        )
        current = "brand"
        filters.append(
            f"[{current}]drawtext=fontfile={font}:text='KI  /  NEWS  /  LIVE':"
            f"fontcolor=0x54ddff:fontsize=24:x=(w-text_w)/2:y=h/2+65:"
            f"enable='lt(t,{intro:.3f})'[introtag]"
        )
        current = "introtag"
        filters.append(
            f"[{current}]drawtext=fontfile={font}:textfile={outro_file}:"
            f"fontcolor=0x54ddff:fontsize=22:x=(w-text_w)/2:y=h/2+65:"
            f"enable='lt(t,0)'[outrotag]"
        )
        current = "outrotag"
        if scenes.get("show_headlines", True) and selected:
            # Each headline gets its own timed overlay, rather than one overflowing text block.
            story_count = len(selected)
            for idx, (title, _, _, _) in enumerate(selected):
                start_time = boundaries[idx + 2]
                end_time = boundaries[idx + 3]
                headline_file = Path(tmp) / f"headline_{idx}.txt"
                # Wrap text to fit the 1280px canvas.
                import textwrap
                wrapped = textwrap.wrap(title, width=34, break_long_words=True)
                if len(wrapped) > 3:
                    wrapped = wrapped[:3]
                    wrapped[-1] = wrapped[-1].rstrip(" .") + "…"
                headline_file.write_text("\n".join(wrapped), encoding="utf-8")
                print(f"Headline {idx+1}/{story_count}: {start_time:.1f}-{end_time:.1f}s: {title[:65]}")
                source_file = Path(tmp) / f"source_{idx}.txt"
                from urllib.parse import urlparse
                host = urlparse(selected[idx][2]).hostname or "Quelle im Web"
                source_file.write_text(host[:75], encoding="utf-8")
                source_label = f"source{idx}"
                # Unified left-side editorial card, with media above the title.
                card_x, card_w = 55, 635
                has_media = story_media[idx] is not None
                card_y = 425 if has_media else 195
                card_h = 200 if has_media else 325
                filters.append(
                    f"[{current}]drawbox=x={card_x}:y={card_y}:w={card_w}:h={card_h}:"
                    f"color=0x07182b@0.91:t=fill:"
                    f"enable='gte(t,{start_time:.3f})*lt(t,{end_time:.3f})'[card{idx}]"
                )
                current = f"card{idx}"
                filters.append(
                    f"[{current}]drawbox=x={card_x}:y={card_y}:w=7:h={card_h}:"
                    f"color=0x35d9ff@0.98:t=fill:"
                    f"enable='gte(t,{start_time:.3f})*lt(t,{end_time:.3f})'[stripe{idx}]"
                )
                current = f"stripe{idx}"
                filters.append(
                    f"[{current}]drawtext=fontfile={font}:textfile={source_file}:"
                    f"fontcolor=0x67dfff:fontsize=21:x={card_x + 24}:y={card_y + card_h - 38}:"
                    f"enable='gte(t,{start_time:.3f})*lt(t,{end_time:.3f})'[credit{idx}]"
                )
                current = f"credit{idx}"
                next_label = "v" if idx == story_count - 1 else f"story{idx}"
                filters.append(
                    f"[{current}]drawtext=fontfile={font}:"
                    f"textfile={headline_file}:fontcolor=white:fontsize={28 if has_media else 34}:"
                    f"line_spacing=8:x={card_x + 24}:y={card_y + 22}:"
                    f"enable='gte(t,{start_time:.3f})*lt(t,{end_time:.3f})'[{next_label}]"
                )
                current = next_label
        # Render source credits on top of every earlier story layer.
        # Use the configured RSS URLs rather than the article landing-page URLs.
        outro_media = Path(tmp) / "outro_media.txt"
        outro_media.write_text("RSS-QUELLEN", encoding="utf-8")
        outro_detail = Path(tmp) / "outro_detail.txt"
        import textwrap
        feed_lines = []
        for feed_url in CONFIG.get("feeds", []):
            # Break after URL separators, but never truncate the only source.
            url_text = str(feed_url).strip()
            feed_lines.extend(textwrap.wrap(url_text, width=45, break_long_words=True,
                                            break_on_hyphens=False))
        if not feed_lines:
            feed_lines = ["Keine RSS-Feeds konfiguriert"]
        if len(feed_lines) > 5:
            feed_lines = feed_lines[:5] + ["Weitere URLs in config.json"]
        outro_detail.write_text("\n".join(feed_lines), encoding="utf-8")
        outro_editorial = Path(tmp) / "outro_editorial.txt"
        outro_editorial.write_text(
            "KI-gestuetzte redaktionelle Bearbeitung:\n"
            "Quellensuche, Abgleich und Zusammenfassung",
            encoding="utf-8"
        )
        outro_headline = Path(tmp) / "outro_headline.txt"
        outro_headline.write_text(
            "PERSONAL NEWS HOST\n"
            "Produktion: Python, Piper TTS, FFmpeg",
            encoding="utf-8"
        )
        outro_enable = f"gte(t,{outro_start:.3f})"
        for label, x, y, w, h, color in (
            ("outromedia", 55, 60, 635, 355, "0x07182b@0.97"),
            ("outrocard", 55, 425, 635, 200, "0x07182b@0.97"),
            ("outrostripe", 55, 425, 7, 200, "0x35d9ff@0.98"),
        ):
            next_label = f"{label}layer"
            filters.append(
                f"[{current}]drawbox=x={x}:y={y}:w={w}:h={h}:color={color}:t=fill:"
                f"enable='{outro_enable}'[{next_label}]"
            )
            current = next_label
        for label, file, size, color, x, y in (
            ("outromediatitle", outro_media, 35, "0x54ddff", 85, 92),
            ("outromediadetail", outro_detail, 23, "white", 85, 155),
            ("outroeditorial", outro_editorial, 20, "0x9addeb", 85, 296),
            ("outroheadline", outro_headline, 28, "white", 85, 463),
        ):
            next_label = f"{label}layer"
            filters.append(
                f"[{current}]drawtext=fontfile={font}:textfile={file}:"
                f"fontcolor={color}:fontsize={size}:line_spacing=10:x={x}:y={y}:"
                f"enable='{outro_enable}'[{next_label}]"
            )
            current = next_label
        filters.append(f"[{current}]null[v]")
        args += ["-filter_complex", ";".join(filters), "-map", "[v]", "-map", "1:a",
                 "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
                 "-r", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
                 "-t", f"{duration:.3f}", "-shortest", "-movflags", "+faststart", str(DOCS / "latest.mp4")]
        run(args)
    lines = ["<!doctype html><html lang='de'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
             "<title>PersonalNewsHost</title><style>body{font:1.1rem system-ui;background:#13243a;color:white;max-width:900px;margin:3rem auto;padding:1rem}a{color:#8ed6ff}video{width:100%}</style>",
             "<h1>PersonalNewsHost</h1><p>Stand: " + html.escape(timestamp) + "</p>",
             "<video controls src='latest.mp4?v=" + now.strftime("%Y%m%d%H%M%S") + "'></video><p><a href='feed.xml'>Video-RSS abonnieren</a> · <a href='transcript.txt'>Transkript</a> · <a href='settings.html'>Konfiguration (Beta)</a> · <a href='browser-studio.html'>Browser-Studio (Beta)</a></p><h2>Quellen</h2><ul>"]
    for title, _, link, _ in selected:
        safe = link if link.startswith(("https://", "http://")) else "#"
        lines.append("<li><a rel='noopener noreferrer' href='" + html.escape(safe, quote=True) + "'>" + html.escape(title) + "</a></li>")
    lines.append("</ul><p>Automatisch aus RSS erstellt; Inhalte nicht unabhängig überprüft.</p></html>")
    (DOCS / "index.html").write_text("\n".join(lines), encoding="utf-8")
    pubdate = email.utils.format_datetime(now)
    guid = now.isoformat()
    feed = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
            '<title>PersonalNewsHost Videos</title><link>' + BASE + '</link>'
            '<description>Automatisch generierte Nachrichten-Videos</description><language>de</language>'
            '<atom:link href="' + BASE + 'feed.xml" rel="self" type="application/rss+xml"/>'
            '<item><title>Nachrichten ' + html.escape(timestamp) + '</title>'
            '<guid isPermaLink="false">' + guid + '</guid>'
            '<pubDate>' + pubdate + '</pubDate>'
            '<description>Aktuelle Ausgabe; Quellen auf der Webseite.</description>'
            '<enclosure url="' + BASE + 'latest.mp4" length="' + str((DOCS / "latest.mp4").stat().st_size) + '" type="video/mp4"/>'
            '</item></channel></rss>')
    (DOCS / "feed.xml").write_text(feed, encoding="utf-8")
    print(f"Generated {len(selected)} stories; video size {(DOCS / 'latest.mp4').stat().st_size} bytes")

if __name__ == "__main__":
    main()
