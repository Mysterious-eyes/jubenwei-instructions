"""Build locations are provided by the portable runner, never by the current directory."""
import os
from pathlib import Path

def required(name):
    value=os.environ.get(name)
    if not value:
        raise RuntimeError('Use generate_all.py or select_training_data.py; build paths are not configured.')
    return Path(value).resolve()

SOURCE_FILE=required('JUBENWEI_BUILD_SOURCE')
OUTPUT_DIR=required('JUBENWEI_BUILD_OUTPUT')
REPORT_FILE=required('JUBENWEI_BUILD_REPORT')
REFERENCE_FILE=Path(os.environ['JUBENWEI_BUILD_REFERENCE']).resolve() if os.environ.get('JUBENWEI_BUILD_REFERENCE') else None
