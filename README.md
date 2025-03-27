# Realtime OpenAI Whisper Transcription

A real-time speech-to-text transcription tool that uses OpenAI's Whisper model to provide live transcription of audio input from your microphone. This project processes audio in small chunks to provide near real-time transcription while maintaining accuracy.

## Features

- Real-time audio recording from microphone
- Chunk-based processing for responsive output
- Smart overlap handling to prevent word duplication
- Continuous transcription output
- Uses OpenAI's Whisper model for accurate transcription

## Prerequisites

- Python 3.7 or higher
- OpenAI API key
- FFmpeg installed on your system
- Microphone connected to your computer

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd RealtimeOpenAIWhisper
```

2. Install the required Python packages:
```bash
pip install ffmpeg-python pyaudio openai
```

3. Set up your OpenAI API key as an environment variable:
```bash
# On Windows (PowerShell)
$env:OPENAI_API_KEY="your-api-key-here"

# On Linux/Mac
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

1. Run the script:
```bash
python realtime.py
```

2. Start speaking into your microphone. The transcription will appear in real-time in your terminal.

3. Press Ctrl+C to stop the recording and exit the program.

## How It Works

The program works by:

1. Recording audio from your microphone in small chunks (4 seconds each)
2. Processing each chunk through OpenAI's Whisper model
3. Handling overlapping regions between chunks to prevent word duplication
4. Displaying the transcription in real-time

### Configuration

You can modify the following parameters in `realtime.py`:

- `CHUNK_LEN_SEC`: Length of each audio chunk in seconds (default: 4)
- `CHUNK_SIZE`: Number of frames per buffer (default: 1024)
- `RATE`: Audio sampling rate (default: 16000)
- `MODEL_NAME`: OpenAI Whisper model to use (default: "whisper-1")
- `OVERLAP_SEC`: Overlap between chunks in seconds (default: 1)

## Notes

- The program requires an active internet connection to use the OpenAI API
- Transcription quality depends on audio input quality and background noise
- The Whisper model may take a few seconds to process each chunk
- Make sure your microphone is properly connected and selected as the default input device

## Troubleshooting

If you encounter issues:

1. Ensure your OpenAI API key is correctly set
2. Check if your microphone is properly connected and selected
3. Verify that FFmpeg is installed and accessible in your system PATH
4. Make sure all required Python packages are installed correctly

## License

[Your chosen license]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 