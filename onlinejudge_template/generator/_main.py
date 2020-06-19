import pathlib
from typing import *

import appdirs
import mako.lookup
import mako.template
import pkg_resources
from onlinejudge_template.types import *


def run(analyzed: AnalyzerResult, *, template_file: str) -> bytes:
    data: Dict[str, Any] = {
        'analyzed': analyzed,
        'config': {},
    }
    directories = [
        str(pathlib.Path(appdirs.user_config_dir('online-judge-tools')) / 'template'),
        pkg_resources.resource_filename('onlinejudge_template_resources', 'template'),
    ]
    lookup = mako.lookup.TemplateLookup(directories=directories, input_encoding="utf-8", output_encoding="utf-8")
    path = pathlib.Path(template_file)
    if path.is_absolute() and path.exists():
        with open(path, "rb") as fh:
            lookup.put_string(template_file, fh.read())
    template = lookup.get_template(template_file)
    return template.render(data=data)
