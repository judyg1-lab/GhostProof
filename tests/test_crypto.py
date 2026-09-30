from src.crypto import generate_key, encrypt_data, decrypt_data


original_data = b"GhostProof test evidence"

print("Original:")
print(original_data)

key = generate_key()

nonce, encrypted_data = encrypt_data(
    original_data,
    key
)

print("\nEncrypted:")
print(encrypted_data)

recovered_data = decrypt_data(
    encrypted_data,
    key,
    nonce
)

print("\nRecovered:")
print(recovered_data)

if original_data == recovered_data:
    print("\n[PASS] Encryption / Decryption successful")
else:
    print("\n[FAIL] Recovered data does not match")