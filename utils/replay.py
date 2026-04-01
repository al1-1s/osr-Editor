"""Replay related classes"""

from typing import cast

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
MODE = {0: "std", 1: "taiko", 2: "catch", 3: "mania"}

class ReplayFrame:
    """
    A class representing a single frame of replay data.
    Each frame contains the following information:
    - time: The timestamp of the frame in milliseconds from the previous frame.
    - x: The x-coordinate of the cursor position (for std, ctb) or the lane index (for mania mode).
    - y: The y-coordinate of the cursor position (only for std).
    - keys: The bitfield representing the keys (including mouse buttons and keyboard keys) pressed (for std),or keys presses (for taiko), or dashing state (for ctb).
    """

    def __init__(self, frame: str):
        # w | x | y | z
        print(f"Parsing frame: {frame}")
        w, x, y, z = frame.split("|")
        self.time = int(w)
        self.x = float(x)
        self.y = float(y)
        self.keys = int(z)
        # TODO: 解析 keys 位域，区分鼠标按键和键盘按键，并根据模式区分不同的按键含义
        pass


class Replay:
    def __init__(self, **kwargs):
        self.mode: int|None = None
        self.version: int|None = None
        self.beatmap_hash: str|None = None
        self.player_name: str|None = None
        self.replay_hash: str|None = None
        self.count_300: int|None = None
        self.count_100: int|None = None
        self.count_50: int|None = None
        self.count_geki: int|None = None
        self.count_katu: int|None = None
        self.count_miss: int|None = None
        self.score: int|None = None
        self.max_combo: int|None = None
        self.perfect: bool|None = None
        self.mods: list[str]|None = None
        self.time_tick: int|None = None
        self.time: str|None = None
        self.score_id: int|None = None
        self.frames: list[ReplayFrame] = []
        self.life_bar_graph: str|None = None
        
        meta = kwargs.get("meta", {})
        frames = kwargs.get("frames", [])
        self.life_bar_graph = kwargs.get("life_bar_graph", None)
        
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
        
        meta = {}
        pos = 0

        mode, offset = (
            int.from_bytes(data[pos : pos + 1], byteorder="little", signed=False),
            1,
        )
        meta["mode"] = mode
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

        meta["life_bar_graph"] = life_bar_graph

        length_data, offset = ints.decode(data[pos:])
        pos += offset
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
        print(f"Loaded {len(frames)} replay frames.")
        print(f"First 5 frames: {frames[:5]}")
        self.frames = [ReplayFrame(frame) for frame in frames[:-1]] # Empty frame at the end

    def check_meta(self):
        """Check the consistency of the replay meta data.
        
        It can only check for any missing fields in the meta data.
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
            "life_bar_graph",
        ]
        for field in required_fields:
            if not hasattr(self, field) or getattr(self, field) is None:
                raise ValueError(f"Missing required meta field: {field}")

    def frames_to_str(self) -> str:
        """Compress the replay frames into a string format suitable for saving to a .osr file.

        Returns:
            str: The compressed replay frames as a string.
        """
        if not self.frames:
            return ""
        return ",".join(f"{frame.time}|{frame.x}|{frame.y}|{frame.keys}" for frame in self.frames)

    def save(self, file_path: str):
        """Save the replay data to a .osr file.

        Args:
            file_path (str): The path where the .osr replay file will be saved.
        """
        # TODO: 实现将 Replay 对象重新打包成 .osr 文件的功能
        self.check_meta()
        mode_b= cast(int, self.mode).to_bytes(1, byteorder="little", signed=False)
        version_b = ints.encode(cast(int, self.version))
        bm_hash_b = strings.encode(cast(str, self.beatmap_hash))
        player_name_b = strings.encode(cast(str, self.player_name))
        replay_hash_b = strings.encode(cast(str, self.replay_hash))
        count_300_b = shorts.encode(cast(int, self.count_300))
        count_100_b = shorts.encode(cast(int, self.count_100))
        count_50_b = shorts.encode(cast(int, self.count_50))
        count_geki_b = shorts.encode(cast(int, self.count_geki))
        count_katu_b = shorts.encode(cast(int, self.count_katu))
        count_miss_b = shorts.encode(cast(int, self.count_miss))
        score_b = ints.encode(cast(int, self.score))
        max_combo_b = shorts.encode(cast(int, self.max_combo))
        perfect_b = (1 if self.perfect else 0).to_bytes(1, byteorder="little", signed=False)
        
        mod_value = 0
        for key, value in MODS.items():
            if self.mods and key in self.mods:
                mod_value |= value
                break
            
        mod_b = ints.encode(mod_value)
        life_bar_graph_b = strings.encode(cast(str, self.life_bar_graph))
        time_tick_b = longs.encode(cast(int, self.time_tick))
        
        frames_str = self.frames_to_str()
        compressed_frames = lzma.compress(frames_str.encode("utf-8"), format=lzma.FORMAT_ALONE)
        length_b = ints.encode(len(compressed_frames))
        
        score_id_b = longs.encode(cast(int, self.score_id))
        
        bytes_data = (
            mode_b
            + version_b
            + bm_hash_b
            + player_name_b
            + replay_hash_b
            + count_300_b
            + count_100_b
            + count_50_b
            + count_geki_b
            + count_katu_b
            + count_miss_b
            + score_b
            + max_combo_b
            + perfect_b
            + mod_b
            + life_bar_graph_b
            + time_tick_b
            + length_b
            + compressed_frames
            + score_id_b
        )
        with open(file_path, "wb") as f:
            f.write(bytes_data)