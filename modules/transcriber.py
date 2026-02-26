"""
Transcription module.
Uses OpenAI Whisper API for speech-to-text.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from openai import OpenAI

from .config import Config


class Transcriber:
    """Transcribes audio files using OpenAI Whisper."""

    MODEL = "whisper-1"

    def __init__(self, config: Config):
        """
        Initialize transcriber.

        Args:
            config: Configuration object with OpenAI API key.
        """
        self.client = OpenAI(api_key=config.openai_api_key)

    def transcribe(self, audio_path: Path) -> str:
        """
        Transcribe a single audio file.

        Args:
            audio_path: Path to audio file (.mp3, .wav, etc.).

        Returns:
            Transcript text.
        """
        with open(audio_path, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model=self.MODEL,
                file=audio_file,
                response_format="text"
            )

        return transcript

    def transcribe_and_save(
        self,
        audio_path: Path,
        output_dir: Path
    ) -> Tuple[str, Path]:
        """
        Transcribe audio and save transcript to file.

        Args:
            audio_path: Path to audio file.
            output_dir: Directory to save transcript.

        Returns:
            Tuple of (transcript_text, transcript_path).
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        transcript = self.transcribe(audio_path)

        transcript_path = output_dir / f"{audio_path.stem}.txt"
        transcript_path.write_text(transcript, encoding="utf-8")

        return transcript, transcript_path

    def transcribe_batch(
        self,
        audio_paths: List[Path],
        output_dir: Path
    ) -> List[Tuple[str, Optional[str], Optional[Path]]]:
        """
        Transcribe multiple audio files.

        Args:
            audio_paths: List of paths to audio files.
            output_dir: Directory to save transcripts.

        Returns:
            List of (call_id, transcript_text, transcript_path) tuples.
            transcript_text and path are None if transcription failed.
        """
        import time
        results = []
        start_time = time.time()
        success_count = 0

        print(f"\n[WHISPER] Transcribing {len(audio_paths)} recordings...", flush=True)

        for i, audio_path in enumerate(audio_paths):
            call_id = audio_path.stem
            iter_start = time.time()
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            print(f"  [{i+1}/{len(audio_paths)}] {call_id} ({file_size_mb:.1f} MB)...", end=" ", flush=True)

            try:
                transcript, transcript_path = self.transcribe_and_save(
                    audio_path, output_dir
                )
                elapsed = time.time() - iter_start
                print(f"OK {len(transcript)} chars ({elapsed:.1f}s)", flush=True)
                success_count += 1
                results.append((call_id, transcript, transcript_path))
            except Exception as e:
                elapsed = time.time() - iter_start
                print(f"FAIL ({elapsed:.1f}s): {e}", flush=True)
                results.append((call_id, None, None))

            # Show ETA every 5 calls (transcription is slower)
            if (i + 1) % 5 == 0 and i + 1 < len(audio_paths):
                total_elapsed = time.time() - start_time
                avg_per_call = total_elapsed / (i + 1)
                remaining = (len(audio_paths) - i - 1) * avg_per_call
                print(f"  [TIME] Progress: {i+1}/{len(audio_paths)} | ETA: {remaining/60:.1f} min remaining", flush=True)

        total_time = time.time() - start_time
        print(f"\n[WHISPER] Done: {success_count}/{len(audio_paths)} files in {total_time/60:.1f} min", flush=True)

        return results
