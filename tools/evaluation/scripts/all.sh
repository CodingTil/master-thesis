#!/bin/bash
set -e

python general.py
python general.py --slides
python bound_stats.py
python bound_stats.py --slides
