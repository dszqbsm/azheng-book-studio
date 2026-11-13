"""Clean already aligned subtitle cues without changing their timing."""
import argparse
import copy
import re
from pathlib import Path

from core import read, save


def caption_boundaries(source, max_quote_chars=30):
    """Return source offsets, required cuts, and display-only quote removals."""
    pairs = {"“": "”", "‘": "’", "「": "」", "『": "』", '"': '"'}
    stack, quotes, remove = [], [], set()
    for i, char in enumerate(source):
        if stack and char == pairs[stack[-1][1]]:
            start, _ = stack.pop()
            quotes.append((start, i))
        elif char in pairs:
            stack.append((i, char))
    protected = set()
    for start, end in quotes:
        quoted = source[start:end + 1]
        if len("".join(quoted.split())) <= max_quote_chars and not re.search(r'[，,；;]', quoted):
            protected.update(range(start + 1, end + 1))
        else:
            remove.update((start, end))
    cuts = {}
    for match in re.finditer(r'[，。！？；：、,.!?;:]+[”’」』"）》】]*|\n+', source):
        end = match.end()
        if end not in protected:
            cuts[end] = bool(re.search(r'[，,；;。！？.!?\n]', match.group()))
    for start, end in quotes:
        if start + 1 in protected and end + 1 not in protected:
            after = end + 1
            while after < len(source) and source[after] in '，。！？；：、,.!?;:':
                after += 1
            if end - start > 12 or source[:start].rstrip().endswith(('：', ':')):
                cuts[start] = cuts[after] = True
    return sorted(cuts.items()), remove


def clean_ending(text):
    return re.sub(r'[，。！？；：、,.!?;:…]+(?=[”’」』）》】]*$)', '', text.rstrip())


def validate_short_cues(cues):
    """Reject internal required cuts that need real timing evidence."""
    for index, cue in enumerate(cues, start=1):
        text = cue['text']
        cuts, _ = caption_boundaries(text)
        for offset, required in cuts:
            if (required and any(char.isalnum() for char in text[:offset])
                    and any(char.isalnum() for char in text[offset:])):
                raise ValueError(
                    f'Subtitle cue {index} crosses a required boundary. '
                    'Split it using the corresponding ASR timestamps before exporting.'
                )


def clean_cues(document):
    result = copy.deepcopy(document)
    previous_end = 0
    for cue in result['cues']:
        start, end = cue['start'], cue['end']
        import math
        if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in (start, end)):
            raise ValueError('Invalid cue timestamps')
        if start < previous_end or end <= start:
            raise ValueError('Overlapping or nonpositive cue timing')
        if not isinstance(cue['text'], str) or not cue['text'].strip():
            raise ValueError('Empty subtitle text')
        cue['text'] = clean_ending(cue['text'])
        if not cue['text']:
            raise ValueError('Cue contains only punctuation')
        previous_end = end
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve() or args.output.exists():
        parser.error('Use a new output file; preserve original aligned cues')
    save(args.output, clean_cues(read(args.input)))
