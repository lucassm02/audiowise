import argparse
import os
import subprocess
import whisper
import language_tool_python
import requests
import uuid
import warnings
import sys
import signal
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".ts", ".webm", ".m4v"}

def get_temp_dir():
    """Get or create a centralized temporary directory in the user's home directory."""
    home_dir = os.path.expanduser("~")
    temp_dir = os.path.join(home_dir, ".audiowise")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    return temp_dir

def cleanup_temp_files(temp_files):
    """Remove temporary files on process termination."""
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    print("[LOG] Arquivos temporários removidos.", flush=True)

def check_dependencies():
    """Check if FFmpeg, Whisper, and LanguageTool dependencies are available."""
    if subprocess.run(["which", "ffmpeg"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
        raise RuntimeError("FFmpeg não está instalado ou não está no PATH.")
    try:
        stderr = StringIO()
        with redirect_stderr(stderr):
            whisper.load_model("base")
    except Exception as e:
        raise RuntimeError(f"Erro ao carregar o Whisper: {e}")
    try:
        language_tool_python.LanguageTool("pt-BR")
    except Exception as e:
        raise RuntimeError(f"Erro ao inicializar o LanguageTool: {e}")

def download_video(url, download_path):
    """Download video from a URL."""
    print(f"[LOG] Baixando vídeo da URL: {url}...", flush=True)
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(download_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        print(f"[LOG] Download concluído: {download_path}", flush=True)
    else:
        raise RuntimeError(f"Erro ao baixar vídeo. Status HTTP: {response.status_code}")

def extract_audio(video_path, output_audio_path):
    """Extract audio from a video file using ffmpeg."""
    print("[LOG] Iniciando extração do áudio...", flush=True)
    try:
        subprocess.run(
            [
                'ffmpeg', '-i', video_path, '-q:a', '0', '-map', 'a', output_audio_path
            ],
            check=True,
            stdout=subprocess.DEVNULL,  # Supress standard output
            stderr=subprocess.DEVNULL   # Supress standard error
        )
        print("[LOG] Extração do áudio concluída.", flush=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Erro ao extrair áudio: {e}")

def transcribe_audio(audio_path, output_txt_path, model, tool):
    """Transcribe the audio using Whisper and save the transcript to a text file with corrections."""
    print("[LOG] Iniciando transcrição do áudio...", flush=True)
    result = model.transcribe(audio_path, fp16=False)  # Processamento em FP32 para menor uso de memória

    print(f"[LOG] Iniciando correção do texto transcrito...", flush=True)
    corrected_text = tool.correct(result['text'])

    with open(output_txt_path, 'w', encoding='utf-8') as txt_file:
        txt_file.write(corrected_text)
    print("[LOG] Transcrição corrigida salva em arquivo.", flush=True)

def convert_to_mono(input_audio, output_audio):
    """Convert audio to mono channel to reduce processing size."""
    subprocess.run(
        ['ffmpeg', '-i', input_audio, '-ac', '1', output_audio],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def process_folder(input_folder, output_folder, model, tool):
    """Process all video files in a folder."""
    print(f"[LOG] Processando pasta: {input_folder}...", flush=True)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    video_files = [
        f for f in os.listdir(input_folder)
        if os.path.isfile(os.path.join(input_folder, f)) and os.path.splitext(f)[1].lower() in SUPPORTED_VIDEO_EXTENSIONS
    ]
    temp_files = []

    for video_file in video_files:
        video_path = os.path.join(input_folder, video_file)
        output_txt_path = os.path.join(output_folder, f"{os.path.splitext(video_file)[0]}.txt")

        if os.path.exists(output_txt_path):
            print(f"[LOG] Arquivo já processado, ignorando: {output_txt_path}", flush=True)
            continue

        unique_id = uuid.uuid4().hex
        temp_dir = get_temp_dir()
        output_audio_path = os.path.join(temp_dir, f"audio_{unique_id}.mp3")
        mono_audio_path = os.path.join(temp_dir, f"mono_audio_{unique_id}.mp3")
        temp_files.extend([output_audio_path, mono_audio_path])

        try:
            print(f"[LOG] Processando arquivo: {video_file}...", flush=True)
            extract_audio(video_path, output_audio_path)
            convert_to_mono(output_audio_path, mono_audio_path)
            transcribe_audio(mono_audio_path, output_txt_path, model, tool)
            os.remove(output_audio_path)
            os.remove(mono_audio_path)
            print(f"[LOG] Processamento concluído para: {video_file}", flush=True)
        except Exception as e:
            print(f"Erro ao processar {video_file}: {e}", flush=True)
            cleanup_temp_files(temp_files)

def main():
    parser = argparse.ArgumentParser(description="CLI para extrair áudio de um vídeo e gerar a transcrição corrigida de falas.")
    parser.add_argument('-i', '--input', type=str, required=True, help="Caminho ou URL do vídeo de entrada, ou pasta contendo vídeos.")
    parser.add_argument('-o', '--output', type=str, required=True, help="Caminho de saída para o arquivo de transcrição ou pasta de saída.")
    parser.add_argument('-m', '--model', type=str, default="base", choices=["tiny", "base", "small", "medium", "large"], help="Tamanho do modelo Whisper a ser utilizado (default: base).")
    parser.add_argument('-l', '--language', type=str, default="pt-BR", help="Idioma para correção gramatical (default: pt-BR).")
    args = parser.parse_args()

    video_path = args.input
    output_path = args.output
    model_size = args.model
    language = args.language

    temp_files = []

    def handle_exit(signum, frame):
        print("[LOG] Interrupção detectada. Limpando recursos...", flush=True)
        cleanup_temp_files(temp_files)
        sys.exit(1)

    signal.signal(signal.SIGINT, handle_exit)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, handle_exit)  # Handle system termination

    try:
        check_dependencies()
        model = whisper.load_model(model_size)  # Carregar modelo uma vez para reutilização
        tool = language_tool_python.LanguageTool(language)  # Criar instância única para correções

        if os.path.isdir(video_path):
            process_folder(video_path, output_path, model, tool)
        else:
            if not os.path.exists(video_path):
                print(f"Erro: O arquivo de entrada '{video_path}' não existe.", flush=True)
                return

            if os.path.isdir(output_path):
                output_path = os.path.join(output_path, f"{os.path.splitext(os.path.basename(video_path))[0]}.txt")

            if os.path.exists(output_path):
                print(f"[LOG] Arquivo já processado, ignorando: {output_path}", flush=True)
                return

            unique_id = uuid.uuid4().hex
            temp_dir = get_temp_dir()
            temp_video_path = os.path.join(temp_dir, f"video_{unique_id}.mp4") if video_path.startswith("http") else video_path
            output_audio_path = os.path.join(temp_dir, f"audio_{unique_id}.mp3")
            mono_audio_path = os.path.join(temp_dir, f"mono_audio_{unique_id}.mp3")
            temp_files.extend([output_audio_path, mono_audio_path])

            try:
                print("[LOG] Processo iniciado.", flush=True)
                if video_path.startswith("http"):
                    download_video(video_path, temp_video_path)

                extract_audio(temp_video_path, output_audio_path)
                convert_to_mono(output_audio_path, mono_audio_path)
                transcribe_audio(mono_audio_path, output_path, model, tool)
                os.remove(output_audio_path)
                os.remove(mono_audio_path)
                if video_path.startswith("http"):
                    os.remove(temp_video_path)
                print("[LOG] Processo concluído com sucesso.", flush=True)
                print(f"[LOG] Arquivo de saída: {output_path}", flush=True)
            except Exception as e:
                print(f"Erro durante o processo: {e}", flush=True)
    except Exception as e:
        print(f"Erro fatal: {e}", flush=True)

if __name__ == "__main__":
    main()
