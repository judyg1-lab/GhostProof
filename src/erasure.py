import math
from zfec import Encoder, Decoder


DATA_SHARDS = 8
TOTAL_SHARDS = 12


def encode_shards(data: bytes) -> tuple[list[bytes], int]:
    """
    將資料編碼成 12 個 shards。
    任意 8 個 shards 即可還原原始資料。

    Returns:
        shards: 12 個編碼後的 shards
        original_size: 原始資料長度
    """

    original_size = len(data)

    # zfec 要求 8 個輸入 block 長度相同
    block_size = math.ceil(original_size / DATA_SHARDS)

    padded_size = block_size * DATA_SHARDS

    padded_data = data + b"\x00" * (
        padded_size - original_size
    )

    # 切成 8 個等長 data blocks
    blocks = []

    for i in range(DATA_SHARDS):
        start = i * block_size
        end = start + block_size

        blocks.append(
            padded_data[start:end]
        )

    encoder = Encoder(
        DATA_SHARDS,
        TOTAL_SHARDS
    )

    # 產生 12 個 shard
    shards = list(
        encoder.encode(blocks)
    )

    return shards, original_size


def decode_shards(
    available_shards: list[bytes],
    shard_indices: list[int],
    original_size: int
) -> bytes:
    """
    使用任意 8 個 shards 還原資料。

    Args:
        available_shards:
            可取得的 8 個 shard

        shard_indices:
            對應 shard 編號，例如
            [0, 1, 3, 4, 6, 8, 10, 11]

        original_size:
            原始資料長度
    """

    if len(available_shards) < DATA_SHARDS:
        raise ValueError(
            f"至少需要 {DATA_SHARDS} 個 shards 才能恢復資料"
        )

    # recovery 只需要 8 個
    available_shards = available_shards[
        :DATA_SHARDS
    ]

    shard_indices = shard_indices[
        :DATA_SHARDS
    ]

    decoder = Decoder(
        DATA_SHARDS,
        TOTAL_SHARDS
    )

    recovered_blocks = decoder.decode(
        available_shards,
        shard_indices
    )

    recovered_data = b"".join(
        recovered_blocks
    )

    # 去除前面補上的 zero padding
    return recovered_data[:original_size]