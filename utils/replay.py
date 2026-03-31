"""Replay related classes"""

from utils.data import *
import lzma
from utils.tick2date import dotnet_ticks_to_datetime

MODS = {
    "None": 0,
    "NoFail": 1,
    "Easy": 1 << 1,
    "TouchDevice": 1 << 2,
    "Hidden": 1 << 3,
    "HardRock": 1 << 4,
    "SuddenDeath": 1 << 5,
    "DoubleTime": 1 << 6,
    "Relax": 1 << 7,
    "HalfTime": 1 << 8,
    "Nightcore": 1 << 9,
    "Flashlight": 1 << 10,
    "Autoplay": 1 << 11,
    "SpunOut": 1 << 12,
    "Autopilot": 1 << 13,
    "Perfect": 1 << 14,
    "Key4": 1 << 15,
    "Key5": 1 << 16,
    "Key6": 1 << 17,
    "Key7": 1 << 18,
    "Key8": 1 << 19,
    "FadeIn": 1 << 20,
    "Random": 1 << 21,
    "Cinema": 1 << 22,
    "Target": 1 << 23,  # CuttingEdge only
    "Key9": 1 << 24,
    "Coop": 1 << 25,
    "Key1": 1 << 26,
    "Key3": 1 << 27,
    "Key2": 1 << 28,
    "ScoreV2": 1 << 29,
    "Mirror": 1 << 30,
}


class ReplayFrame:
    """
    A class representing a single frame of replay data.
    Each frame contains the following information:
    - time: The timestamp of the frame in milliseconds from the previous frame.
    - x: The x-coordinate of the cursor position (for std, ctb) or the lane index (for mania mode).
    - y: The y-coordinate of the cursor position (only for std).
    - keys: The bitfield representing the keys (including mouse buttons and keyboard keys) pressed (for std),or keys presses (for taiko), or dashing state (for ctb).
    """

    def __init__(self, frames: str):
        # w | x | y | z
        w, x, y, z = frames.split("|")
        self.time = int(w)
        self.x = int(x)
        self.y = int(y)
        self.keys = int(z)
        pass


class Replay:
    def __init__(self, **kwargs):
        meta = kwargs.get("meta", {})
        frames = kwargs.get("frames", [])
        for key, value in meta.items():
            setattr(self, key, value)
        if len(frames) > 0 and isinstance(frames[0], str):
            # If frames are provided as strings, we need to parse them into ReplayFrame objects
            setattr(self, "frames", [ReplayFrame(frame) for frame in frames])
        else:
            self.frames = frames

    def __str__(self):
        return f"Replay(player_name={getattr(self, 'player_name', 'unknown')}, beatmap_hash={getattr(self, 'beatmap_hash', 'unknown')}, score={getattr(self, 'score', 0)}, max_combo={getattr(self, 'max_combo', 0)}, mods={getattr(self, 'mods', 0)}, time={getattr(self, 'time', 'unknown')})"

    @staticmethod
    def unpack_osr(data: bytes) -> tuple[dict, str, str]:
        """Unpack osu! replay data from a byte sequence.

        Args:
            data (bytes): The byte sequence containing the replay data.

        Returns:
            (replay_meta, life_bar_graph, replay_data) (tuple[dict, str, str]): A tuple containing the unpacked replay meta as a dictionary, the life bar graph as a string, and the unzipped replay data as a string.
        """
        MODE = {0: "std", 1: "taiko", 2: "catch", 3: "mania"}
        meta = {}
        pos = 0

        mode, offset = (
            int.from_bytes(data[pos : pos + 1], byteorder="little", signed=False),
            1,
        )
        meta["mode"] = MODE.get(mode, "unknown")
        pos += offset

        version, offset = ints.decode(data[pos:])
        meta["version"] = version
        pos += offset

        beatmap_hash, offset = strings.decode(data[pos:])
        meta["beatmap_hash"] = beatmap_hash
        pos += offset

        player_name, offset = strings.decode(data[pos:])
        meta["player_name"] = player_name
        pos += offset

        replay_hash, offset = strings.decode(data[pos:])
        meta["replay_hash"] = replay_hash
        pos += offset

        count_300, offset = shorts.decode(data[pos:])
        meta["count_300"] = count_300
        pos += offset

        count_100, offset = shorts.decode(data[pos:])
        meta["count_100"] = count_100
        pos += offset

        count_50, offset = shorts.decode(data[pos:])
        meta["count_50"] = count_50
        pos += offset

        count_geki, offset = shorts.decode(data[pos:])
        meta["count_geki"] = count_geki
        pos += offset

        count_katu, offset = shorts.decode(data[pos:])
        meta["count_katu"] = count_katu
        pos += offset

        count_miss, offset = shorts.decode(data[pos:])
        meta["count_miss"] = count_miss
        pos += offset

        score, offset = ints.decode(data[pos:])
        meta["score"] = score
        pos += offset

        max_combo, offset = shorts.decode(data[pos:])
        meta["max_combo"] = max_combo
        pos += offset

        pfc, offset = (
            int.from_bytes(data[pos : pos + 1], byteorder="little", signed=False),
            1,
        )
        meta["perfect"] = bool(pfc)
        pos += offset

        mod, offset = ints.decode(data[pos:])
        mods = []
        for key, value in MODS.items():
            if mod & value:
                mods.append(key)
        meta["mods"] = mods
        pos += offset

        life_bar_graph, offset = strings.decode(data[pos:])
        pos += offset

        time_stamp, offset = longs.decode(data[pos:])
        meta["time_tick"] = time_stamp
        meta["time"] = dotnet_ticks_to_datetime(time_stamp).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        pos += offset

        meta[life_bar_graph] = life_bar_graph
        print(f"Parsed meta: {meta}")

        length_data, offset = ints.decode(data[pos:])
        pos += offset
        print(f"Compressed replay data length: {length_data} bytes")
        compressed_data = data[pos : pos + length_data]
        try:
            replay_data = lzma.decompress(
                compressed_data, format=lzma.FORMAT_ALONE
            ).decode("utf-8")
        except lzma.LZMAError as e:
            raise ValueError(f"Decompression failed: {e}")
        except UnicodeDecodeError:
            raise ValueError(
                "Decompression succeeded, but the content is not valid UTF-8 text."
            )
        pos += length_data

        score_id = longs.decode(data[pos:])[0]
        meta["score_id"] = score_id

        return meta, life_bar_graph, replay_data

    def load(self, file_path: str):
        """Load replay data from a .osr file.

        Args:
            file_path (str): The path to the .osr replay file.
        """
        with open(file_path, "rb") as f:
            data = f.read()
        meta, self.life_bar_graph, replay_data = self.unpack_osr(data)
        for key, value in meta.items():
            setattr(self, key, value)
        frames = replay_data.split(",")
        self.frames = [ReplayFrame(frame) for frame in frames]

    def check_meta(self):
        """Check the consistency of the replay meta data.

        This method can be used to verify that the meta data fields are consistent with each other
        (e.g., if the meta contains count_geki, then the mode should be standard, etc.).
        It can also check for any missing or invalid fields in the meta data.

        It should be called after loading the replay data or modifying any of the meta fields to ensure that the replay data is valid and consistent.
        """
        required_fields = [
            "mode",
            "version",
            "beatmap_hash",
            "player_name",
            "replay_hash",
            "count_300",
            "count_100",
            "count_50",
            "count_geki",
            "count_katu",
            "count_miss",
            "score",
            "max_combo",
            "perfect",
            "mods",
            "time_tick",
            "score_id",
        ]
        for field in required_fields:
            if not hasattr(self, field):
                raise ValueError(f"Missing required meta field: {field}")

    def save_to_file(self, file_path: str):
        """Save the replay data to a .osr file.

        Args:
            file_path (str): The path where the .osr replay file will be saved.
        """
        # TODO: 实现将 Replay 对象重新打包成 .osr 文件的功能
        self.check_meta()

        raise NotImplementedError("Saving replay to file is not implemented yet.")
        pass
