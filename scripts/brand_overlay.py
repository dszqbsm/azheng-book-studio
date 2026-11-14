from PIL import Image

from chapter_bar import chapter_bar_height


def add_brand_overlay(d, script, asset, materials, width, height, duration, has_chapters):
    with Image.open(asset) as source:
        seal = source.convert("RGBA")
    bounds = seal.getchannel("A").point(lambda value: 255 if value >= 8 else 0).getbbox()
    if bounds is None:
        raise ValueError("Brand seal has no visible pixels")
    seal = seal.crop(bounds)
    seal_height = max(1, round(height * 96 / 1080))
    seal_width = min(max(1, round(seal.width * seal_height / seal.height)), max(1, width // 4))
    seal = seal.resize((seal_width, seal_height), Image.Resampling.LANCZOS)
    margin = max(1, round(height * 24 / 1080))
    top = margin + (chapter_bar_height(height) if has_chapters else 0)
    overlay = Image.new("RGBA", (width, height))
    overlay.alpha_composite(seal, (min(margin, width - seal_width), top))
    path = materials / "azheng-seal-overlay.png"
    overlay.save(path)
    script.append_track(d.TrackSpec(d.TrackType.video, "Brand seal"))
    script.add_segment(d.VideoSegment(d.VideoMaterial(str(path)), d.Timerange(0, duration), volume=0), "Brand seal")
