"""
DOCX generator — calls make_resume.js using the local node_modules/docx package.
Reliable on Railway because it uses npm install (not npm install -g).
"""
import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

_BASE = Path(__file__).resolve().parent.parent      # project root
_JS   = _BASE / 'make_resume.js'
_NM   = _BASE / 'node_modules' / 'docx'            # local install


def _node_bin() -> str:
    node = shutil.which('node') or shutil.which('nodejs')
    if node:
        return node
    for p in ['/usr/bin/node', '/usr/local/bin/node']:
        if Path(p).exists():
            return p
    raise RuntimeError('node binary not found on PATH')


def _check_prereqs():
    if not _JS.exists():
        raise FileNotFoundError(f'make_resume.js not found at {_JS}')
    if not _NM.exists():
        raise FileNotFoundError(
            f'node_modules/docx not found at {_NM}. '
            'Make sure nixpacks.toml runs "npm install" during build.'
        )


def _sync_generate(content: str, doc_type: str) -> bytes:
    _check_prereqs()
    node = _node_bin()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                     delete=False, encoding='utf-8') as tf:
        tf.write(content)
        txt_path = Path(tf.name)

    out_path = txt_path.with_suffix('.docx')

    try:
        result = subprocess.run(
            [node, str(_JS), doc_type, str(txt_path), str(out_path)],
            capture_output=True, text=True, timeout=60,
            cwd=str(_BASE),          # run from project root so require() finds node_modules
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if stdout:
            logger.info(f'Node: {stdout}')
        if stderr:
            logger.warning(f'Node stderr: {stderr}')

        if result.returncode != 0:
            raise RuntimeError(f'Node exited {result.returncode}: {stderr or stdout}')

        if not out_path.exists():
            raise RuntimeError('Output .docx was not created')

        size = out_path.stat().st_size
        if size < 200:
            raise RuntimeError(f'Output .docx too small ({size} bytes) — generation failed')

        logger.info(f'DOCX generated OK: {size} bytes')
        return out_path.read_bytes()

    finally:
        txt_path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)


async def generate_docx(content: str, doc_type: str = 'resume') -> bytes:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_generate, content, doc_type)
