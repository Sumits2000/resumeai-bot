"""
DOCX generator — creates formatted, editable Word files for users.
Uses Node.js + docx npm package under the hood.
"""
import asyncio
import logging
import os
import tempfile
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Locate make_resume.js — works both locally and on Railway
_BASE_DIR = Path(__file__).resolve().parent.parent
_JS_SCRIPT = _BASE_DIR / "make_resume.js"


def _find_node() -> str:
    """Find the node binary — handles different Railway/local paths."""
    for candidate in ["node", "/usr/bin/node", "/usr/local/bin/node", "/nix/store/*/bin/node"]:
        try:
            result = subprocess.run([candidate, "--version"],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return candidate
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    # Last resort — search PATH
    import shutil
    node = shutil.which("node")
    if node:
        return node
    raise RuntimeError("node not found. Make sure nixpacks.toml includes nodejs_20.")


def _find_docx_module() -> str | None:
    """Find globally installed docx npm module."""
    for candidate in [
        "/usr/local/lib/node_modules/docx",
        "/usr/lib/node_modules/docx",
        "/root/.npm-global/lib/node_modules/docx",
        "/home/claude/.npm-global/lib/node_modules/docx",
    ]:
        if Path(candidate).exists():
            return candidate
    # Try node to find it
    try:
        node = _find_node()
        result = subprocess.run(
            [node, "-e", "console.log(require.resolve('docx'))"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return str(Path(result.stdout.strip()).parent.parent)
    except Exception:
        pass
    return None


async def generate_docx(content: str, doc_type: str = "resume") -> bytes:
    """
    Generate a formatted .docx from plain text resume/cover letter.
    Returns raw bytes of the .docx file.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_generate, content, doc_type)


def _sync_generate(content: str, doc_type: str) -> bytes:
    # Write content to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                     delete=False, encoding='utf-8') as tf:
        tf.write(content)
        txt_path = tf.name

    out_path = txt_path.replace('.txt', '.docx')

    try:
        node = _find_node()
        js_path = str(_JS_SCRIPT)

        if not Path(js_path).exists():
            raise FileNotFoundError(f"make_resume.js not found at {js_path}")

        logger.info(f"Running: {node} {js_path} {doc_type}")

        env = os.environ.copy()

        # Help Node find the docx module if installed globally
        docx_path = _find_docx_module()
        if docx_path:
            node_path = str(Path(docx_path).parent)
            existing = env.get("NODE_PATH", "")
            env["NODE_PATH"] = f"{node_path}:{existing}" if existing else node_path

        result = subprocess.run(
            [node, js_path, doc_type, txt_path, out_path],
            capture_output=True, text=True, timeout=45, env=env
        )

        logger.info(f"Node stdout: {result.stdout.strip()}")
        if result.stderr:
            logger.warning(f"Node stderr: {result.stderr.strip()}")

        if result.returncode != 0:
            raise RuntimeError(f"Node exited {result.returncode}: {result.stderr or result.stdout}")

        if not Path(out_path).exists():
            raise RuntimeError("DOCX file was not created by Node script.")

        with open(out_path, 'rb') as f:
            data = f.read()

        if len(data) < 100:
            raise RuntimeError("DOCX file is too small — generation may have failed.")

        return data

    finally:
        for p in [txt_path, out_path]:
            try:
                os.unlink(p)
            except Exception:
                pass
