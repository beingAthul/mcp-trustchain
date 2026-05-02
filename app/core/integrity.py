import json
import hashlib
from typing import Dict, Any

def generate_canonical_hash(config: Dict[str, Any]) -> str:
    """
    Generates a SHA-256 hash of a JSON configuration using canonical formatting.
    Canonical formatting ensures that the same JSON object always produces the same string
    representation: sorted keys, no whitespace around separators.
    """
    canonical_string = json.dumps(
        config,
        sort_keys=True,
        ensure_ascii=False,
        separators=(',', ':')
    )
    return hashlib.sha256(canonical_string.encode('utf-8')).hexdigest()

def verify_integrity(config: Dict[str, Any], expected_hash: str) -> bool:
    """
    Verifies if a given configuration matches the expected canonical hash.
    """
    current_hash = generate_canonical_hash(config)
    return current_hash == expected_hash
