import os
import shutil
import subprocess


class IPFSStorage:

    def __init__(
        self,
        ipfs_executable=None
    ):
        # 如果沒有手動指定，
        # 自動從系統 PATH 找 ipfs
        if ipfs_executable is None:

            ipfs_executable = shutil.which(
                "ipfs"
            )

        if ipfs_executable is None:

            raise FileNotFoundError(
                "找不到 Kubo IPFS 執行檔。"
                "請確認已安裝 Kubo，"
                "且 ipfs 已加入 PATH。"
            )

        self.ipfs_executable = (
            ipfs_executable
        )


    def add_file(
        self,
        file_path
    ):

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