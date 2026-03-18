import re
import subprocess
from functools import lru_cache
from pathlib import Path
from tempfile import NamedTemporaryFile

from faster_whisper import WhisperModel

BASE_DIR = Path(__file__).resolve().parent
TRANSCRIPTS_DIR = BASE_DIR / "transcripts"
TRANSCRIPT_FILE = TRANSCRIPTS_DIR / "meeting.txt"
MODEL_SIZE = "base"


@lru_cache(maxsize=1)
def get_whisper_model() -> WhisperModel:
    try:
        return WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    except Exception as exc:
        raise RuntimeError(
            "Whisper model initialization failed. Verify faster-whisper dependencies and model download setup."
        ) from exc


def _clean_whisper_artifacts(text: str) -> str:
    """Remove common Whisper hallucinations and artifacts."""
    artifacts = [
        r"\[music\]",
        r"\[applause\]",
        r"\[laughter\]",
        r"\[inaudible\]",
        r"\[silence\]",
        r"\[noise\]",
        r"\[background noise\]",
        r"♪.*?♪",
        r"\(music\)",
        r"\(applause\)",
        r"\(laughter\)",
    ]
    
    cleaned = text
    for pattern in artifacts:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _post_process_transcript(text: str) -> str:
    """Apply post-processing to improve transcript quality."""
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)
    
    text = re.sub(r"([.!?])\s*([a-z])", lambda m: f"{m.group(1)} {m.group(2).upper()}", text)
    
    text = re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)
    
    text = re.sub(r"\s+", " ", text).strip()
    
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    
    return text


def append_transcript_text(text: str) -> None:
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPT_FILE.touch(exist_ok=True)

    with TRANSCRIPT_FILE.open("a", encoding="utf-8") as transcript_file:
        transcript_file.write(f"{text}\n")


def convert_audio_for_transcription(audio_path: Path) -> Path:
    """Convert audio to optimal format for Whisper transcription."""
    with NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        converted_path = Path(temp_file.name)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(audio_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-af",
        "highpass=f=200,lowpass=f=3000,volume=1.5",
        "-acodec",
        "pcm_s16le",
        str(converted_path),
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        converted_path.unlink(missing_ok=True)
        stderr = (result.stderr or "").strip()
        raise RuntimeError(
            "Audio transcription failed. ffmpeg could not decode the uploaded recording. "
            f"ffmpeg error: {stderr or 'Unknown ffmpeg error.'}"
        )

    return converted_path


def transcribe_audio(audio_path: Path) -> str:
    model = get_whisper_model()
    converted_path = convert_audio_for_transcription(audio_path)

    try:
        segments, info = model.transcribe(
            str(converted_path),
            beam_size=5,
            best_of=5,
            temperature=0.0,
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": 500,
                "speech_pad_ms": 400,
            },
            condition_on_previous_text=True,
            without_timestamps=False,
            word_timestamps=False,
            language=None,
        )
    except Exception as exc:
        raise RuntimeError(
            "Audio transcription failed after ffmpeg conversion. Verify the recording contains valid audio."
        ) from exc
    finally:
        converted_path.unlink(missing_ok=True)

    segments_list = list(segments)
    
    if not segments_list:
        transcript = "[No speech detected in audio chunk]"
        append_transcript_text(transcript)
        return transcript
    
    detected_language = info.language if hasattr(info, 'language') else "unknown"
    language_probability = info.language_probability if hasattr(info, 'language_probability') else 0.0
    
    cleaned_segments = []
    for segment in segments_list:
        text = segment.text.strip()
        if not text:
            continue
        
        text = _clean_whisper_artifacts(text)
        
        if segment.no_speech_prob < 0.6 and text:
            cleaned_segments.append(text)
    
    if not cleaned_segments:
        transcript = "[No speech detected in audio chunk]"
    else:
        transcript = " ".join(cleaned_segments)
        transcript = _post_process_transcript(transcript)
    
    metadata = f"[lang:{detected_language}|conf:{language_probability:.2f}]"
    append_transcript_text(f"{metadata} {transcript}")
    
    return transcript
