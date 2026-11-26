import argparse
import sys
from pathlib import Path

from . import __version__, cutlist, subtitles
from .errors import SwearJarError


def find(args):
    video = Path(args.video)
    if not video.is_file():
        raise SwearJarError(f"'{video}' not found")
    output = Path(args.output) if args.output else video.with_name(f"{video.stem}-cuts.txt")
    # Cut lists are edited by hand, so never replace one by accident.
    if output.exists() and not args.force:
        raise SwearJarError(f"'{output}' already exists. Use --force to replace it or -o to pick another name.")

    cues, source = subtitles.load(video, language=args.language, srt=args.srt)
    items = cutlist.entries(cues, cutlist.swear_pattern())
    print(f"Subtitles: {source} ({len(cues)} lines)")
    if not items:
        print("No swear words found; no cut list written.")
        return
    output.write_text(cutlist.render(items), encoding="utf-8")
    print(f"Wrote {len(items)} entries to {output}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="swearjar", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    command = commands.add_parser("find", help="write a cut list from a video's subtitles")
    command.add_argument("video")
    command.add_argument("--srt", help="use this subtitle file")
    command.add_argument("--language", default="en", help="subtitle language (default: en)")
    command.add_argument("-o", "--output", help="cut list to write (default: <video>-cuts.txt)")
    command.add_argument("--force", action="store_true", help="replace an existing cut list")
    command.set_defaults(run=find)

    args = parser.parse_args(argv)
    try:
        args.run(args)
    except SwearJarError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0
