# src/utils/llm.py
import subprocess
import tempfile
import os
from typing import Optional, Tuple

def _run_proc(cmd, input_text: Optional[str] = None, timeout: int = 60) -> Tuple[int, str, str]:
    """
    Run subprocess and return (returncode, stdout, stderr).
    Uses text mode with explicit UTF-8 decoding and 'replace' for errors so it won't crash on non-CP1252 bytes on Windows.
    """
    try:
        proc = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",    # force utf-8 decoding
            errors="replace",    # replace undecodable bytes instead of raising
            timeout=timeout
        )
        stdout = proc.stdout if proc.stdout is not None else ""
        stderr = proc.stderr if proc.stderr is not None else ""
        return proc.returncode, stdout.strip(), stderr.strip()
    except FileNotFoundError:
        raise RuntimeError("ollama CLI not found. Make sure `ollama` is installed and in PATH.")
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"ollama call timed out after {timeout}s") from e
    except Exception as e:
        # convert any unexpected error into a clear RuntimeError
        raise RuntimeError(f"Error running subprocess: {e}") from e

def call_ollama(prompt: str, model: str = 'llama3.2:3b', timeout: int = 60) -> str:
    """
    Robust wrapper to call Ollama CLI with multiple invocation strategies.
    Tries:
      1) `ollama run <model>` with prompt passed in stdin
      2) `ollama run <model> --prompt "<prompt>"`
      3) write prompt to a temp file and call `ollama run <model> --prompt-file <file>`

    Returns model output (stdout) or raises RuntimeError with helpful stderr.
    """
    if not prompt:
        return ''

    last_err = None

    # Strategy 1: run and pass prompt via stdin (works on many versions)
    cmd1 = ['ollama', 'run', model]
    rc, out, err = _run_proc(cmd1, input_text=prompt, timeout=timeout)
    if rc == 0 and out:
        return out
    last_err = f"rc={rc}, stderr={err}"

    # Strategy 2: pass prompt as --prompt argument
    try:
        cmd2 = ['ollama', 'run', model, '--prompt', prompt]
        rc, out, err = _run_proc(cmd2, input_text=None, timeout=timeout)
        if rc == 0 and out:
            return out
        last_err = f"rc={rc}, stderr={err}"
    except Exception:
        # continue to next strategy
        pass

    # Strategy 3: write prompt to a temp file and use --prompt-file (if supported)
    try:
        with tempfile.NamedTemporaryFile('w+', delete=False, encoding='utf-8', suffix='.txt') as tf:
            tf.write(prompt)
            tf.flush()
            tmp_path = tf.name
        cmd3 = ['ollama', 'run', model, '--prompt-file', tmp_path]
        rc, out, err = _run_proc(cmd3, input_text=None, timeout=timeout)
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        if rc == 0 and out:
            return out
        last_err = f"rc={rc}, stderr={err}"
    except Exception:
        # ignore and fall through
        pass

    # If we reach here, all strategies failed. Raise informative error.
    help_msg = (
        "Failed to call ollama with the tried invocation methods.\n"
        "Last error: " + str(last_err) + "\n\n"
        "Suggestions:\n"
        " - Run `ollama run --help` locally to inspect supported flags for your version.\n"
        " - Try `ollama run <model>` in a terminal and paste a short prompt to see expected behavior.\n"
        " - If your Ollama supports a different flag, edit src/utils/llm.py to add that strategy.\n"
    )
    raise RuntimeError(help_msg)


def safe_summarize(text: str, model: str = 'llama3.2:3b', max_sentences: int = 3) -> str:
    """
    A small helper to produce concise summaries from LLM.
    If the LLM call fails, returns a short truncated fallback summary.
    """
    if not text:
        return ''
    # Keep prompt short to reduce token usage and avoid long outputs
    prompt = (
        "You are a concise summarizer. Summarize the following text in "
        f"{max_sentences} short sentences and then give 3 bullet takeaways.\n\n"
        f"Text:\n{text}\n\nSummary:"
    )
    try:
        out = call_ollama(prompt, model=model, timeout=60)
        # If the model echoes the input and doesn't give a summary, be defensive:
        if not out or len(out.strip()) < 10:
            return (text[:200] + '...') if len(text) > 200 else text
        return out.strip()
    except Exception:
        # fallback: keep a short snippet of the input as a minimal summary
        try:
            snippet = text.strip().replace("\\n", " ")
            snippet = snippet[:240] + ("..." if len(snippet) > 240 else "")
            return snippet
        except Exception:
            return ""
