"""Basic tests for the Universal Translator."""

from pathlib import Path
from src.translator.html_converter import HTMLToMarkdown


def test_html_to_markdown_basic():
    converter = HTMLToMarkdown()
    html = "<h1>Title</h1><p>Hello <strong>world</strong></p>"
    md = converter.convert(html)
    assert "# Title" in md
    assert "**world**" in md


def test_html_to_markdown_cleans_extra_newlines():
    converter = HTMLToMarkdown()
    html = "<p>A</p><br><br><br><br><p>B</p>"
    md = converter.convert(html)
    assert "\n\n\n" not in md


def test_vtt_to_markdown():
    from src.translator.translator import UniversalTranslator

    vtt_content = """WEBVTT

1
00:00:01.000 --> 00:00:05.000
<v Alice>Hello everyone, let's get started.

2
00:00:05.000 --> 00:00:10.000
<v Bob>Sounds good, I have the agenda ready.
"""
    tmp = Path("/tmp/test_transcript.vtt")
    tmp.write_text(vtt_content)
    result = UniversalTranslator._vtt_to_md(tmp)
    assert "Alice" in result
    assert "Bob" in result
    assert "agenda" in result
    tmp.unlink()
