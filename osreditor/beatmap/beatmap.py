from dataclasses import dataclass, field
from typing import Union, Optional, Callable

"""Beatmap class for handling osu! beatmap data."""


@dataclass
class HitObjectRaw:
    x: int
    y: int
    time: int
    type: int
    hit_sound: int
    object_params: str  # inculdes hit sample set, as osu!mania holds use colon to separate end time and hit sample set, while other modes use comma to separate. fuck ppy:/
    raw_line: str


@dataclass
class CircleData:
    hit_sample: str


@dataclass
class SliderData:
    curve: str
    slides: int
    length: int
    edge_sounds: str
    edge_sets: str
    hit_sample: str


@dataclass
class SpinnerData:
    end_time: int
    hit_sample: str


@dataclass
class HoldData:
    end_time: int
    hit_sample: str


@dataclass
class TimingPoint:
    time: int
    beat_length: float
    meter: int
    sample_set: int
    sample_index: int
    volume: int
    effects: int


@dataclass
class InheritedTimingPoint:
    time: int
    slider_velocity_multiplier: float
    sample_set: int
    sample_index: int
    volume: int
    effects: int


Payload = Union[CircleData, SliderData, SpinnerData, HoldData]


@dataclass
class HitObject:
    raw: HitObjectRaw
    payload: Payload

    def __post_init__(self):
        self.x = self.raw.x
        self.y = self.raw.y
        self.time = self.raw.time
        self.type = self.raw.type
        self.hitsound = self.raw.hit_sound


class ObjectParser:
    def __init__(self):
        pass

    @staticmethod
    def parse(raw: HitObjectRaw) -> Payload:
        parser_registry: dict[int, Callable[[HitObjectRaw], Payload]] = {
            1: ObjectParser.parse_circle,
            2: ObjectParser.parse_slider,
            4: ObjectParser.parse_spinner,
            128: ObjectParser.parse_hold,
        }
        for bit, parser in parser_registry.items():
            if raw.type & bit:
                return parser(raw)
        raise ValueError(f"Unknown hit object type: {raw.type}")

    @staticmethod
    def parse_circle(raw: HitObjectRaw) -> CircleData:
        return CircleData(hit_sample=raw.object_params)

    @staticmethod
    def parse_slider(raw: HitObjectRaw) -> SliderData:
        return SliderData(
            curve=raw.object_params.split(",")[0],
            slides=int(raw.object_params.split(",")[1]),
            length=int(raw.object_params.split(",")[2]),
            edge_sounds=raw.object_params.split(",")[3],
            edge_sets=raw.object_params.split(",")[4],
            hit_sample=raw.object_params.split(",")[5],
        )

    @staticmethod
    def parse_spinner(raw: HitObjectRaw) -> SpinnerData:
        return SpinnerData(
            end_time=int(raw.object_params.split(",")[0]),
            hit_sample=raw.object_params.split(",")[1],
        )

    @staticmethod
    def parse_hold(raw: HitObjectRaw) -> HoldData:
        return HoldData(
            end_time=int(raw.object_params.split(":")[0]),
            hit_sample=":".join(raw.object_params.split(":")[1:]),
        )


@dataclass
class Beatmap:
    title: Optional[str] = None
    artist: Optional[str] = None
    title_unicode: Optional[str] = None
    artist_unicode: Optional[str] = None
    version: Optional[str] = None
    bid: Optional[int] = None
    sid: Optional[int] = None
    hit_objects: list[HitObject] = field(default_factory=list)
    mode: Optional[int] = None
    od: Optional[float] = None
    ar: Optional[float] = None
    hp: Optional[float] = None
    cs: Optional[float] = None
    timing_points: list[TimingPoint] = field(default_factory=list)
    inherited_timing_points: list[InheritedTimingPoint] = field(default_factory=list)

    @classmethod
    def from_osu_file(cls, file_path: str) -> "Beatmap":
        meta, hitobjects = cls.unpack_osu(file_path)
        instance = cls()
        for key, value in meta.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        instance.hit_objects = hitobjects
        return instance

    @staticmethod
    def unpack_osu(file_path: str) -> tuple[dict, list[HitObject]]:
        meta = {}
        hitobjects = []
        with open(file_path, "r", encoding="utf-8") as f:
            section = None
            for line in f:
                line = line.strip()
                if not line or line.startswith("//"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    section = line[1:-1]
                    continue

                if section == "General":
                    if line.startswith("Mode:"):
                        meta["mode"] = int(line[len("Mode:") :].strip())
                elif section == "Metadata":
                    if line.startswith("Title:"):
                        meta["title"] = line[len("Title:") :].strip()
                    elif line.startswith("Artist:"):
                        meta["artist"] = line[len("Artist:") :].strip()
                    elif line.startswith("TitleUnicode:"):
                        meta["title_unicode"] = line[len("TitleUnicode:") :].strip()
                    elif line.startswith("ArtistUnicode:"):
                        meta["artist_unicode"] = line[len("ArtistUnicode:") :].strip()
                    elif line.startswith("Version:"):
                        meta["version"] = line[len("Version:") :].strip()
                    elif line.startswith("BeatmapID:"):
                        meta["bid"] = int(line[len("BeatmapID:") :].strip())
                    elif line.startswith("BeatmapSetID:"):
                        meta["sid"] = int(line[len("BeatmapSetID:") :].strip())
                elif section == "Difficulty":
                    if line.startswith("HPDrainRate:"):
                        meta["hp"] = float(line[len("HPDrainRate:") :].strip())
                    elif line.startswith("CircleSize:"):
                        meta["cs"] = float(line[len("CircleSize:") :].strip())
                    elif line.startswith("OverallDifficulty:"):
                        meta["od"] = float(line[len("OverallDifficulty:") :].strip())
                    elif line.startswith("ApproachRate:"):
                        meta["ar"] = float(line[len("ApproachRate:") :].strip())
                elif section == "TimingPoints":
                    parts = line.split(",")
                    if len(parts) < 8:
                        raise ValueError(f"Invalid timing point line: {line}")
                    time = int(parts[0])
                    beat_length = float(parts[1])
                    meter = int(parts[2])
                    sample_set = int(parts[3])
                    sample_index = int(parts[4])
                    volume = int(parts[5])
                    is_inherited = int(parts[6]) == 0
                    effects = int(parts[7])
                    if beat_length > 0:
                        meta["timing_points"] = meta.get("timing_points", []) + [
                            TimingPoint(
                                time,
                                beat_length,
                                meter,
                                sample_set,
                                sample_index,
                                volume,
                                effects,
                            )
                        ]
                    else:
                        meta["inherited_timing_points"] = (
                            meta.get("inherited_timing_points", [])
                            + [
                                InheritedTimingPoint(
                                    time,
                                    -100 / beat_length,
                                    sample_set,
                                    sample_index,
                                    volume,
                                    effects,
                                )
                            ]
                        )
                elif section == "HitObjects":
                    parts = line.split(",")
                    if len(parts) < 5:
                        raise ValueError(f"Invalid hit object line: {line}")
                    x = int(parts[0])
                    y = int(parts[1])
                    time = int(parts[2])
                    type = int(parts[3])
                    hit_sound = int(parts[4])
                    object_params = ",".join(parts[5:]) if len(parts) > 5 else ""
                    raw = HitObjectRaw(x, y, time, type, hit_sound, object_params, line)
                    payload = ObjectParser.parse(raw)
                    hitobjects.append(HitObject(raw, payload))
        return meta, hitobjects
