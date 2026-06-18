"""Compatibility CLI wrapper for the direct Ollama training report provider.

Provider behavior now lives in
services.training_report_section_direct_ollama_provider. This script remains for
existing runtime QA commands and backward-compatible imports.
"""

from __future__ import annotations

from services.training_report_section_direct_ollama_provider import *  # noqa: F403
from services.training_report_section_direct_ollama_provider import main

if __name__ == "__main__":
    main()
