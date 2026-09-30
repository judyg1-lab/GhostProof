from src.integrity import calculate_sha256, verify_integrity


original_data = b"GhostProof evidence"
recovered_data = b"GhostProof evidence"
tampered_data = b"GhostProof evidence hacked"


original_hash = calculate_sha256(original_data)
recovered_hash = calculate_sha256(recovered_data)
tampered_hash = calculate_sha256(tampered_data)


print("Original hash:")
print(original_hash)

print("\nRecovered hash:")
print(recovered_hash)

print("\nTampered hash:")
print(tampered_hash)


if verify_integrity(original_data, recovered_data):
    print("\n[PASS] Recovered evidence integrity verified")
else:
    print("\n[FAIL] Recovered evidence has been modified")


if verify_integrity(original_data, tampered_data):
    print("[FAIL] Tampered evidence was not detected")
else:
    print("[PASS] Tampered evidence successfully detected")