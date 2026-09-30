from src.erasure import (
    encode_shards,
    decode_shards,
    DATA_SHARDS,
    TOTAL_SHARDS
)


original_data = (
    b"GhostProof real 8-of-12 "
    b"erasure coding recovery test."
)


print("====================================")
print("GhostProof Erasure Coding Test")
print("====================================")

print(
    "Original size:",
    len(original_data),
    "bytes"
)


# -------------------------
# Encode
# -------------------------

shards, original_size = encode_shards(
    original_data
)

print(
    f"Generated shards: {len(shards)}"
)

print(
    f"Configuration   : "
    f"{DATA_SHARDS}-of-{TOTAL_SHARDS}"
)

print(
    f"Shard size      : "
    f"{len(shards[0])} bytes"
)


# -------------------------
# 模擬遺失 4 個 shards
# -------------------------

lost_indices = [1, 4, 7, 10]

available_shards = []
available_indices = []

for index, shard in enumerate(shards):

    if index not in lost_indices:

        available_shards.append(
            shard
        )

        available_indices.append(
            index
        )


print(
    "\nLost shards     :",
    lost_indices
)

print(
    "Available shards:",
    available_indices
)

print(
    "Remaining count :",
    len(available_shards)
)


# -------------------------
# Recovery
# -------------------------

recovered_data = decode_shards(
    available_shards,
    available_indices,
    original_size
)


print(
    "\nRecovered data:"
)

print(
    recovered_data
)


# -------------------------
# Verify
# -------------------------

if recovered_data == original_data:

    print(
        "\n[PASS] "
        "Data recovered successfully "
        "after losing 4 shards"
    )

else:

    print(
        "\n[FAIL] "
        "Recovered data mismatch"
    )