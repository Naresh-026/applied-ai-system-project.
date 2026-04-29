import logging
import json
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "ai_agent.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("ai_code_analyst")

DANGEROUS_PATTERNS = [
    "subprocess", "os.system", "eval(", "exec(",
    "__import__", "shutil.rmtree", "os.remove", "open(",
]


def check_guardrails(code: str) -> tuple[bool, str]:
    """Return (is_safe, reason). Blocks dangerous or oversized inputs."""
    if len(code.strip()) < 10:
        return False, "Please provide at least a few lines of code to analyze."
    if len(code) > 5000:
        return False, "Code exceeds 5,000 characters. Submit a smaller snippet."
    for pattern in DANGEROUS_PATTERNS:
        if pattern in code:
            return False, (
                f"Guardrail triggered: code contains `{pattern}`. "
                "Only analyze safe, non-destructive Python snippets."
            )
    return True, ""


def log_analysis(code_snippet: str, result: dict) -> None:
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "code_chars": len(code_snippet),
        "bugs_found": len(result.get("bugs", [])),
        "confidence": result.get("confidence", 0),
        "error": result.get("error", ""),
    }
    logger.info("analysis | " + json.dumps(entry))
