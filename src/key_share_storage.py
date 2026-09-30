import os
import json


class KeyShareStorage:

    def __init__(
        self,
        base_dir="key_nodes",
        total_nodes=5
    ):
        self.base_dir = base_dir
        self.total_nodes = total_nodes

        os.makedirs(
            self.base_dir,
            exist_ok=True
        )

        for node_id in range(
            1,
            self.total_nodes + 1
        ):
            node_dir = self.get_node_dir(
                node_id
            )

            os.makedirs(
                node_dir,
                exist_ok=True
            )


    def get_node_dir(
        self,
        node_id
    ):
        return os.path.join(
            self.base_dir,
            f"node_{node_id}"
        )


    def save_share(
        self,
        event_id,
        share_index,
        share_value
    ):
        """
        將某一份 Shamir share
        儲存到對應的 key node。
        """

        if not (
            1 <= share_index <= self.total_nodes
        ):
            raise ValueError(
                f"Invalid node/share index: "
                f"{share_index}"
            )


        node_dir = self.get_node_dir(
            share_index
        )


        filename = (
            f"{event_id}_share_"
            f"{share_index}.json"
        )


        share_path = os.path.join(
            node_dir,
            filename
        )


        share_data = {
            "event_id":
                event_id,

            "share_index":
                share_index,

            "x":
                share_index,

            "y":
                str(
                    share_value
                )
        }


        with open(
            share_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                share_data,
                f,
                indent=4
            )


        return share_path


    def load_share(
        self,
        event_id,
        share_index
    ):
        """
        從指定 node 讀取某事件的 share。
        """

        node_dir = self.get_node_dir(
            share_index
        )


        filename = (
            f"{event_id}_share_"
            f"{share_index}.json"
        )


        share_path = os.path.join(
            node_dir,
            filename
        )


        if not os.path.exists(
            share_path
        ):
            return None


        with open(
            share_path,
            "r",
            encoding="utf-8"
        ) as f:

            share_data = json.load(
                f
            )


        return (
            int(
                share_data["x"]
            ),
            int(
                share_data["y"]
            )
        )


    def load_available_shares(
        self,
        event_id
    ):
        """
        掃描所有 key nodes，
        找出目前還存在的 shares。
        """

        shares = []


        for share_index in range(
            1,
            self.total_nodes + 1
        ):

            share = self.load_share(
                event_id,
                share_index
            )


            if share is not None:

                shares.append(
                    share
                )


        return shares