"""Replay related classes"""

import lzma
from dataclasses import dataclass
from typing import cast
from utils.data import *
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
MODE = {0: "std", 1: "taiko", 2: "ctb", 3: "mania"}

# Frame Info Format:
# (time_abs, time_d, mode, state_data)
# std: (time_abs, time_d, mode, {"x": x, "y": y, "keys": bool to indicate the corresponding key is pressed})
# taiko: (time_abs, time_d, mode, {"keys": bool to indicate the corresponding key is pressed})
# ctb: (time_abs, time_d, mode, {"x": x, "dash": dash})
# mania: (time_abs, time_d, mode, {"lane" : bool to indicate the corresponding lane is pressed})


class ReplayFrame:
    """
    A class representing a single frame of replay data.
    Detailed information about the frame is different between modes.
    See subclasses for more details.

    You should not create ReplayFrame objects directly, but use the corresponding subclass based on the mode of the replay.
    """

    def __init__(self, frame: str):
        # w | x | y | z
        # print(f"Parsing frame: {frame}")
        w, x, y, z = frame.split("|")
        self.time_d = int(w)
        self.x = float(x)
        self.y = float(y)
        self.keys = int(z)
        self.mode = "unknown"
        pass


class ReplayFrameStd(ReplayFrame):
    """
    A class representing a single frame of replay data for standard mode.

    The frame data is in the format of "time_d|x|y|keys", where:
    - time_d: The time in milliseconds from the previous frame (delta time).
    - x: The x-coordinate of the cursor position.
    - y: The y-coordinate of the cursor position.
    - keys: A bitfield representing the pressed keys (M1, M2, K1, K2).
    """

    def __init__(self, frame: str):
        super().__init__(frame)
        self.mode = "std"


class ReplayFrameTaiko(ReplayFrame):
    """
    A class representing a single frame of replay data for taiko mode.

    The frame data is in the format of "time_d|x|y|keys", where:
    - time_d: The time in milliseconds from the previous frame (delta time).
    - x: The x-coordinate of the cursor position (not used in taiko mode, always 0).
    - y: The y-coordinate of the cursor position (not used in taiko mode, always 0).
    - keys: A bitfield representing the pressed keys (LEFT-DON, LEFT-KAT, RIGHT-DON, RIGHT-KAT).
    """

    def __init__(self, frame: str):
        super().__init__(frame)
        self.mode = "taiko"


class ReplayFrameCtb(ReplayFrame):
    """
    A class representing a single frame of replay data for catch the beat mode.

    The frame data is in the format of "time_d|x|y|keys", where:
    - time_d: The time in milliseconds from the previous frame (delta time).
    - x: The x-coordinate of the cursor position.
    - y: The y-coordinate of the cursor position (not used in ctb mode, always 0).
    - keys: A bitfield representing the pressed keys (DASH).

    """

    def __init__(self, frame: str):
        super().__init__(frame)
        self.mode = "ctb"


class ReplayFrameMania(ReplayFrame):
    """
    A class representing a single frame of replay data for mania mode.

    The frame data is in the format of "time_d|x|y|keys", where:
    - time_d: The time in milliseconds from the previous frame (delta time).
    - x: The lane index (0-based) of the key press.
    - y: The y-coordinate of the cursor position (not used in mania mode, always 0).
    - keys: A bitfield representing the pressed keys (not used in mania mode, always 0).
    """

    def __init__(self, frame: str):
        super().__init__(frame)
        self.mode = "mania"
        self.x = int(self.x)


@dataclass
class FrameInfo:
    time_abs: int
    time_d: int
    mode: str
    key_data: dict
    cursor_data: dict | None
    raw: ReplayFrame


class FrameDecoder:
    """
    A class for decoding replay frames into a standardized format.

    You should create a new FrameDecoder object for each replay you want to decode.
    Or you need to call the reset() method to reset the internal time state before decoding a new replay.
    """

    def __init__(self) -> None:
        self.time = 0  # used to keep track of the absolute time of the replay frames.

    def reset(self) -> None:
        self.time = 0

    def decode(self, frame: ReplayFrame) -> FrameInfo | None:

        mode = frame.mode
        if frame.time_d < 0:
            # End of the replay
            return

        self.time += frame.time_d
        match mode:
            case "std":
                time_d = frame.time_d
                cursor_data = {"x": frame.x, "y": frame.y}
                key_data = {
                    "M1": bool(frame.keys & 1),
                    "M2": bool(frame.keys & 2),
                    "K1": bool(frame.keys & 4),
                    "K2": bool(frame.keys & 8),
                }
                raw = frame
            case "taiko":
                time_d = frame.time_d
                cursor_data = None
                key_data = {
                    "LEFT-DON": bool(frame.keys & 1),
                    "LEFT-KAT": bool(frame.keys & 2),
                    "RIGHT-DON": bool(frame.keys & 4),
                    "RIGHT-KAT": bool(frame.keys & 8),
                }
                raw = frame
            case "ctb":
                time_d = frame.time_d
                cursor_data = {"x": frame.x, "y": 0}
                key_data = {
                    "DASH": bool(frame.keys & 1),
                }
                raw = frame
            case "mania":
                assert isinstance(
                    frame.x, int
                ), f"Expected integer for frame.x, got {type(frame.x)}"
                time_d = frame.time_d
                key_data = {f"lane_{n}": bool(frame.x & (1 << n)) for n in range(18)}
                cursor_data = None
                raw = frame
            case _:
                raise ValueError(f"Unsupported mode: {mode}")

        return FrameInfo(
            time_abs=self.time,
            time_d=time_d,
            mode=mode,
            key_data=key_data,
            cursor_data=cursor_data,
            raw=raw,
        )


@dataclass
class Action:
    time: int
    key: str  # e.g. "M1", "LEFT-DON", "lane_0"
    action: str
    cursor_x: float | None
    cursor_y: float | None


class ActionParser:
    """
    A class for parsing replay frame info into a readable action format.

    You should create a new ActionParser object for each frame series you want to parse.
    Or you need to call the reset() method to reset the internal action list before parsing a new frame series.
    """

    def __init__(self) -> None:
        self.actions: list[Action] = []

    def reset(self) -> None:
        self.actions = []

    def parse(self, frames_info: list[FrameInfo]) -> list[Action]:

        curr = 1
        prev = 0  # First frame is always the initial state (0|0|0|0)

        while True:
            if curr >= len(frames_info):
                break
            prev_frame = frames_info[prev]
            curr_frame = frames_info[curr]
            for key in prev_frame.key_data.keys():
                if prev_frame.key_data[key] != curr_frame.key_data[key]:
                    action_type = "press" if curr_frame.key_data[key] else "release"
                    action = Action(
                        time=curr_frame.time_abs,
                        key=key,
                        action=action_type,
                        cursor_x=(
                            curr_frame.cursor_data["x"]
                            if curr_frame.cursor_data and "x" in curr_frame.cursor_data
                            else None
                        ),
                        cursor_y=(
                            curr_frame.cursor_data["y"]
                            if curr_frame.cursor_data and "y" in curr_frame.cursor_data
                            else None
                        ),
                    )
                    self.actions.append(action)
            prev += 1
            curr += 1

        return self.actions


class Replay:
    def __init__(self, **kwargs):
        self.mode: int | None = None
        self.version: int | None = None
        self.beatmap_hash: str | None = None
        self.player_name: str | None = None
        self.replay_hash: str | None = None
        self.count_300: int | None = None
        self.count_100: int | None = None
        self.count_50: int | None = None
        self.count_geki: int | None = None
        self.count_katu: int | None = None
        self.count_miss: int | None = None
        self.score: int | None = None
        self.max_combo: int | None = None
        self.perfect: bool | None = None
        self.mods: list[str] | None = None
        self.time_tick: int | None = None
        self.time: str | None = None
        self.score_id: int | None = None
        self.frames: list[ReplayFrame] = []
        self.frames_info: list[FrameInfo] = []
        self.frame_decoder = FrameDecoder()
        self.action_parser = ActionParser()
        self.actions: list[Action] = []
        self.life_bar_graph: str | None = None

        meta = kwargs.get("meta", {})
        frames = kwargs.get("frames", [])
        self.life_bar_graph = kwargs.get("life_bar_graph", None)

        for key, value in meta.items():
            setattr(self, key, value)
        if len(frames) > 0 and isinstance(frames[0], str):
            # Parse strings into ReplayFrame objects
            self.check_meta()
            match self.mode:
                case 0:
                    frame_class = ReplayFrameStd
                case 1:
                    frame_class = ReplayFrameTaiko
                case 2:
                    frame_class = ReplayFrameCtb
                case 3:
                    frame_class = ReplayFrameMania
                case _:
                    raise ValueError(f"Unsupported mode: {self.mode}")
            setattr(self, "frames", [frame_class(frame) for frame in frames])
        else:
            self.frames = frames

        self.frames_info = self.decode_frames()
        self.actions = self.parse_actions()

    def __str__(self):
        return f"Replay(player_name={getattr(self, 'player_name', 'unknown')}, beatmap_hash={getattr(self, 'beatmap_hash', 'unknown')}, score={getattr(self, 'score', 0)}, max_combo={getattr(self, 'max_combo', 0)}, mods={getattr(self, 'mods', 0)}, time={getattr(self, 'time', 'unknown')})"

    @staticmethod
    def unpack_osr(data: bytes) -> tuple[dict, str, str]:
        """Unpack osu! replay data from a byte sequence.

        Args:
            data (bytes): The byte sequence containing the replay data.

        Returns:
            (replay_meta, life_bar_graph, replay_data) (tuple[dict, str, str]): A tuple containing the unpacked replay meta as a dictionary, the raw life bar graph as a string, and the raw unzipped replay data as a string.
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

    @staticmethod
    def str_to_frames(frames_str: str, mode: int) -> list[ReplayFrame]:
        """Convert a string of replay frames into a list of ReplayFrame objects.

        Args:
            frames_str (str): The string containing the replay frames, where each frame is in the format of "time_d|x|y|keys" and frames are separated by commas.
            mode (int): The game mode for which to parse the frames.

        Returns:
            list[ReplayFrame]: A list of ReplayFrame objects parsed from the input string.
        """
        if not frames_str:
            return []
        frame_strs = [
            frame for frame in frames_str.split(",") if frame
        ]  # Filter out possible empty strings
        match mode:
            case 0:
                frame_class = ReplayFrameStd
            case 1:
                frame_class = ReplayFrameTaiko
            case 2:
                frame_class = ReplayFrameCtb
            case 3:
                frame_class = ReplayFrameMania
            case _:
                raise ValueError(f"Unsupported mode: {mode}")
        return [frame_class(frame_str) for frame_str in frame_strs]

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
        frames = Replay.str_to_frames(replay_data, meta.get("mode", -1))
        self.frames = frames
        self.frames_info = self.decode_frames()
        self.actions = self.parse_actions()

    def to_json(self) -> dict:
        """Convert the Replay object into a JSON-serializable dictionary.

        Returns:
            dict: A dictionary containing the replay meta and frames data, suitable for JSON serialization.
        """
        return {
            "meta": {
                "mode": self.mode,
                "version": self.version,
                "beatmap_hash": self.beatmap_hash,
                "player_name": self.player_name,
                "replay_hash": self.replay_hash,
                "count_300": self.count_300,
                "count_100": self.count_100,
                "count_50": self.count_50,
                "count_geki": self.count_geki,
                "count_katu": self.count_katu,
                "count_miss": self.count_miss,
                "score": self.score,
                "max_combo": self.max_combo,
                "perfect": self.perfect,
                "mods": self.mods,
                "time_tick": self.time_tick,
                "time": self.time,
                "score_id": self.score_id,
            },
            "frames": [
                {
                    "time_d": frame.time_d,
                    "x": frame.x,
                    "y": frame.y,
                    "keys": frame.keys,
                    "mode": frame.mode,
                }
                for frame in self.frames
            ],
            "life_bar_graph": self.life_bar_graph,
        }

    def decode_frames(self) -> list[FrameInfo]:
        """Decode the replay frames into a list of FrameInfo objects.

        Returns:
            list[FrameInfo]: A list of FrameInfo objects containing the decoded information of each frame.
        """
        self.frame_decoder.reset()
        if not self.frames:
            return []
        frame_infos: list[FrameInfo] = []
        for frame in self.frames:
            frame_info = self.frame_decoder.decode(frame)
            if frame_info is not None:
                frame_infos.append(frame_info)
        frame_infos.sort(key=lambda x: x.time_abs)
        return frame_infos

    def parse_actions(self) -> list[Action]:
        self.action_parser.reset()
        if not self.frames_info:
            return []
        actions = self.action_parser.parse(self.frames_info)
        actions.sort(key=lambda x: x.time)
        return actions

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
        ret_str = ",".join(
            f"{frame.time_d}|{frame.x}|{frame.y}|{frame.keys}" for frame in self.frames
        )
        return ret_str + ","  # Add a trailing comma to indicate the end of frames

    def save(self, file_path: str):
        """Save the replay data to a .osr file.

        Args:
            file_path (str): The path where the .osr replay file will be saved.
        """
        # TODO: 实现将 Replay 对象重新打包成 .osr 文件的功能
        self.check_meta()
        mode_b = cast(int, self.mode).to_bytes(1, byteorder="little", signed=False)
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
        perfect_b = (1 if self.perfect else 0).to_bytes(
            1, byteorder="little", signed=False
        )

        mod_value = 0
        for key, value in MODS.items():
            if self.mods and key in self.mods:
                mod_value |= value

        mod_b = ints.encode(mod_value)
        life_bar_graph_b = strings.encode(cast(str, self.life_bar_graph))
        time_tick_b = longs.encode(cast(int, self.time_tick))

        frames_str = self.frames_to_str()
        compressed_frames = lzma.compress(
            frames_str.encode("utf-8"), format=lzma.FORMAT_ALONE
        )
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
