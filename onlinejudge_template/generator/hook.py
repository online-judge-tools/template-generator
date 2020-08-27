import shlex
import subprocess
import sys
from logging import getLogger
from typing import *

logger = getLogger(__name__)


def _prepare_hook(*, data: Dict[str, Any]) -> None:
    data['hook'] = []


def register_filter_command(command: List[str], *, data: Dict[str, Any]) -> None:
    if not command:
        raise ValueError('command is empty')
    if data['hook']:
        raise RuntimeError('hook is already registered')
    data['hook'].extend(command)


def _execute_hook(rendered: bytes, *, data: Dict[str, Any]) -> bytes:
    """
    :raises: subprocess.CalledProcessError
    """

    if not data['hook']:
        return rendered
    logger.info('execute filter command: $ %s', ' '.join(map(shlex.quote, data['hook'])))
    return subprocess.check_output(data['hook'], input=rendered, stderr=sys.stderr)
