"""A previewer of beatmap. Renders beatmap to an image. Only supports osu!mania for now."""

from PIL import Image, ImageDraw
from .. import beatmap


def read_beatmap(file_path: str) -> beatmap.Beatmap:
    """Reads a beatmap file and returns a Beatmap object."""
    return beatmap.Beatmap.from_osu_file(file_path)


class BeatmapPreviewer:
    LANE_WIDTH = 20  # width of each column
    TAP_HEIGHT = 9  # height of tap hit objects
    TIME_HEIGHT_SCALE = 0.5  # scale factor for converting time to height
    HOLD_HEIGHT = (
        2 * TIME_HEIGHT_SCALE
    )  # height of hold hit objects  (for each 2ms of hold duration)
    MIN_HOLD_HEIGHT = 5  # minimum height of hold hit objects
    PADDING = 5  # padding on the sides of the preview image
    LANE_SPACING = 2  # spacing between lanes
    MAX_COLUMN_HEIGHT = 5000  # maximum height of each column
    COLUMN_SPACING = 80  # spacing between columns
    SPLIT_LINE_WEIGHT = 2  # weight of the split line between columns
    VERTICAL_OFFSET = 2  # vertical offset to prevent hit objects from touching the bottom edge of the image

    BACKGROUND_COLOR = (0, 0, 0)  # background color of the preview image
    TAP_COLOR_1 = (60, 200, 200)  # color of taps
    TAP_COLOR_2 = (200, 200, 200)  # color of taps
    HOLD_COLOR_1 = (60, 200, 200)  # color of holds
    HOLD_COLOR_2 = (200, 200, 200)  # color of holds
    EDGE_COLOR = (60, 200, 200)  # color of edge of hit objects
    SPLIT_LINE_COLOR = (180, 180, 180)  # color of the split line between columns

    def __init__(self, beatmap: beatmap.Beatmap):
        if not beatmap.cs:
            raise ValueError("missing column value in beatmap, cannot render preview")
        if beatmap.mode != 3:
            raise ValueError("unsupported game mode, only mania is supported for now")
        self.beatmap = beatmap
        self.lanes = int(beatmap.cs)
        self.width = (
            self.lanes * self.LANE_WIDTH
            + 2 * self.PADDING
            + (self.lanes - 1) * self.LANE_SPACING
        )
        self.column_width = self.width + self.COLUMN_SPACING
        self.original_height = int(
            beatmap.hit_objects[-1].time * self.TIME_HEIGHT_SCALE + 10
        )
        self.height = self.original_height
        # print(f"Preview image size: {self.width}x{self.height}")
        # width = lanes * LANE_WIDTH, height = time of last hit object * TIME_HEIGHT_SCALE + 10
        self.img = Image.new("RGB", (self.width, self.height), self.BACKGROUND_COLOR)
        self.drawer = ImageDraw.Draw(self.img)

    def draw(self) -> Image.Image:
        """Renders the beatmap to an image."""
        for hit_object in self.beatmap.hit_objects:
            if hit_object.type == 1:  # tap
                self.draw_tap(hit_object)
            elif hit_object.type == 128:  # hold
                self.draw_holds(hit_object)
        self.to_multi_column()
        for timing_point in self.beatmap.timing_points:
            self.draw_timing_points(timing_point)
        # for inherited_timing_point in self.beatmap.inherited_timing_points:
        #     self.draw_inherited_timing_points(inherited_timing_point)

        # print("Finished rendering beatmap preview.")

        return self.img

    def draw_tap(self, hit_object: beatmap.HitObject) -> None:
        """Renders a tap hit object to the image."""
        x = hit_object.x
        time = hit_object.time
        lane = x * self.lanes // 512
        # Draw a rounded rectangle for the tap hit object
        # time -> y coordinate, lane -> x coordinate
        x0 = lane * self.LANE_WIDTH + self.PADDING + lane * self.LANE_SPACING
        x1 = (lane + 1) * self.LANE_WIDTH + self.PADDING + lane * self.LANE_SPACING
        y1 = self.height - (time * self.TIME_HEIGHT_SCALE + self.VERTICAL_OFFSET)
        y0 = self.height - (
            time * self.TIME_HEIGHT_SCALE + self.VERTICAL_OFFSET + self.TAP_HEIGHT
        )

        if lane % 2 == 0:
            color = self.TAP_COLOR_1
        else:
            color = self.TAP_COLOR_2

        # print(f"Rendering tap hit object at lane {lane}, time {time}ms, coordinates ({x0}, {y0}, {x1}, {y1})")
        self.drawer.rounded_rectangle(
            (x0, y0, x1, y1), radius=5, fill=color, outline=(0, 0, 0)
        )

    def draw_holds(self, hit_object: beatmap.HitObject) -> None:
        """Renders a hold hit object to the image."""
        x = hit_object.x
        y = hit_object.y
        time = hit_object.time
        lane = x * self.lanes // 512
        end_time = hit_object.payload.end_time  # type: ignore
        duration = end_time - time
        hold_height = self.HOLD_HEIGHT * (duration // 2)
        x0 = lane * self.LANE_WIDTH + self.PADDING + lane * self.LANE_SPACING
        x1 = (lane + 1) * self.LANE_WIDTH + self.PADDING + lane * self.LANE_SPACING
        y1 = self.height - (time * self.TIME_HEIGHT_SCALE + self.VERTICAL_OFFSET)
        y0 = self.height - (
            time * self.TIME_HEIGHT_SCALE + self.VERTICAL_OFFSET + hold_height
        )
        # y0 = self.height - (time * self.TIME_HEIGHT_SCALE + self.VERTICAL_OFFSET + hold_height + self.MIN_HOLD_HEIGHT)

        if lane % 2 == 0:
            color = self.HOLD_COLOR_1
        else:
            color = self.HOLD_COLOR_2

        # print(f"Rendering hold hit object at lane {lane}, time {time}ms, end time {end_time}ms, duration {duration}ms, coordinates ({x0}, {y0}, {x1}, {y1})")
        self.drawer.rounded_rectangle(
            (x0, y0, x1, y1), radius=5, fill=color, outline=(0, 0, 0)
        )

    def draw_timing_points(self, timing_point: beatmap.TimingPoint) -> None:
        """Renders timing points to the image. (after column splitting)"""
        bpm = round(60000 / timing_point.beat_length, 2)  # round to 2 decimal places
        time = timing_point.time
        y = time * self.TIME_HEIGHT_SCALE + self.VERTICAL_OFFSET
        # print(f"original y: {y}")
        column = y // self.MAX_COLUMN_HEIGHT
        y = (column + 1) * self.MAX_COLUMN_HEIGHT - y
        x0 = column * self.column_width
        x1 = x0 + self.column_width
        x_text = x1 - self.COLUMN_SPACING + self.SPLIT_LINE_WEIGHT
        y_text = y - 10  # slightly above the line
        # print(f"Rendering timing point at time {time}ms, BPM {bpm}, coordinates ({x0}, {y}, {x1}, {y}), column {column}")
        self.drawer.line((x0, y, x1, y), fill=(255, 0, 0), width=1)
        self.drawer.text((x_text, y_text), f"{bpm}", fill=(255, 0, 0))

    def draw_inherited_timing_points(
        self, inherited_timing_point: beatmap.InheritedTimingPoint
    ) -> None:
        """Renders inherited timing points to the image. (after column splitting)
        
        unfinished.
        """
        raise NotImplementedError
        scroll_speed = round(
            100 / inherited_timing_point.slider_velocity_multiplier, 2
        )  # round to 2 decimal places
        time = inherited_timing_point.time
        y = time * self.TIME_HEIGHT_SCALE + self.VERTICAL_OFFSET
        column = y // self.MAX_COLUMN_HEIGHT
        y = (column + 1) * self.MAX_COLUMN_HEIGHT - y
        x0 = column * self.column_width
        x1 = x0 + self.column_width
        x_text = x1 - self.COLUMN_SPACING + self.SPLIT_LINE_WEIGHT
        y_text = y - 10  # slightly above the line
        self.drawer.line((x0, y, x1, y), fill=(0, 255, 0), width=1)
        self.drawer.text((x_text, y_text), f"{scroll_speed}%", fill=(0, 255, 0))

    def to_multi_column(self) -> Image.Image:
        """Converts a tall preview image into multiple side-by-side columns."""
        if self.height <= self.MAX_COLUMN_HEIGHT:
            return self.img

        # Split from bottom to top so early timeline appears in the first column.
        columns = (self.height + self.MAX_COLUMN_HEIGHT - 1) // self.MAX_COLUMN_HEIGHT
        new_width = columns * self.width + (columns - 1) * self.COLUMN_SPACING
        new_img = Image.new(
            "RGB", (new_width, self.MAX_COLUMN_HEIGHT), self.BACKGROUND_COLOR
        )

        for col_idx in range(columns):
            src_bottom = self.height - col_idx * self.MAX_COLUMN_HEIGHT
            src_top = max(0, src_bottom - self.MAX_COLUMN_HEIGHT)
            chunk_height = src_bottom - src_top

            chunk = self.img.crop((0, src_top, self.width, src_bottom))
            dest_x = col_idx * (self.width + self.COLUMN_SPACING)
            dest_y = self.MAX_COLUMN_HEIGHT - chunk_height
            new_img.paste(chunk, (dest_x, dest_y))

        # Draw split lines at each column boundary.
        split_draw = ImageDraw.Draw(new_img)
        for boundary_idx in range(1, columns):
            # split_x = (
            #     boundary_idx * self.width
            #     + (boundary_idx - 1) * self.COLUMN_SPACING
            #     + self.COLUMN_SPACING // 2
            # )
            # split_draw.line(
            #     (split_x, 0, split_x, self.MAX_COLUMN_HEIGHT - 1),
            #     fill=self.SPLIT_LINE_COLOR,
            #     width=self.SPLIT_LINE_WEIGHT,
            # )
            split_x1 = (
                boundary_idx * self.width + (boundary_idx - 1) * self.COLUMN_SPACING
            )
            split_x2 = split_x1 + self.COLUMN_SPACING
            split_draw.line(
                (split_x1, 0, split_x1, self.MAX_COLUMN_HEIGHT - 1),
                fill=self.SPLIT_LINE_COLOR,
                width=self.SPLIT_LINE_WEIGHT,
            )
            split_draw.line(
                (split_x2, 0, split_x2, self.MAX_COLUMN_HEIGHT - 1),
                fill=self.SPLIT_LINE_COLOR,
                width=self.SPLIT_LINE_WEIGHT,
            )

        self.img = new_img
        self.width = new_width
        self.height = self.MAX_COLUMN_HEIGHT
        self.drawer = ImageDraw.Draw(self.img)
        return self.img


def main(path):
    beatmap = read_beatmap(path)
    previewer = BeatmapPreviewer(beatmap)
    img = previewer.draw()
    img.save("preview4.png")


if __name__ == "__main__":
    main(r"test\Us4KKi - Aria for Lepus (Arisu Tendou) [save].osu")
