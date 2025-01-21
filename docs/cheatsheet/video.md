# Video utils
## Video Subtitles
This tutorial explains how to add subtitles to the video files.

### Prepare
Install:
```sh
sudo apt install qnapi uchardet ffmpeg recode
```

### Download subtitles for your language

#### Qnapi
```sh
qnapi -l pl *.mp4
qnapi -l pl *.mkv
```

#### VLsub
or open with VLC, with VLsub extension.

#### Subliminal
```sh
pip install subliminal
subliminal download -l pl *.mkv
```

### Detect encoding
```sh
uchardet *.txt
```
Expect `UTF-8`, `Windows-1250` or `UTF-16`.

### Verify that converted encoding is actually fine 
```sh
cat *.txt | recode cp1250..utf8
cat *.txt | recode utf16..utf8
```

Available encodings:
```sh
recode --list
```

### Recode to UTF8
```sh
recode cp1250..utf8 *.txt
# or
recode utf16..utf8 *.txt
```

### Convert to SRT
Convert TXT to SRT, add `.default.srt` suffix for Jellyfin:
```sh
ffmpeg -i 'S01E03.txt' 'S01E03.default.srt'
```
```sh
ls -1 *.txt | sed -e 's/\.txt$//g' | xargs -d '\n' -I %s echo 'ffmpeg -i "%s.txt" "%s.default.srt"'
```

### Appendix
Do the ffmpeg conversion for all TXT files in the current directory:
```python
from pathlib import Path
from nuclear import shell

for path in Path('.').iterdir():
    if path.name.endswith('.txt'):
        stem = path.name[:-4]
        print(f'converting {path.name}')
        shell(f"ffmpeg -i '{stem}.txt' '{stem}.default.srt'")
```

## Download YouTube video as MP4
```sh
pip install -U yt-dlp
yt-dlp -f 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' URL
```

## Dynamic Audio Normalizer
This allows for applying extra gain to the "quiet" sections of the audio while avoiding distortions or clipping the "loud" sections.
In other words: The Dynamic Audio Normalizer will "even out" the volume of quiet and loud sections, in the sense that the volume of each section is brought to the same target level.
```sh
ffmpeg -i "$INPUT.mkv" -c:v copy -af "dynaudnorm=maxgain=30" -c:a aac -b:a 192k "$INPUT.norm.mkv"
```
```sh
ls -1 *.mkv | sed -e 's/\.mkv$//g' | xargs -d '\n' -I %s echo 'ffmpeg -i "%s.mkv" -c:v copy -af "dynaudnorm=maxgain=30" -c:a aac -b:a 192k "%s.norm.mkv"'
ls -1 *.mp4 | sed -e 's/\.mp4$//g' | xargs -d '\n' -I %s echo 'ffmpeg -i "%s.mp4" -c:v copy -af "dynaudnorm=maxgain=30" -c:a aac -b:a 192k "%s.norm.mp4"'
```
