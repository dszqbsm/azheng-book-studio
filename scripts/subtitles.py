"""Clean already aligned subtitle cues without changing their timing."""
import argparse
import copy
import re
from pathlib import Path

from core import read, save


def clean_ending(text):
    return re.sub(r'[，。！？；：、,.!?;:…]+(?=[”’」』）》】]*$)', '', text.rstrip())


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
