import contextlib
import io
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from swearjar import cli, cutlist, subtitles

SRT = """1
00:00:01,500 --> 00:00:02,200
<i>Oh, shit.</i>

2
00:00:02,300 --> 00:00:03,100
What the
hell?

3
00:00:05,000 --> 00:00:06,000
[banging on door]

4
00:00:07,000 --> 00:00:08,000
Hello, class.
"""


class ParseTest(unittest.TestCase):
    def test_reads_cues_and_strips_markup(self):
        cues = subtitles.parse(SRT.replace("\n", "\r\n"))
        self.assertEqual(cues[0], subtitles.Cue(1.5, 2.2, "Oh, shit."))
        self.assertEqual(cues[1].text, "What the hell?")
        self.assertEqual(len(cues), 4)


class CutListTest(unittest.TestCase):
    def test_merges_overlaps_and_skips_sound_descriptions(self):
        items = cutlist.entries(subtitles.parse(SRT), cutlist.swear_pattern())
        self.assertEqual(cutlist.render(items), "00:00:01 - 00:00:04\tOh, shit. / What the hell?\n")


class ChooseStreamTest(unittest.TestCase):
    def stream(self, index, language=None, codec="subrip", forced=0):
        tags = {"language": language} if language else {}
        return {"index": index, "codec_name": codec, "tags": tags, "disposition": {"forced": forced}}

    def test_skips_other_languages_forced_and_image_tracks(self):
        streams = [
            self.stream(1, "hin"),
            self.stream(2, "eng", forced=1),
            self.stream(3, "eng", codec="hdmv_pgs_subtitle"),
            self.stream(4, "eng"),
        ]
        self.assertEqual(subtitles.choose_stream(streams, "en")["index"], 4)

    def test_untagged_only_when_unambiguous(self):
        self.assertEqual(subtitles.choose_stream([self.stream(1)], "en")["index"], 1)
        self.assertIsNone(subtitles.choose_stream([self.stream(1), self.stream(2)], "en"))


@unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg not installed")
class FindCommandTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        (self.dir / "in.srt").write_text(SRT)
        self.video = self.dir / "movie.mkv"
        subprocess.run([
            "ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=s=64x64:d=9",
            "-i", str(self.dir / "in.srt"), "-map", "0", "-map", "1",
            "-metadata:s:s:0", "language=eng", str(self.video),
        ], check=True)

    def run_cli(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return cli.main(["find", str(self.video), *args])

    def test_writes_list_from_embedded_track_and_keeps_edits(self):
        self.assertEqual(self.run_cli(), 0)
        output = self.dir / "movie-cuts.txt"
        self.assertTrue(output.read_text().startswith("00:00:01 - 00:00:04\t"))
        output.write_text("edited")
        self.assertEqual(self.run_cli(), 1)
        self.assertEqual(output.read_text(), "edited")


if __name__ == "__main__":
    unittest.main()
