#!/usr/bin/env bash
# Renders a 16s 9:16 motion-graphics Reel from product.jpg with ffmpeg.
# Not AI-generated footage: image moves, transitions, effects, text cards, beat.
set -euo pipefail
cd "$(dirname "$0")"
F=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
IMG=product.jpg
OUT=${1:-vortex-ring-blade-reel.mp4}
FPS=30; X=0.4
D=(3.0 3.2 3.0 3.0 2.8 3.0)   # sum 18 - 5*0.4 = 16s

# seg <index> <zoom expr> <vf extra> <text> <size>
seg() {
  local i=$1 z=$2 fx=$3 txt=$4 sz=$5 d=${D[$1]}
  local n=$(python3 -c "print(int($d*$FPS))")
  ffmpeg -y -loglevel error -loop 1 -i $IMG -filter_complex "
    [0]split[a][b];
    [a]scale=-2:1920,crop=1080:1920,boxblur=30:5,eq=brightness=-0.25[bg];
    [b]scale=2160:2160,zoompan=z='$z':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$n:s=1080x1080:fps=$FPS[fg];
    [bg][fg]overlay=0:420,${fx}drawbox=y=1480:w=1080:h=6:color=0x4aa8ff@0.9:t=fill,
    drawtext=fontfile=$F:text='$txt':fontsize=$sz:fontcolor=white:borderw=6:bordercolor=0x1450ff:x=(w-text_w)/2:y=300:enable='gte(t,0.05)',
    format=yuv420p,setsar=1,trim=duration=$d,setpts=PTS-STARTPTS[v]" -map "[v]" -r $FPS -t $d seg$i.mp4
}
seg 0 "1.6-0.6*on/90"          "" "1 SECOND"        150
seg 1 "1.0+0.5*on/96"          "" "BOTH BLADES OUT" 105
seg 2 "1.2"                    "hue=h='t*130':s=1.6," "7 COLOURS" 140
seg 3 "1.1+0.3*sin(on/8)"      "rgbashift=rh=6:bh=-6," "GRAVITY SENSOR" 100
seg 4 "1.7-0.5*on/84"          "eq=contrast=1.4:saturation=1.8," "HIT SFX ON" 130
seg 5 "1.0+0.2*on/90"          "" "PICK A COLOUR" 120

T=(fadewhite zoomin hblur radial pixelize)
cmd=(ffmpeg -y -loglevel error); for i in 0 1 2 3 4 5; do cmd+=(-i seg$i.mp4); done
fc=""; prev="[0:v]"; off=0
for i in 1 2 3 4 5; do
  off=$(python3 -c "print(round(${D[$((i-1))]}+$off-$X,3))")
  fc+="${prev}[$i:v]xfade=transition=${T[$((i-1))]}:duration=$X:offset=$off[x$i];"; prev="[x$i]"
done
# audio: 120bpm kick + hats + whoosh at each cut
A="aevalsrc='0.9*sin(2*PI*(50+60*exp(-30*mod(t,0.5)))*t)*exp(-9*mod(t,0.5))':d=16:s=44100[k];"
A+="anoisesrc=d=16:c=white:r=44100,highpass=f=7000,volume='0.25*exp(-40*mod(t+0.25,0.5))':eval=frame[h];"
A+="anoisesrc=d=16:c=pink:r=44100,bandpass=f=1800:w=1500,volume='0.7*(lt(abs(mod(t,3.2)-2.8),0.35))':eval=frame[w];"
A+="[k][h][w]amix=inputs=3:normalize=0,alimiter=limit=0.95,afade=t=out:st=15.5:d=0.5[a]"
"${cmd[@]}" -filter_complex "$fc$A" -map "$prev" -map "[a]" -c:v libx264 -crf 20 -preset medium -c:a aac -b:a 160k -shortest -movflags +faststart "$OUT"
rm -f seg?.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
