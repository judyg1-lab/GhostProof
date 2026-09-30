from src.crypto import generate_key
from src.secret_sharing import (
    split_secret,
    recover_secret
)


original_key = generate_key()

print("Original AES key:")
print(original_key.hex())


shares = split_secret(
    original_key,
    threshold=3,
    num_shares=5
)


print("\nGenerated shares:")

for x, y in shares:
    print(
        f"Share {x}: {hex(y)[:60]}..."
    )


# 任意選 3 份
selected_shares = [
    shares[0],
    shares[2],
    shares[4]
]


print("\nSelected shares:")
print([x for x, _ in selected_shares])


recovered_key = recover_secret(
    selected_shares,
    threshold=3,
    secret_length=32
)


print("\nRecovered AES key:")
print(recovered_key.hex())


if recovered_key == original_key:
    print(
        "\n[PASS] AES key recovered successfully "
        "from 3-of-5 shares"
    )
else:
    print(
        "\n[FAIL] Recovered AES key does not match"
    )


# 測試只有 2 份
insufficient_shares = [
    shares[0],
    shares[1]
]

try:

    recover_secret(
        insufficient_shares,
        threshold=3,
        secret_length=32
    )

    print(
        "[FAIL] 2 shares unexpectedly passed "
        "the threshold check"
    )

except ValueError as e:

    print(
        "[PASS] 2 shares cannot reconstruct "
        "the original AES key"
    )

    print(
        f"       Reason: {e}"
    )