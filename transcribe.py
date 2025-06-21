#!/usr/bin/env python3

import os
import subprocess
import sys
import argparse
import shlex
from pathlib import Path

MEDIA_EXTENSIONS = {'.mp3', '.mp4', '.wav', '.m4a', '.avi', '.mov'}
WHISPER_PATH = Path('/Users/alexey/projects/whisper.cpp')
WHISPER_BIN = WHISPER_PATH / 'build/bin/whisper-cli'

def find_media_file(directory: Path) -> Path | None:
    for file in directory.iterdir():
        if file.suffix.lower() in MEDIA_EXTENSIONS and file.is_file():
            return file
    return None

def preprocess_audio(src: Path) -> Path:
    processed_wav = src.with_suffix('.processed.wav')
    print(f"Preprocessing {src.name} with ffmpeg...")
    cmd = [
        'ffmpeg', '-i', src, "-y",
        '-ar', '16000', '-ac', '1',
        '-c:a', 'pcm_s16le',
        '-af', 'silenceremove=stop_periods=-1:stop_duration=1:stop_threshold=-30dB',
        processed_wav
    ]
    print(f"Running: {' '.join(shlex.quote(str(arg)) for arg in cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(f"ffmpeg error while processing {src.name}", file=sys.stderr)
        sys.exit(1)
    print(f"Generated: {processed_wav.name}")
    return processed_wav

def transcribe_with_whisper(input_file: Path, output_base: Path, model: str):
    whisper_model = WHISPER_PATH / f'models/ggml-{model}.bin'
    cmd = [
        WHISPER_BIN,
        '-m', whisper_model,
        '-f', input_file,
        '-l', 'auto',
        '-otxt', "-np", "-pc",
        '-of', output_base,
        '-et', '2.8',
        '--prompt', "Please transcribe with proper punctuation and capitalization."
    ]
    print(f"Running: {' '.join(shlex.quote(str(arg)) for arg in cmd)}")
    return subprocess.run(cmd).returncode == 0

def main():
    parser = argparse.ArgumentParser(description='Transcribe media files using Whisper')
    parser.add_argument('--model', '-m', default='medium', 
                       help='Whisper model to use (default: medium)')
    args = parser.parse_args()

    os.chdir(Path(__file__).resolve().parent)

    while True:
        media_file = find_media_file(Path('.'))
        if not media_file:
            print("No more media files found in current directory")
            break

        print(f"Processing file: {media_file.name}")
        print(f"Using model: {args.model}")
        base_name = media_file.with_suffix('')
        expected_txt = media_file.with_suffix('.txt')

        processed_input = preprocess_audio(media_file)

        success = transcribe_with_whisper(processed_input, base_name, args.model)
        if not success or not expected_txt.exists():
            print(f"Error processing file: {media_file.name}", file=sys.stderr)
            if not expected_txt.exists():
                print(f"Output file {expected_txt.name} was not created", file=sys.stderr)
            processed_input.unlink(missing_ok=True)
            sys.exit(1)

        print(f"Removing temporary file: {processed_input.name}")
        processed_input.unlink(missing_ok=True)

        print(f"Removing original file: {media_file.name}")
        media_file.unlink()

if __name__ == '__main__':
    main()
