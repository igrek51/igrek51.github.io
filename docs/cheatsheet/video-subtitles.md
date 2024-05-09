# Video Subtitles
This explains how to add subtitles to the video files.

Prepare by installing: `sudo apt install qnapi uchardet ffmpeg recode`

## Download subtitles for your language
```sh
qnapi -l pl *.mp4
```

## Detect encoding
```sh
uchardet *.txt
```
Expect `UTF-8`, `Windows-1250` or `UTF-16`.

## Verify that converted encoding is actually fine 
```sh
cat S01E03.txt | recode cp1250..utf8
cat S01E03.txt | recode utf16..utf8
```

## Recode to UTF8
```sh
recode cp1250..utf8 *.txt
# or
recode utf16..utf8 *.txt
```

## Convert to SRT
Convert TXT to SRT, add `.default.srt` suffix for Jellyfin:
```sh
ffmpeg -i 'S01E03.txt' 'S01E03.default.srt'
```

## Appendix
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
