import pytest
from app.core.integrity import generate_canonical_hash, verify_integrity

def test_canonical_hash_consistency():
    config1 = {"a": 1, "b": 2, "c": {"d": 3}}
    config2 = {"b": 2, "c": {"d": 3}, "a": 1}
    
    hash1 = generate_canonical_hash(config1)
    hash2 = generate_canonical_hash(config2)
    
    assert hash1 == hash2

def test_verify_integrity():
    config = {"a": 1, "b": 2}
    expected_hash = generate_canonical_hash(config)
    
    assert verify_integrity(config, expected_hash) == True
    
    # Modify config
    config["a"] = 99
    assert verify_integrity(config, expected_hash) == False
