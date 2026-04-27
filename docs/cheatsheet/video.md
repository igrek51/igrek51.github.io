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

### Verify that converted encoding is right 
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
pip3 install --upgrade yt-dlp --break-system-packages
yt-dlp -f 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' URL
# Or (newer):
yt-dlp -f "bestvideo[height<=1080]+bestaudio/best" --merge-output-format mp4 --no-playlist --remote-components ejs:github URL
# Download MP4 with normalized audio
yt-dlp -f 'bestvideo[height<=1080]+bestaudio/best' \
  --merge-output-format mp4 \
  --no-playlist --remote-components ejs:github \
  --postprocessor-args "Merger:-filter:a 'pan=stereo|FL < 1.0*FL + 0.707*FC + 0.707*BL|FR < 1.0*FR + 0.707*FC + 0.707*BR,aresample=matrix_encoding=dplii,dynaudnorm=maxgain=50:framelen=400:gausssize=15' -c:v copy -c:a aac -ac 2" \
  -o "{target}" \
  "{yt_url}"
```

## Download YouTube video as normalized MP3
```sh
pip3 install --upgrade yt-dlp --break-system-packages
# Download MP3 with normalized audio
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  --no-playlist --remote-components ejs:github \
  --postprocessor-args "ExtractAudio:-filter:a 'dynaudnorm=maxgain=50:framelen=400:gausssize=15'" \
  -o "{target}.mp3" \
  "{yt_url}"
```

## Dynamic Audio Normalizer / Night Mode / Dynamic range compression
This allows for applying extra gain to the "quiet" sections of the audio while avoiding distortions
or clipping the "loud" sections.
In other words: The Dynamic Audio Normalizer will "even out" the volume of quiet and loud sections,
in the sense that the volume of each section is brought to the same target level.
```sh
ffmpeg -i "$INPUT.mkv" -c:v copy -af "dynaudnorm=maxgain=50:framelen=400:gausssize=15" -c:a aac -b:a 192k "$INPUT.norm.mkv"
```
```sh
ls -1 *.mkv | sed -e 's/\.mkv$//g' | xargs -d '\n' -I %s echo 'ffmpeg -i "%s.mkv" -c:v copy -af "dynaudnorm=maxgain=50:framelen=400:gausssize=15" -c:a aac -b:a 192k "%s.norm.mkv"'
ls -1 *.mp4 | sed -e 's/\.mp4$//g' | xargs -d '\n' -I %s echo 'ffmpeg -i "%s.mp4" -c:v copy -af "dynaudnorm=maxgain=50:framelen=400:gausssize=15" -c:a aac -b:a 192k "%s.norm.mp4"'
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

## nukefile.py
Python script executing commands for batch of files:
```python
#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "nuclear>=2.8.1",
# ]
# ///
from pathlib import Path
from nuclear import nuke, logger

class Config:
    dry: bool = False
    sources: list[tuple] = [
        ('NUM', 'YT_URL', 'TITLE'),
    ]

config, sh = nuke.init(Config)

def mkv_to_mp3():
    sources: list[Path] = list(Path('.').glob('*.mkv'))
    for file in sources:
        """
        map 0:a:1 - From input #0 select audio stream index #1 (second)
        pan=stereo - downmix 5.1 to stereo
        aresample=matrix_encoding=dplii - Dolby Pro Logic II matrix
        dynaudnorm - Dynamic Audio Normalizer
        -ac 2 -q:a 0 - output 2 channels, variable bitrate
        """
        target = f'{file.stem}.mp3'
        if Path(target).exists():
            logger.debug(f'{target} already exists - skipping')
            continue
        cmd = f'''ffmpeg -i "{f.absolute()}"
    -map 0:a:1
    -filter:a "pan=stereo|FL < 1.0*FL + 0.707*FC + 0.707*BL|FR < 1.0*FR + 0.707*FC + 0.707*BR,
    aresample=matrix_encoding=dplii,
    dynaudnorm=maxgain=50:framelen=400:gausssize=15"
    -ac 2 -q:a 0
    "{target}"'''.replace('\n', '')
        sh<<cmd

def yt_to_mp3():
    for id, yt_url, title in config.sources:
        target = f'{id} {title}.mp4'
        if Path(target).exists():
            logger.debug('target already exists - skipping', target=target)
            continue
        sh<<f'''yt-dlp -f 'bestvideo[height<=1080]+bestaudio/best' \
--merge-output-format mp4 \
--no-playlist --remote-components ejs:github \
--postprocessor-args "Merger:-filter:a 'pan=stereo|FL < 1.0*FL + 0.707*FC + 0.707*BL|FR < 1.0*FR + 0.707*FC + 0.707*BR,aresample=matrix_encoding=dplii,dynaudnorm=maxgain=50:framelen=400:gausssize=15' -c:v copy -c:a aac -ac 2" \
-o "{target}" \
"{yt_url}"'''

if __name__ == '__main__':
    nuke.run()
```

## Split video into chunks
```python
#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "nuclear>=2.8.1",
# ]
# ///
from pathlib import Path
from nuclear import shell, logger

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

## MKV to audiobook generator
```python
#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "nuclear>=2.8.1",
#   "unidecode",
# ]
# ///
from pathlib import Path
from nuclear import nuke, logger
from unidecode import unidecode

class Config:
    dry: bool = False
    bluey_sources: list[str] = [
        '/opt/dump/movies-series/Bluey/S01/S01E22 Bluey - Podaj Paczkę.mkv',
    ]
    bluey_offset: int = 200

config: Config = nuke.load_config(Config)
sh = nuke.sh(raw_output=True, print_log=True, dry=config.dry)

def push():
    sh << "rsync -avh --delete --size-only --info=progress2 '/opt/dump/alilo/custom/' '/media/igrek/USB DRIVE/CUSTOM/'"
    sh << "rsync -avh --delete --size-only --info=progress2 '/opt/dump/alilo/storytales/' '/media/igrek/USB DRIVE/STORY/'"

def fatsort():
    sh<<"sync"
    sh<<"sudo fdisk -l"
    partition = '/dev/sda1'
    input(f"\nPresss enter to confirm writing to partition {partition}...")
    try:
        sh<<f"umount {partition}"
    except CommandError:
        pass
    sh<<f"sudo fsck.vfat -r {partition}"
    sh<<f"sudo fatsort -n {partition}"

def bluey():
    sources: list[Path] = nuke.validate_sources(config.bluey_sources)
    for i, f in enumerate(sources):
        filename = unidecode(f.stem[7:])
        target = f'storytales/{config.bluey_offset + i} {filename}.mp3'
        if Path(target).exists():
            logger.debug('target already exists - skipping', target=target)
            continue
        sh(
            f'ffmpeg -i "{f.absolute()}"'
            f' -map 0:a:1'  # From input #0 select audio stream index #1 (second)
            f' -ss 00:00:25'
            f' -filter:a "pan=stereo|FL < 1.0*FL + 0.707*FC + 0.707*BL|FR < 1.0*FR + 0.707*FC + 0.707*BR,'  # downmix 5.1 to stereo
            f'aresample=matrix_encoding=dplii,'  # Dolby Pro Logic II matrix
            f'dynaudnorm=maxgain=50:framelen=400:gausssize=15"'  # Dynamic Audio Normalizer
            f' -ac 2 -q:a 0'  # output 2 channels, variable bitrate
            f' "{target}"'
        )

if __name__ == '__main__':
    nuke.run()
```
