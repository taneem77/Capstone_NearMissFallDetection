"""KFall replay source. Reads <sensor_dir>/SAxx/SxxTyyRzz.csv + <label_dir>/SAxx_label.xlsx."""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Iterable, Iterator, Optional

from ..io import Recording, parse_name, read_labels, read_sensor_csv
from .base import Source


class KFallSource(Source):
    def __init__(self, sensor_dir, label_dir, subjects: Optional[Iterable[str]] = None,
                 tasks: Optional[Iterable[int]] = None, cache_dir=None):
        self.sensor_dir, self.label_dir = Path(sensor_dir), Path(label_dir)
        self.subjects_filter = set(subjects) if subjects else None
        self.tasks_filter = set(tasks) if tasks else None
        self.cache_dir = Path(cache_dir) if cache_dir else None

    def _subject_dirs(self):
        for d in sorted(self.sensor_dir.glob("SA*")):
            if d.is_dir() and (self.subjects_filter is None or d.name in self.subjects_filter):
                yield d

    def _load_subject(self, d: Path) -> list[Recording]:
        cache = self.cache_dir / f"{d.name}.pkl" if self.cache_dir else None
        if cache and cache.exists():
            recs = pickle.loads(cache.read_bytes())
        else:
            lab_file = self.label_dir / f"{d.name}_label.xlsx"
            labels = read_labels(lab_file) if lab_file.exists() else {}
            recs = []
            for f in sorted(d.glob("S*T*R*.csv")):
                _, task, trial = parse_name(f)
                raw = read_sensor_csv(f)
                on, im = labels.get((task, trial), (None, None))
                recs.append(Recording(subject=d.name, task=task, trial=trial, fs=raw["fs"],
                                      acc=raw["acc"], gyro=raw["gyro"],
                                      fall_onset=on, fall_impact=im))
            if cache:
                cache.parent.mkdir(parents=True, exist_ok=True)
                cache.write_bytes(pickle.dumps(recs))
        if self.tasks_filter:
            recs = [r for r in recs if r.task in self.tasks_filter]
        return recs

    def recordings(self) -> Iterator[Recording]:
        for d in self._subject_dirs():
            yield from self._load_subject(d)
