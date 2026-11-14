"""Build the on-screen chapter bar from the final narration timeline."""
import math
from pathlib import Path

from core import digest, read


def load_chapters(project, path, audio, fps):
    document = read(path)
    if document.get("audio_sha256") != audio["sha256"]:
        raise ValueError("Chapter timeline does not match the final audio")
    if "script_sha256" in document and document["script_sha256"] != digest(project / "script.md"):
        raise ValueError("Chapter timeline does not match the script")
    end = math.ceil(audio["duration"] * fps)
    chapters = []
    for row in document["chapters"]:
        start = row["start"]
        title = row.get("display_title") or row["title"].rsplit("｜", 1)[-1]
        if not isinstance(start, (int, float)) or not math.isfinite(start) or not 0 <= start < audio["duration"]:
            raise ValueError("Invalid chapter start time")
        frame = round(start * fps)
        if frame >= end or (chapters and (start <= chapters[-1][0] or frame <= chapters[-1][1])):
            raise ValueError("Chapter starts must occupy distinct, ordered frames")
        if not title.strip():
            raise ValueError("Empty chapter label")
        chapters.append((start, frame, title.strip()))
    if not chapters or chapters[0][0] != 0:
        raise ValueError("Chapter timeline must begin at zero")
    return [(frame, title) for _, frame, title in chapters], end


def chapter_bar_height(height):
    return max(28, round(height * .075))


def add_chapter_bar(d, script, materials, width, height, fps, chapters, end):
    from PIL import Image, ImageDraw, ImageFont

    def micros(frame):
        return round(frame * 1_000_000 / fps)

    frames = [frame for frame, _ in chapters] + [end]
    edges = [round(width * frame / end) for frame in frames]
    bar_height = chapter_bar_height(height)
    font_path = Path("C:/Windows/Fonts/msyhbd.ttc")
    font = ImageFont.truetype(str(font_path), max(12, round(bar_height * .43)))
    script.append_track(d.TrackSpec(d.TrackType.video, "Chapter bar"))
    script.append_track(d.TrackSpec(d.TrackType.video, "Chapter progress"))
    for active, start in enumerate(frames[:-1]):
        canvas = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(canvas)
        for index, (_, title) in enumerate(chapters):
            left, right = edges[index:index + 2]
            if right <= left:
                continue
            selected = index == active
            draw.rectangle((left, 0, right - 1, bar_height - 1), fill=(26, 24, 21, 224))
            if selected:
                draw.rectangle((left, 0, right - 1, bar_height - 1), fill=(102, 73, 31, 245))
            if index:
                draw.line((left, 0, left, bar_height - 1), fill=(255, 255, 255, 105))
            label = title
            while label and font.getlength(label) > right - left - 12:
                label = label[:-2] + "…" if len(label) > 2 else ""
            if label:
                draw.text(((left + right) / 2, bar_height / 2), label, font=font, anchor="mm",
                          fill=(255, 226, 153) if selected else (244, 242, 237))
        image_path = materials / f"chapter_bar_{active + 1:02}.png"
        canvas.save(image_path)
        duration = micros(frames[active + 1]) - micros(start)
        segment = d.VideoSegment(d.VideoMaterial(str(image_path)), d.Timerange(micros(start), duration), volume=0)
        script.add_segment(segment, "Chapter bar")

    cursor = Image.new("RGBA", (width, height))
    center = width // 2
    radius = max(2, round(height * .005))
    ImageDraw.Draw(cursor).ellipse((center - radius, bar_height - 2 * radius, center + radius, bar_height),
                                  fill=(255, 211, 96))
    cursor_path = materials / "chapter_progress.png"
    cursor.save(cursor_path)
    duration = micros(end)
    segment = d.VideoSegment(d.VideoMaterial(str(cursor_path)), d.Timerange(0, duration), volume=0)
    inset = 2 * radius / width
    segment.add_keyframe(d.KeyframeProperty.position_x, 0, -1 + inset)
    segment.add_keyframe(d.KeyframeProperty.position_x, micros(end - 1), 1 - inset)
    script.add_segment(segment, "Chapter progress")
