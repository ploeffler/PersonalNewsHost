# Recherche: lokale Text-, Bild- und Videogenerierung

Stand: 29.10.2026. Dokumentationsrecherche; keine Installation, kein eigener Benchmark und keine Hardwareprüfung. Auswahl geeigneter Kandidaten, keine vollständige Marktübersicht. Verfügbare Checkpoints sind nicht zwangsläufig die neuesten oder besten für diesen Rechner.

## Laufzeiten und Container

| Lösung | Einsatz | CPU/GPU | Container |
|---|---|---|---|
| Ollama | Textmodelle und Modellverwaltung | CPU; unterstützte NVIDIA-/AMD-GPUs und Vulkan abhängig von Hardware/Build | Offizielles `ollama/ollama`; ROCm-Variante |
| llama.cpp | Quantisierte GGUF-Textmodelle, API-Server | CPU und verschiedene GPU-Backends; teilweises GPU-Offloading möglich | Offizielle Serverimages, u.a. CUDA, ROCm, Vulkan |
| LocalAI | Gemeinsame API für Text, Bild, Audio und Video über Backends | Fähigkeit hängt vom ausgewählten Backend und Modell ab | Offizielles `localai/localai` |
| ComfyUI | Reproduzierbare Bild-/Video-Workflows, API und Vorschau | CPU-Modus vorhanden; GPU für anspruchsvolle Medien empfohlen | Eigener reproduzierbarer Container oder gesondert geprüftes Community-Image; hier kein offizielles Image verifiziert |
| stable-diffusion.cpp | Schlankes Bildbackend und unterstützte Videomodelle | CPU sowie u.a. CUDA/Vulkan; Modell-/Backendkompatibilität prüfen | Projekt dokumentiert GHCR-Image und eigene Vulkan-/ROCm-Builds |
| Docker Model Runner | Alternative Docker-nahe Modellverwaltung | llama.cpp für CPU/GPU; Diffusers-Backend laut Dokumentation NVIDIA-GPU | Docker-Komponente; nicht mit einem beliebigen eigenständigen Compose-Service gleichsetzen |

Quellen: [Ollama Docker](https://github.com/ollama/ollama/blob/main/docs/docker.mdx), [llama.cpp Docker](https://github.com/ggml-org/llama.cpp/blob/master/docs/docker.md), [LocalAI Überblick](https://localai.io/docs/overview/), [LocalAI Video](https://localai.io/docs/features/video-generation/index.print.html), [ComfyUI](https://github.com/Comfy-Org/ComfyUI), [stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp), [sd.cpp Docker](https://github.com/leejet/stable-diffusion.cpp/blob/master/docs/docker.md), [Docker Model Runner](https://docs.docker.com/ai/model-runner/inference-engines/).

## Konkrete Modelle für erste Tests

- **Text: Qwen3-8B**, mehrsprachig, Apache-2.0. Quantisierte Varianten für Ollama/llama.cpp nach Herkunft prüfen. Eigene deutsche Nachrichtentests für Quellenbindung, Stilprofil und strukturierte Ausgaben erforderlich. [Modellkarte](https://huggingface.co/Qwen/Qwen3-8B)
- **Bilder: FLUX.1-schnell**, Text-zu-Bild, 1–4 Generierungsschritte, Apache-2.0. Für Hintergründe, Symbolbilder und Avatarentwürfe; konkrete Speicheranforderungen hängen von Präzision und Offloading ab. Nicht alle FLUX-Varianten haben dieselbe Lizenz. [Modellkarte](https://huggingface.co/black-forest-labs/FLUX.1-schnell)
- **Bilder: SD 1.5 oder SDXL**, in ComfyUI und stable-diffusion.cpp unterstützt; kleinere bzw. etablierte Vergleichsbasis. Lizenz des tatsächlich verwendeten Checkpoints separat prüfen. [Backend-Modellübersicht](https://github.com/leejet/stable-diffusion.cpp)
- **Video: Wan2.2 TI2V-5B**, Text-/Bild-zu-Video. Offizieller Referenzlauf nennt mindestens 24 GB VRAM mit CPU-Offloading; große A14B-Referenzläufe mindestens 80 GB. Kleinere quantisierte Community-Setups sind kein gleichwertiger offizieller Hardware-Nachweis. [Projekt und Referenzbefehle](https://github.com/Wan-Video/Wan2.2)
- **Video: LTX-Video**, weiterer lokaler Kandidat mit ComfyUI-Anbindung. Speicher, Qualität und Lizenz des konkreten Checkpoints vor Auswahl prüfen. [Offizielles Projekt](https://github.com/Lightricks/LTX-Video)

## Empfehlung für PersonalNewsHost

Als Architekturvorschlag: Anwendung, Textdienst und Medienworker als getrennte Services. Zuerst Ollama mit einem quantisierten Qwen3-Modell testen; alternativ llama.cpp für genauere Laufzeitkontrolle. Für Bilder und optionale Clips ComfyUI mit fest versionierten lokalen Workflows evaluieren. LocalAI ist eine Alternative, wenn ein einheitlicher API-Zugang wichtiger als die direkte Workflowsteuerung ist.

CPU-Profil: lokaler Text, vorhandene TTS, Grafiken/Standbilder und FFmpeg-Komposition. GPU-Profil: zusätzliche Bildgenerierung und optional generative Clips. CPU-Unterstützung einer Laufzeit ist keine Zusage, jedes Videomodell sinnvoll ohne GPU betreiben zu können. Eine komplette Nachrichtensendung kann auch ohne generatives Videomodell aus Bildern, Grafiken, Studioansichten und Audio zusammengesetzt werden.

GPU-Zugriff ist optional je Worker zu konfigurieren. Hosttreiber und Container-Backend müssen zusammenpassen; GPU-Durchreichung allein macht ein CPU-Image nicht GPU-fähig. Modelle und Cache persistent speichern, schwere Jobs über eine gemeinsame Warteschlange koordinieren und Modelle bei Bedarf entladen. Lokale Inferenz-APIs nur intern erreichbar machen. Modelle/Workflows dürfen keine Cloud-API-Knoten enthalten, wenn vollständig lokaler Betrieb gewählt ist.

Vor endgültiger Auswahl: GPU-Modell und VRAM, RAM, CPU und verfügbaren Speicher erfassen. Dann identische deutsche Textaufgaben, ein Referenzbild und einen kurzen Clip auf dem Zielrechner messen. Lokale Nutzung spart externe API-Gebühren, benötigt aber Rechenzeit, Strom und Speicher.
