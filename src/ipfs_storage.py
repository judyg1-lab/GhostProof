import os
import subprocess


DEFAULT_IPFS_EXE = (
    r"C:\Users\sxdhw\Apps"
    r"\kubo_v0.43.1"
    r"\kubo"
    r"\ipfs.exe"
)


class IPFSStorage:

    def __init__(
        self,
        ipfs_executable=DEFAULT_IPFS_EXE
    ):
        self.ipfs_executable = ipfs_executable


    def add_file(
        self,
        file_path
    ):
        """
        將檔案加入 IPFS，
        回傳 CID。
        """

        if not os.path.exists(
            file_path
        ):
            raise FileNotFoundError(
                file_path
            )

        result = subprocess.run(
            [
                self.ipfs_executable,
                "add",
                "-Q",
                file_path
            ],
            capture_output=True,
            text=True,
            check=True
        )

        cid = result.stdout.strip()

        if not cid:
            raise RuntimeError(
                "IPFS 沒有回傳 CID"
            )

        return cid


    def get_file(
        self,
        cid,
        output_path
    ):
        """
        透過 CID 從 IPFS 取回檔案。
        """

        subprocess.run(
            [
                self.ipfs_executable,
                "get",
                cid,
                "-o",
                output_path
            ],
            check=True
        )

        return output_path