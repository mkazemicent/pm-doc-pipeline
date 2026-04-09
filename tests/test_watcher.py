from src.watcher import PipelineWatcher


def test_scan_detects_new_supported_file(tmp_path):
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    watcher = PipelineWatcher(watch_dir, tmp_path / "config.yaml", tmp_path)

    # First scan: empty.
    assert watcher.scan_once() == []

    # Add a supported file.
    (watch_dir / "notes.md").write_text("# Notes", encoding="utf-8")
    changed = watcher.scan_once()

    assert len(changed) == 1
    assert changed[0].name == "notes.md"


def test_scan_ignores_unsupported_extensions(tmp_path):
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    watcher = PipelineWatcher(watch_dir, tmp_path / "config.yaml", tmp_path)

    (watch_dir / "photo.jpg").write_text("fake", encoding="utf-8")
    (watch_dir / "data.csv").write_text("a,b,c", encoding="utf-8")

    assert watcher.scan_once() == []


def test_scan_detects_modification(tmp_path):
    import time

    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    watcher = PipelineWatcher(watch_dir, tmp_path / "config.yaml", tmp_path)

    watched_file = watch_dir / "notes.md"
    watched_file.write_text("# V1", encoding="utf-8")
    watcher.scan_once()  # baseline

    time.sleep(0.1)  # ensure mtime differs
    watched_file.write_text("# V2", encoding="utf-8")
    changed = watcher.scan_once()

    assert len(changed) == 1
    assert changed[0].name == "notes.md"


def test_scan_no_change_on_second_scan(tmp_path):
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    watcher = PipelineWatcher(watch_dir, tmp_path / "config.yaml", tmp_path)

    (watch_dir / "notes.md").write_text("# Notes", encoding="utf-8")
    watcher.scan_once()  # first scan picks it up
    changed = watcher.scan_once()  # second scan: no change

    assert changed == []


def test_scan_nonexistent_dir(tmp_path):
    watcher = PipelineWatcher(tmp_path / "nope", tmp_path / "config.yaml", tmp_path)

    assert watcher.scan_once() == []
