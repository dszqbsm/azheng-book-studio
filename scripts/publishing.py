"""Validate all four platform titles against the user's publishing constraints."""
import argparse
import json
import hashlib
import math
from pathlib import Path


def validate_titles(titles):
    config = json.loads((Path(__file__).resolve().parents[1] / 'configs/publishing.json').read_text(encoding='utf-8'))
    if not isinstance(titles, dict):
        raise ValueError('Titles must be a JSON object')
    result = []
    for key, platform in config['platforms'].items():
        title = titles.get(key)
        if not isinstance(title, str) or not title.strip() or any(c in title for c in '\r\n'):
            raise ValueError(f"{platform['name']}: missing or invalid single-line title")
        count = len(title)
        limit = platform['max_characters']
        if limit is not None and count > limit:
            raise ValueError(f"{platform['name']}: {count} characters exceeds {limit}")
        result.append(dict(platform=platform['name'], title=title, characters=count, limit=limit))
    return result


def validate_chapters(document):
    config = json.loads((Path(__file__).resolve().parents[1] / 'configs/publishing.json').read_text(encoding='utf-8'))
    limit = config['chapters']['max_name_characters']
    chapters = document.get('chapters')
    if not isinstance(chapters, list) or not chapters:
        raise ValueError('Missing chapter list')
    result = []
    for chapter in chapters:
        title = chapter.get('title')
        if not isinstance(title, str) or not title.strip() or any(c in title for c in '\r\n'):
            raise ValueError('Missing or invalid chapter name')
        if len(title) > limit:
            raise ValueError(f'Chapter name: {len(title)} characters exceeds {limit}: {title}')
        result.append(dict(title=title, characters=len(title), limit=limit))
    return result


def validate_package(path):
    from PIL import Image
    path = Path(path).resolve()
    project = path.parent.parent
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    titles = validate_titles(data.get('titles'))
    def nonempty(value):
        return isinstance(value, str) and bool(value.strip())
    if not nonempty(data.get('description')):
        raise ValueError('Missing description')
    tags = data.get('tags')
    if not isinstance(tags, list) or not tags or not all(nonempty(t) for t in tags):
        raise ValueError('Missing recommended tags')
    collection = data.get('collection', {})
    if collection.get('action') not in ['existing', 'create', 'suggest_create'] or not all(nonempty(collection.get(k)) for k in ['name', 'description', 'reason']):
        raise ValueError('Missing collection recommendation')
    def local_file(value):
        if not nonempty(value) or Path(value).is_absolute():
            raise ValueError('Expected project-relative file path')
        target = (project / value).resolve()
        if not target.is_relative_to(project) or not target.is_file():
            raise ValueError('Missing project file: ' + value)
        return target
    chapters = json.loads(local_file(data.get('chapters_file')).read_text(encoding='utf-8-sig'))
    validate_chapters(chapters)
    audio = json.loads((project / 'audio/final.json').read_text(encoding='utf-8-sig'))
    if chapters.get('audio_sha256') != audio['sha256'] or chapters.get('script_sha256') != hashlib.sha256((project / 'script.md').read_bytes()).hexdigest():
        raise ValueError('Stale chapter audio/script version')
    duration = chapters.get('duration')
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or abs(duration - audio['duration']) > .1:
        raise ValueError('Chapter duration does not match final audio')
    previous = -1
    for chapter in chapters['chapters']:
        start = chapter.get('start')
        if not isinstance(start, (int, float)) or not math.isfinite(start) or not previous < start < duration:
            raise ValueError('Invalid chapter timestamp ordering')
        seconds = math.floor(start)
        stamp = (f'{seconds//3600:02}:{seconds//60%60:02}:{seconds%60:02}' if duration >= 3600 else f'{seconds//60:02}:{seconds%60:02}')
        if chapter.get('timestamp') != stamp:
            raise ValueError('Chapter timestamp label mismatch')
        previous = start
    if chapters['chapters'][0]['start'] != 0:
        raise ValueError('Missing opening at 00:00')
    config = json.loads((Path(__file__).resolve().parents[1] / 'configs/publishing.json').read_text(encoding='utf-8'))
    if set(data.get('covers', {})) != set(config['covers']['formats']):
        raise ValueError('Exactly two covers required: 3:4 and 4:3')
    cover_paths = {}
    for ratio, size in config['covers']['formats'].items():
        cover = local_file(data['covers'][ratio])
        with Image.open(cover) as image:
            image.verify()
        with Image.open(cover) as image:
            if image.size != (size['width'], size['height']):
                raise ValueError('Incorrect cover dimensions: ' + ratio)
        cover_paths[ratio] = cover
    return data, titles, chapters, cover_paths


def render_package(path):
    data, titles, chapters, covers = validate_package(path)
    lines = ['# 发布包', '', '## 四平台标题', '']
    lines += [f"- {t['platform']}（{t['characters']}字）：{t['title']}" for t in titles]
    lines += ['', '## 简介', '', data['description'], '', '## 推荐标签', '', ' '.join(data['tags']), '', '## 章节', '', '```text']
    lines += [f"{c['timestamp']} {c['title']}" for c in chapters['chapters']]
    c = data['collection']
    action = {'existing': '建议归入已有合集', 'create': '建议新建合集', 'suggest_create': '建议新建（尚未核对已有合集）'}[c['action']]
    lines += ['```', '', '## 合集建议', '', f"{action}：{c['name']}", '', c['description'], '', c['reason'], '', '## 封面', '']
    lines += [f'- [{ratio} 封面]({file.as_posix()})' for ratio, file in covers.items()]
    lines += ['', '基于当前最终配音时间；如发布视频增加片头、删减或变速，需重核章节时间。此包未自动上传或发布。', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--chapters', action='store_true', help='Validate chapter names instead of platform titles')
    modes.add_argument('--package', action='store_true', help='Validate and render the complete publication package')
    parser.add_argument('--output', type=Path, help='Write publication Markdown to a new file')
    args = parser.parse_args()
    try:
        if args.package:
            text = render_package(args.input)
            if args.output:
                with args.output.open('x', encoding='utf-8') as output:
                    output.write(text)
                print(json.dumps({'ok': True, 'output': str(args.output)}, ensure_ascii=False))
            else:
                print(text)
            raise SystemExit(0)
        if args.output:
            raise ValueError('--output requires --package')
        validate = validate_chapters if args.chapters else validate_titles
        print(json.dumps(validate(json.loads(args.input.read_text(encoding='utf-8-sig'))), ensure_ascii=False, indent=2))
    except ValueError as error:
        parser.exit(2, str(error) + '\n')
