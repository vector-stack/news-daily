import json,re,os,subprocess,time,sys
N=json.load(open("news.json"));seg="_seg";os.makedirs(seg,exist_ok=True)
lines=[("zh",N["intro_zh"]),("en",N["intro_en"])]
for s in N["sections"]:
    lines.append(("zh",f"{s['name'].replace('/','与')}。"))
    for it in s["items"]:
        lines.append(("zh",f"{it['title']}。{it['sum']}。"))
        lines.append(("en",re.sub(r"[（(][^）)]*[）)]\s*$","",it["en"])))
lines+=[("zh",N["outro_zh"]),("en",N["outro_en"])]
V={"zh":"zh-CN-XiaoxiaoNeural","en":"en-US-AndrewNeural"}
gap=f"{seg}/gap.mp3"
subprocess.run(["ffmpeg","-y","-loglevel","error","-f","lavfi","-i","anullsrc=r=24000:cl=mono","-t","0.6","-c:a","libmp3lame","-b:a","48k",gap],check=True)
dur=lambda f:float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout.strip() or 0)
files=[];retries=0;short=0;fail=0;t0=time.time()
for k,(lang,t) in enumerate(lines):
    o=f"{seg}/{k:03d}.mp3";ok=False
    for a in range(5):
        r=subprocess.run([sys.executable,"-m","edge_tts","--voice",V[lang],"--rate=+5%","--text",t,"--write-media",o],capture_output=True)
        if r.returncode==0 and os.path.exists(o) and os.path.getsize(o)>0:
            d=dur(o);exp=(len(t.split())/2.8) if lang=="en" else (len(t)/5.0)
            if d>=max(0.5,0.45*exp): ok=True;break
            short+=1;print(f"SHORT {d:.1f}<{exp:.1f}: {t[:30]}")
        else: print("ERR",r.stderr.decode()[-200:])
        retries+=1;time.sleep(2)
    if not ok: fail+=1;print("FAIL",t[:40]);continue
    files+=[o,gap]
open(f"{seg}/list.txt","w").write("".join(f"file '{os.path.abspath(f)}'\n" for f in files))
subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",f"{seg}/list.txt","-ar","24000","-ac","1","-c:a","libmp3lame","-b:a","64k","news.mp3"],check=True)
res=dict(segments=len(lines),failed=fail,retries=retries,short=short,tts_seconds=round(time.time()-t0,1),mp3_seconds=round(dur("news.mp3"),1),mp3_mb=round(os.path.getsize("news.mp3")/1e6,2))
print(json.dumps(res));json.dump(res,open("result.json","w"))
with open(os.environ.get("GITHUB_STEP_SUMMARY","/dev/null"),"a") as f: f.write("```\n"+json.dumps(res,indent=1)+"\n```\n")
sys.exit(1 if fail else 0)
