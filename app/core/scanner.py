import yaml
import json
import os
from pathlib import Path
from typing import Dict, Any, List

RULES_FILE_PATH = Path(__file__).parent / "rules.yaml"

class ScannerResult:
    def __init__(self, risk_type: str, severity: str, explanation: str, suggested_fix: str, rule_id: str):
        self.risk_type = risk_type
        self.severity = severity
        self.explanation = explanation
        self.suggested_fix = suggested_fix
        self.rule_id = rule_id

    def to_dict(self):
        return {
            "risk_type": self.risk_type,
            "severity": self.severity,
            "explanation": self.explanation,
            "suggested_fix": self.suggested_fix,
            "rule_id": self.rule_id
        }

class StaticScanner:
    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        if not RULES_FILE_PATH.exists():
            raise FileNotFoundError(f"Rules file not found at {RULES_FILE_PATH}")
        with open(RULES_FILE_PATH, 'r') as f:
            return yaml.safe_load(f)

    def scan_config(self, config: Dict[str, Any]) -> List[ScannerResult]:
        results = []
        config_text_elements = self._extract_all_text(config)
        config_text_lower = [text.lower() for text in config_text_elements]

        # 1. Check patterns
        for rule in self.rules.get('rules', []):
            for pattern in rule.get('patterns', []):
                pattern_lower = pattern.lower()
                for text in config_text_lower:
                    if pattern_lower in text:
                        results.append(ScannerResult(
                            risk_type=rule['risk_type'],
                            severity=rule['severity'],
                            explanation=f"{rule['description']} (Matched: '{pattern}')",
                            suggested_fix=rule['suggested_fix'],
                            rule_id=rule['id']
                        ))
                        break # Only report once per rule

        # 2. Check dangerous combinations
        for combo in self.rules.get('dangerous_combinations', []):
            capabilities: List[str] = combo.get('capabilities', [])
            matched_capabilities = 0
            
            for cap in capabilities:
                cap_lower = cap.lower()
                for text in config_text_lower:
                    if cap_lower in text:
                        matched_capabilities += 1
                        break
            
            if matched_capabilities == len(capabilities) and len(capabilities) > 0:
                 results.append(ScannerResult(
                    risk_type=combo['risk_type'],
                    severity=combo['severity'],
                    explanation=combo['description'],
                    suggested_fix=combo['suggested_fix'],
                    rule_id=combo['id']
                ))

        return results

    def _extract_all_text(self, item: Any) -> List[str]:
        """Recursively extracts all strings from a JSON-like dictionary structure."""
        extracted = []
        if isinstance(item, dict):
            for k, v in item.items():
                extracted.append(str(k))
                extracted.extend(self._extract_all_text(v))
        elif isinstance(item, list):
            for i in item:
                extracted.extend(self._extract_all_text(i))
        elif isinstance(item, str):
            extracted.append(item)
        elif item is not None:
             extracted.append(str(item))
        return extracted
