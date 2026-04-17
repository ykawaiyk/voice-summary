"""
recordings/ 内の音声ファイルを並列で文字起こしし、transcripts/ に保存する
対応形式: mp3, m4a, wav, flac, ogg, mp4, aac, wma
"""
from pathlib import Path
from faster_whisper import WhisperModel
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import sys

AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".flac", ".ogg", ".mp4", ".aac", ".wma"}
RECORDINGS_DIR = Path("recordings")
TRANSCRIPTS_DIR = Path("transcripts")

# モデルサイズ: tiny / base / small / medium / large-v3
MODEL_SIZE = "small"

# 並列数: CPUコア数に応じて調整（RAMが少ない場合は2に下げる）
MAX_WORKERS = 3

# スレッドごとに独立したモデルインスタンスを保持
_thread_local = threading.local()
_print_lock = threading.Lock()


def get_model() -> WhisperModel:
    if not hasattr(_thread_local, "model"):
        _thread_local.model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    return _thread_local.model


def safe_print(msg: str) -> None:
    with _print_lock:
        print(msg)


def process_file(audio_path: Path) -> tuple[str, bool, str]:
    """1ファイルを文字起こしして保存。(ファイル名, 成功か, メッセージ) を返す"""
    output_path = TRANSCRIPTS_DIR / f"{audio_path.stem}.txt"

    if output_path.exists():
        return audio_path.name, True, "スキップ（既に存在）"

    try:
        model = get_model()
        safe_print(f"  [開始] {audio_path.name}")

        segments, info = model.transcribe(
            str(audio_path),
            language="ja",
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        lines = []
        lines.append(f"# {audio_path.stem}")
        lines.append(f"検出言語: {info.language} (確信度: {info.language_probability:.2f})")
        lines.append(f"音声時間: {info.duration:.1f}秒")
        lines.append("")
        lines.append("---")
        lines.append("")

        for seg in segments:
            start_min = int(seg.start // 60)
            start_sec = int(seg.start % 60)
            lines.append(f"[{start_min:02d}:{start_sec:02d}] {seg.text.strip()}")

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return audio_path.name, True, f"完了 → {output_path}"

    except Exception as e:
        return audio_path.name, False, f"エラー: {e}"


def main() -> None:
    TRANSCRIPTS_DIR.mkdir(exist_ok=True)

    if not RECORDINGS_DIR.exists():
        print(f"エラー: {RECORDINGS_DIR} が見つかりません")
        sys.exit(1)

    audio_files = [
        p for p in RECORDINGS_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS
    ]

    if not audio_files:
        print(f"{RECORDINGS_DIR} に音声ファイルが見つかりません")
        return

    workers = min(MAX_WORKERS, len(audio_files))
    print(f"対象ファイル: {len(audio_files)}件 / 並列数: {workers}")
    print(f"モデル: {MODEL_SIZE} (初回はダウンロードに数分かかります)\n")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_file, f): f for f in audio_files}
        done = 0
        for future in as_completed(futures):
            done += 1
            name, ok, msg = future.result()
            status = "OK" if ok else "NG"
            safe_print(f"  [{done}/{len(audio_files)}] [{status}] {name}: {msg}")

    print("\n全ファイル処理完了")


if __name__ == "__main__":
    main()
