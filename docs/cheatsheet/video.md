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

Extract normalized audio from video:
```sh
ffmpeg -i input.mkv -map a \
    -filter:a "pan=stereo|FL < 1.0*FL + 0.707*FC + 0.707*BL|FR < 1.0*FR + 0.707*FC + 0.707*BR" \
    -filter:a "aresample=matrix_encoding=dplii" \
    -filter:a "dynaudnorm=maxgain=50:framelen=400:gausssize=15" \
    -ac 2 -q:a 0 \
    output.mp3
```

## Split video into chunks
```python
#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "nuclear",
# ]
# ///
from nuclear import shell, logger
from pathlib import Path

src_path = '[INPUT_PATH].mkv'
dst_suffix = '-[TITLE].mkv'
chunk_duration = 10  # in minutes

def format_duration_m(minutes: int) -> str:
    return f"{minutes // 60}:{minutes % 60}:00"

src_duration_s = float(shell(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{src_path}"').strip())
parts = list(range(0, int(src_duration_s // 60), chunk_duration))
logger.debug('Creating chunks', parts=parts, count=len(parts))
for index, part in enumerate(parts):
    minutes_from = part
    minutes_to = part + chunk_duration
    out_path = f'{str(index+1).zfill(3)}{dst_suffix}'
    shell(
        f'ffmpeg'
        f' -i "{src_path}"'
        f' -ss {format_duration_m(minutes_from)} -to {format_duration_m(minutes_to)}'
        f' -c:v copy'
        f' -filter:a "pan=stereo|FL < 1.0*FL + 0.707*FC + 0.707*BL|FR < 1.0*FR + 0.707*FC + 0.707*BR"'  # Downmix to stereo
        f' -filter:a "aresample=matrix_encoding=dplii"'
        f' -filter:a "dynaudnorm=maxgain=50:framelen=400:gausssize=15"'  # Dynamic audio normalization
        f' -ac 2 -c:a aac -b:a 192k'
        f' "{out_path}"'
    )
    logger.info(f'Created: {out_path}')
```
