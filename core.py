from utils import *
import lzma

MODE = {
    0: "std",
    1: "taiko",
    2: "catch",
    3: "mania"
}

def unpack_osr(data: bytes) -> tuple[dict, str, str]:
    """Unpack osu! replay data from a byte sequence.
    
    Args:
        data (bytes): The byte sequence containing the replay data.
    
    Returns:
        (replay_meta, life_bar_graph, replay_data) (tuple[dict, str, str]): A tuple containing the unpacked replay meta as a dictionary, the life bar graph as a string, and the unzipped replay data as a string.
    """
    
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
    
    meta['life_bar_graph'] = life_bar_graph
    # print(f"Parsed meta: {meta}")
    
    length_data, offset = ints.decode(data[pos:])
    pos += offset
    # print(f"Compressed replay data length: {length_data} bytes")
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
    
    
        
    
    
    
    