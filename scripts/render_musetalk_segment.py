import gc,json,resource,subprocess,traceback,sys,math,argparse
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument("--segment",choices=["intro","outro"],required=True)
args=parser.parse_args()
out=Path("musetalk-render")
out.mkdir(exist_ok=True)
plan=json.loads(Path("broadcast-plan.json").read_text(encoding="utf-8"))
segment=next(x for x in plan["segments"] if x["id"]==args.segment)
report={"segment":args.segment,"device":"cpu","pipeline":"MuseTalk 1.5 ten-fps inference and FFmpeg optical flow interpolation","full_official_inference":False}
try:
    import torch, numpy as np, cv2
    from PIL import Image
    from huggingface_hub import hf_hub_download
    torch.set_num_threads(4)
    subprocess.run(["git","clone","--depth","1","https://github.com/TMElyralab/MuseTalk.git","/tmp/official-musetalk"],check=True)
    import sys
    sys.path.insert(0,"/tmp/official-musetalk")
    from musetalk.utils.audio_processor import AudioProcessor
    from musetalk.models.unet import PositionalEncoding, UNet
    from musetalk.models.vae import VAE
    from transformers import WhisperModel
    import sys
    sys.path.insert(0,str(Path.cwd()/"scripts"))
    from generate import synthesize
    speech=segment["speech_text"]
    synthesize(speech,out/"speech-long.wav")
    report["speech_engine"]="Piper de_DE-thorsten-high"
    report["speech_text"]=speech
    import soundfile as sf
    audio_data,audio_rate=sf.read(str(out/"speech-long.wav"))
    report["raw_speech_seconds"]=round(len(audio_data)/audio_rate,3)
    duration=len(audio_data)/audio_rate
    if duration<=0:raise RuntimeError("Empty Piper audio")
    sf.write(str(out/"speech.wav"),audio_data,audio_rate)
    report["speech_seconds"]=round(duration,3)
    ap=AudioProcessor(feature_extractor_path="openai/whisper-tiny")
    features,audio_length=ap.get_audio_feature(str(out/"speech.wav"))
    whisper=WhisperModel.from_pretrained("openai/whisper-tiny").eval()
    with torch.inference_mode():
        chunks=ap.get_whisper_chunk(features,"cpu",torch.float32,whisper,audio_length,fps=10)
        conditioned=PositionalEncoding(d_model=384)(chunks[:1])
    report["official_audio_chunks"]=list(chunks.shape)
    report["official_positional_encoding"]=list(conditioned.shape)
    del whisper,features,ap,chunks
    gc.collect()
    model_dir=Path("/tmp/official-vae")
    model_dir.mkdir(exist_ok=True)
    for fname in ["config.json","diffusion_pytorch_model.bin"]:
        source=hf_hub_download(repo_id="stabilityai/sd-vae-ft-mse",filename=fname)
        (model_dir/fname).symlink_to(source)
    vae=VAE(model_path=str(model_dir))
    im=np.array(Image.open("assets/presenter.png").convert("RGB"))[:,:,::-1].copy()
    x1,y1,x2,y2=730,105,949,400
    face=cv2.resize(im[y1:y2,x1:x2],(256,256))
    Image.fromarray(cv2.cvtColor(face,cv2.COLOR_BGR2RGB)).save(out/"source-face.png")
    with torch.inference_mode():
        latents=vae.get_latents_for_unet(face)
    report["official_vae_latents"]=list(latents.shape)
    report["official_vae_latents_finite"]=bool(torch.isfinite(latents).all())
    report["official_mask"]="upper half retained, lower half zero before [-1,1] normalization"
    unet_weights=hf_hub_download(repo_id="TMElyralab/MuseTalk",filename="musetalkV15/unet.pth")
    unet_config=hf_hub_download(repo_id="TMElyralab/MuseTalk",filename="musetalkV15/musetalk.json")
    net=UNet(unet_config=unet_config,model_path=unet_weights,device=torch.device("cpu"))
    net.model.eval()
    import time
    frames_dir=out/"frames"
    frames_dir.mkdir(exist_ok=True)
    target_frames=max(1,math.floor(duration*10))
    report["target_frames"]=target_frames
    report["neural_fps"]=10
    report["output_fps"]=25
    # Rebuild all official audio chunks after the Whisper stage has been released.
    ap=AudioProcessor(feature_extractor_path="openai/whisper-tiny")
    features,audio_length=ap.get_audio_feature(str(out/"speech.wav"))
    whisper=WhisperModel.from_pretrained("openai/whisper-tiny").eval()
    with torch.inference_mode():
        chunks=ap.get_whisper_chunk(features,"cpu",torch.float32,whisper,audio_length,fps=10)
        all_audio=PositionalEncoding(d_model=384)(chunks)
    del whisper,features,ap,chunks
    gc.collect()
    original=Image.open("assets/presenter.png").convert("RGB")
    import PIL.ImageFilter
    mask=Image.new("L",(256,256),0)
    from PIL import ImageDraw
    ImageDraw.Draw(mask).ellipse((45,105,212,247),fill=255)
    mask=mask.filter(PIL.ImageFilter.GaussianBlur(13))
    start=time.monotonic()
    report["available_audio_frames"]=len(all_audio)
    if len(all_audio)<target_frames:
        raise RuntimeError(f"Only {len(all_audio)} audio-conditioned frames available, need {target_frames}")
    for idx in range(target_frames):
        with torch.inference_mode():
            predicted=net.model(latents,torch.tensor([0]),encoder_hidden_states=all_audio[idx:idx+1]).sample
            reconstructed=vae.decode_latents(predicted)[0]
        generated=Image.fromarray(cv2.cvtColor(reconstructed,cv2.COLOR_BGR2RGB))
        blended=Image.composite(generated,Image.fromarray(cv2.cvtColor(face,cv2.COLOR_BGR2RGB)),mask)
        full=original.copy()
        full.paste(blended.resize((x2-x1,y2-y1)),(x1,y1))
        full.thumbnail((960,540))
        full.save(frames_dir/f"frame-{idx:03d}.png")
        print("Official MuseTalk frame",idx+1,flush=True)
    report["frames"]=target_frames
    report["complete_segment"]=report["frames"]==target_frames
    report["unet_decode_seconds"]=round(time.monotonic()-start,3)
    output=Path("rendered")/(args.segment+".mp4")
    output.parent.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg","-y","-loglevel","error","-framerate","10","-i",str(frames_dir/"frame-%03d.png"),"-i",str(out/"speech.wav"),"-vf",f"scale=1280:720,tpad=stop_mode=clone:stop_duration=1,minterpolate=fps=25:mi_mode=mci:mc_mode=obmc:me_mode=bidir,trim=duration={duration:.6f},setpts=PTS-STARTPTS","-t",str(duration),"-c:v","libx264","-preset","ultrafast","-r","25","-pix_fmt","yuv420p","-c:a","aac","-ar","48000","-b:a","160k","-shortest",str(output)],check=True)
    report["video_generated"]=True
    report["unet_decode_seconds_per_frame"]=round(report["unet_decode_seconds"]/max(1,report["frames"]),3)
    report["fps"]=25
    report["interpolated_frames"]=True
    report["neural_frames"]=target_frames
    report["output_frames_target"]=round(duration*25)
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-count_frames","-show_entries","stream=nb_read_frames,r_frame_rate,duration","-of","json",str(output)],text=True))
    report["output_video_probe"]=probe
    actual_frames=int(probe["streams"][0]["nb_read_frames"])
    report["output_frames_actual"]=actual_frames
    if abs(actual_frames-round(duration*25))>1:
        raise RuntimeError(f"Unexpected frame count {actual_frames} for {duration}s")
    report["visual_quality_verified"]=False
    report["production_publishing_enabled"]=False
    report["status"]="success" if report["complete_segment"] else "error"
except Exception as exc:
    report["status"]="error"
    report["error"]=repr(exc)
    traceback.print_exc()
report["max_rss_kb"]=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
(out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2),flush=True)
if report["status"]=="error":raise SystemExit(1)
