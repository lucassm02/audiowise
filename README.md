# AudioWise CLI - Audio Transcription Tool

AudioWise is a command-line interface (CLI) tool for extracting audio from video files, transcribing the audio using the Whisper model, and correcting the text using the LanguageTool library. It supports individual video files or folders containing multiple files.

## Prerequisites

Ensure the following prerequisites are met before using AudioWise:

1. **Python 3.8 or higher** - [Download Python here](https://www.python.org/downloads/).
2. **FFmpeg** - Required for audio extraction.
   - Install on Linux: `sudo apt install ffmpeg`
   - Install on macOS: `brew install ffmpeg`
   - For Windows, download from [ffmpeg.org](https://ffmpeg.org/).
3. **Required Python libraries:**
   - Install dependencies using:
     ```bash
     pip install -r requirements.txt
     ```

## Installation

Clone the repository or copy the files to your machine:
```bash
git clone https://github.com/your-username/audiowise-cli.git
cd audiowise-cli
```

Ensure the main script is executable:
```bash
chmod +x main.py
```

## Usage

### Basic Commands

The general syntax for AudioWise CLI is:
```bash
python main.py -i <input> -o <output> [options]
```

### Arguments

- `-i` or `--input`: Path to the input video or a folder containing video files.
- `-o` or `--output`: Path to the output file or folder where the transcription will be saved.
- `-m` or `--model`: Whisper model to use. Available options: `tiny`, `base`, `small`, `medium`, `large` (default: `base`).
- `-l` or `--language`: Language for grammatical correction (default: `pt-BR`).

### Examples

#### Transcribe a single video file:
```bash
python main.py -i video.mp4 -o transcription.txt -m small -l pt-BR
```

#### Process all videos in a folder:
```bash
python main.py -i ./videos -o ./transcriptions -m base -l en-US
```

#### Download and process a video from a URL:
```bash
python main.py -i https://example.com/video.mp4 -o transcription.txt -m tiny -l es
```

### Logs

- Process logs are displayed directly in the terminal so you can monitor the progress of each step.
- Already processed files are skipped, and a warning is logged.

### Interruptions

- When pressing `Ctrl+C` or if the system terminates the process, the script automatically cleans up all temporary files created during execution.

## Features

- **Audio Extraction**: Converts video audio to mono for better performance.
- **Transcription with Whisper**: Uses machine learning models to transcribe audio.
- **Correction with LanguageTool**: Corrects grammar and spelling in the specified language.
- **Chunk Processing**: Ensures better memory management.
- **Supports Multiple Formats**: Compatible with popular extensions such as `.mp4`, `.mkv`, `.avi`, and more.

## Common Issues

### `FFmpeg not installed or not in PATH`
Ensure FFmpeg is installed and accessible from the terminal.

### `Error loading Whisper`
Verify all Whisper dependencies are installed correctly. Use:
```bash
pip install -r requirements.txt
```

### `LanguageTool failed to initialize`
Verify that the language specified with the `-l` argument is supported.

## Contributing

Feel free to submit issues and pull requests to the official repository.

## License

This project is licensed under the [MIT License](LICENSE).

