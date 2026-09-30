import secrets


PRIME = 2**521 - 1


def split_secret(
    secret: bytes,
    threshold: int = 3,
    num_shares: int = 5
) -> list[tuple[int, int]]:
    if threshold < 2:
        raise ValueError("threshold 必須至少為 2")

    if num_shares < threshold:
        raise ValueError("num_shares 不可小於 threshold")

    secret_int = int.from_bytes(secret, byteorder="big")

    if secret_int >= PRIME:
        raise ValueError("Secret too large for selected finite field")

    coefficients = [secret_int]

    for _ in range(threshold - 1):
        coefficients.append(
            secrets.randbelow(PRIME)
        )

    shares = []

    for x in range(1, num_shares + 1):
        y = 0

        for power, coefficient in enumerate(coefficients):
            y = (
                y
                + coefficient * pow(x, power, PRIME)
            ) % PRIME

        shares.append((x, y))

    return shares


def recover_secret(
    shares: list[tuple[int, int]],
    threshold: int = 3,
    secret_length: int = 32
) -> bytes:
    """
    使用 Lagrange interpolation
    從 Shamir shares 重建 secret。

    至少需要 threshold 份 shares。
    """

    if len(shares) < threshold:
        raise ValueError(
            f"至少需要 {threshold} 個 shares，"
            f"目前只有 {len(shares)} 個"
        )

    secret_int = 0

    for i, (x_i, y_i) in enumerate(shares):

        numerator = 1
        denominator = 1

        for j, (x_j, _) in enumerate(shares):

            if i == j:
                continue

            numerator = (
                numerator * (-x_j)
            ) % PRIME

            denominator = (
                denominator * (x_i - x_j)
            ) % PRIME

        lagrange = (
            numerator
            * pow(
                denominator,
                -1,
                PRIME
            )
        ) % PRIME

        secret_int = (
            secret_int
            + y_i * lagrange
        ) % PRIME

    if secret_int >= (1 << (8 * secret_length)):
        raise ValueError(
            "Recovered secret exceeds expected length"
        )

    return secret_int.to_bytes(
        secret_length,
        byteorder="big"
    )