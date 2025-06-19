#!/bin/bash

# Change to the directory where the script is located
cd "$(dirname "$0")"

# Function to find media files
find_media_file() {
    find . -maxdepth 1 -type f \( -iname "*.mp3" -o -iname "*.mp4" -o -iname "*.wav" -o -iname "*.m4a" -o -iname "*.avi" -o -iname "*.mov" \) | head -n 1
}

source .venv/bin/activate

while true; do
    media_file=$(find_media_file)
    
    if [ -z "$media_file" ]; then
        echo "No more media files found in current directory"
        exit 0
    fi
    
    echo "Processing file: $media_file"

    base_name="${media_file%.*}"
    expected_txt="${base_name}.txt"
    whisper=/Users/alexey/projects/whisper.cpp
    
    # Check if the file is already WAV format
    file_extension=$(echo "$media_file" | tr '[:upper:]' '[:lower:]' | sed 's/.*\.//')
    
    if [ "$file_extension" != "wav" ]; then
        echo "Converting $media_file to WAV format..."
        wav_file="${base_name}.wav"
        ffmpeg -i "$media_file" -ar 16000 -ac 1 -c:a pcm_s16le "$wav_file"
        
        if [ $? -ne 0 ]; then
            echo "Error converting file to WAV: $media_file"
            exit 1
        fi
        
        # Use the converted WAV file for whisper processing
        whisper_input="$wav_file"
        echo "Converted to: $wav_file"
    else
        # File is already WAV, use it directly
        whisper_input="$media_file"
    fi

    #whisper --language=ru --output_format=txt --model=large --fp16=False "$media_file"
    $whisper/build/bin/whisper-cli -m $whisper/models/ggml-large-v3.bin -f "$whisper_input" -l auto -otxt
    
    if [ $? -ne 0 ] || [ ! -f "$expected_txt" ]; then
        echo "Error processing file: $media_file"
        if [ ! -f "$expected_txt" ]; then
            echo "Output file $expected_txt was not created"
        fi
        # Clean up temporary WAV file if it was created
        if [ "$file_extension" != "wav" ] && [ -f "$wav_file" ]; then
            rm "$wav_file"
        fi
        exit 1
    fi
    
    # Clean up temporary WAV file if it was created
    if [ "$file_extension" != "wav" ] && [ -f "$wav_file" ]; then
        echo "Removed temporary WAV file: $wav_file"
        rm "$wav_file"
    fi
    
    echo "Removed original file: $media_file"
    rm "$media_file"
done 
