"""
DOCX generator — creates formatted, editable Word files for users.
Uses Node.js + docx npm package under the hood.
"""
import asyncio
import logging
import os
import sys
import tempfile
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to the JS generator script (same folder as this file's parent)
_JS_SCRIPT = Path(__file__).parent.parent / "make_resume.js"


async def generate_docx(content: str, doc_type: str = "resume") -> bytes:
    """
    Generate a formatted .docx file from plain text resume/cover letter.

    Args:
        content:  Plain text resume or cover letter from Gemini
        doc_type: "resume" or "cover"

    Returns:
        Raw bytes of the .docx file
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_generate, content, doc_type)


def _sync_generate(content: str, doc_type: str) -> bytes:
    # Write content to a temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                     delete=False, encoding='utf-8') as tf:
        tf.write(content)
        txt_path = tf.name

    out_path = txt_path.replace('.txt', '.docx')

    try:
        result = subprocess.run(
            ["node", str(_JS_SCRIPT), doc_type, txt_path, out_path],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0 or not Path(out_path).exists():
            logger.error(f"docx generation failed: {result.stderr}")
            raise RuntimeError(f"DOCX generation failed: {result.stderr or result.stdout}")

        with open(out_path, 'rb') as f:
            return f.read()

    finally:
        for p in [txt_path, out_path]:
            try:
                os.unlink(p)
            except Exception:
                pass
