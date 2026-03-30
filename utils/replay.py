"""Replay related classes"""
from utils.data import *
import lzma
from utils.tick2date import dotnet_ticks_to_datetime

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
    def __init__(self,  **kwargs):
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
        MODE = {
            0: "std",
            1: "taiko",
            2: "catch",
            3: "mania"
        }
        meta = {}
        pos = 0

        mode, offset = int.from_bytes(data[pos:pos+1], byteorder='little', signed=False), 1
        meta['mode'] = MODE.get(mode, "unknown")
        pos += offset
        
        version, offset = ints.decode(data[pos:])
        meta['version'] = version
        pos += offset
        
        beatmap_hash, offset = strings.decode(data[pos:])
        meta['beatmap_hash'] = beatmap_hash
        pos += offset
        
        player_name, offset = strings.decode(data[pos:])
        meta['player_name'] = player_name
        pos += offset
        
        replay_hash, offset = strings.decode(data[pos:])
        meta['replay_hash'] = replay_hash
        pos += offset
        
        count_300, offset = shorts.decode(data[pos:])
        meta['count_300'] = count_300
        pos += offset
        
        if mode == 0:  
            count_100, offset = shorts.decode(data[pos:])
            meta['count_100'] = count_100
            pos += offset

            count_50, offset = shorts.decode(data[pos:])
            meta['count_50'] = count_50
            pos += offset
            
            count_geki, offset = shorts.decode(data[pos:])
            meta['count_geki'] = count_geki
            pos += offset
            
            count_katu, offset = shorts.decode(data[pos:])
            meta['count_katu'] = count_katu
            pos += offset
        elif mode == 1:
            count_150, offset = shorts.decode(data[pos:])
            meta['count_150'] = count_150
            pos += offset
        elif mode == 2:
            count_100, offset = shorts.decode(data[pos:])
            meta['count_100'] = count_100
            pos += offset
            
            count_small_fruit, offset = shorts.decode(data[pos:])
            meta['count_small_fruit'] = count_small_fruit
            pos += offset
        elif mode == 3:
            count_100, offset = shorts.decode(data[pos:])
            meta['count_100'] = count_100
            pos += offset
            
            count_50, offset = shorts.decode(data[pos:])
            meta['count_50'] = count_50
            pos += offset
            
            count_320, offset = shorts.decode(data[pos:])
            meta['count_320'] = count_320
            pos += offset
            
            count_200, offset = shorts.decode(data[pos:])
            meta['count_200'] = count_200
            pos += offset
        else:
            raise ValueError(f"Unsupported game mode: {mode}")
        
        count_miss, offset = shorts.decode(data[pos:])
        meta['count_miss'] = count_miss
        pos += offset
        
        score, offset = ints.decode(data[pos:])
        meta['score'] = score
        pos += offset
        
        max_combo, offset = shorts.decode(data[pos:])
        meta['max_combo'] = max_combo
        pos += offset
        
        pfc, offset = int.from_bytes(data[pos:pos+1], byteorder='little', signed=False), 1
        meta['perfect'] = bool(pfc)
        pos += offset
        
        mods, offset = ints.decode(data[pos:])
        meta['mods'] = mods # TODO: 解析 mods 位域
        pos += offset
        
        life_bar_graph, offset = strings.decode(data[pos:])
        pos += offset
        
        time_stamp, offset = longs.decode(data[pos:])
        meta['time_tick'] = time_stamp
        meta['time'] = dotnet_ticks_to_datetime(time_stamp).strftime('%Y-%m-%d %H:%M:%S')
        pos += offset
        
        meta[life_bar_graph] = life_bar_graph
        print(f"Parsed meta: {meta}")
        
        length_data, offset = ints.decode(data[pos:])
        pos += offset
        print(f"Compressed replay data length: {length_data} bytes")
        compressed_data = data[pos:pos+length_data]
        try:
            replay_data = lzma.decompress(compressed_data, format=lzma.FORMAT_ALONE).decode("utf-8")
        except lzma.LZMAError as e:
            raise ValueError(f"Decompression failed: {e}")
        except UnicodeDecodeError:
            raise ValueError("Decompression succeeded, but the content is not valid UTF-8 text.")
        pos += length_data
        
        score_id = longs.decode(data[pos:])[0]
        meta['score_id'] = score_id
        
        return meta, life_bar_graph, replay_data
        
    def load_from_file(self, file_path: str):
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

    def construct_bytes(self) -> bytes:
        """Construct the byte sequence representing the replay data for hash calculating.
        
        This method should take the current state of the Replay object (including meta data and frames) and construct a byte sequence that can be saved as a .osr file. 
        The constructed byte sequence should follow the same format as the original .osr replay data, including the correct encoding of meta fields, compression of replay data, and calculation of the replay hash.
        
        Returns:
            bytes: The byte sequence representing the replay data(not containing the header and hash).
        """
        # TODO
        # We still need to figure out the exact fields used in calculating hash.

    def recal_hash(self):
        """Recalculate the replay hash based on the current replay data.
        
        This method should be called after modifying any of the replay data to ensure that the replay hash is consistent with the content.
        """
        # First to construct the replay data bytes from the current frames and meta data
        # TODO
        pass
    
    def check_meta(self):
        """Check the consistency of the replay meta data.
        
        This method can be used to verify that the meta data fields are consistent with each other 
        (e.g., if the meta contains count_geki, then the mode should be standard, etc.). 
        It can also check for any missing or invalid fields in the meta data.
        
        It should be called after loading the replay data or modifying any of the meta fields to ensure that the replay data is valid and consistent.
        """
        mode = getattr(self, "mode", None)
        match mode:
            case "std":
                required_fields = ["count_100", "count_50", "count_geki", "count_katu"]
            case "taiko":
                required_fields = ["count_150"]
            case "catch":
                required_fields = ["count_100", "count_small_fruit"]
            case "mania":
                required_fields = ["count_100", "count_50", "count_320", "count_200"]
            case _:
                raise ValueError(f"Unsupported game mode: {mode}")
        required_fields.extend([
            "count_300", 
            "version",
            "count_miss", 
            "max_combo", 
            "perfect", 
            "mods", 
            "time_tick", 
            "score_id", 
            "time", 
            "score", 
            "score_id", 
            "beatmap_hash",
            "player_name",
            "replay_hash",
            ])
        for field in required_fields:
            if not hasattr(self, field):
                raise ValueError(f"Missing required meta field: {field}")
    
    def save_to_file(self, file_path: str):
        """Save the replay data to a .osr file.
        
        Args:
            file_path (str): The path where the .osr replay file will be saved.
        """
        # TODO: 实现将 Replay 对象重新打包成 .osr 文件的功能
        raise NotImplementedError("Saving replay to file is not implemented yet.")
        pass
    