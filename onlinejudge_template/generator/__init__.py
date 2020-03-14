import pathlib
from typing import *

import appdirs
import mako.lookup
import mako.template
import pkg_resources
from onlinejudge_template.types import *


def run(input_format: Optional[FormatNode], output_format: Optional[FormatNode], *, template_file: str) -> bytes:
    data: Dict[str, Any] = {
        'input': input_format,
        'output': output_format,
        'config': {},
    }
    directories = [
        str(pathlib.Path(appdirs.user_config_dir('online-judge-tools')) / 'template'),
        pkg_resources.resource_filename('onlinejudge_template_resources', 'template'),
    ]
    lookup = mako.lookup.TemplateLookup(directories=directories, input_encoding="utf-8", output_encoding="utf-8")
    template = lookup.get_template(template_file)
    return template.render(data=data)
