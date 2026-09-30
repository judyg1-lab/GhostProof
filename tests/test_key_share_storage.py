import shutil
import os

from src.key_share_storage import (
    KeyShareStorage
)


TEST_DIR = "key_nodes_test"


if os.path.exists(
    TEST_DIR
):
    shutil.rmtree(
        TEST_DIR
    )


storage = KeyShareStorage(
    base_dir=TEST_DIR,
    total_nodes=5
)


event_id = "event_test"


print(
    "GhostProof Key Share Storage Test"
)


for i in range(
    1,
    6
):

    storage.save_share(
        event_id=event_id,
        share_index=i,
        share_value=1000 + i
    )


print(
    "[PASS] 5 shares saved"
)


shares = storage.load_available_shares(
    event_id
)


print(
    "Available shares:",
    shares
)


if len(shares) == 5:

    print(
        "[PASS] 5 key nodes readable"
    )

else:

    print(
        "[FAIL] key share storage test failed"
    )