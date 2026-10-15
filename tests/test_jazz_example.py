"""Run the jazz example offline with real MIDI and classification code."""

import random
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

import matplotlib.pyplot as plt
import mido
import numpy as np
import pytest


@pytest.fixture(scope="module")
def jazz_example(tmp_path_factory):
    directory = tmp_path_factory.mktemp("jazz-example")
    tracks = {}
    for musician, base_pitch in [("Bill Evans", 60), ("Oscar Peterson", 72)]:
        for index in range(10):
            path = directory / f"{base_pitch}-{index}.mid"
            midi = mido.MidiFile(ticks_per_beat=480)
            track = mido.MidiTrack()
            midi.tracks.append(track)
            track.append(mido.MetaMessage("set_tempo", tempo=500000))
            previous_tick = 0
            for note_index in range(4):
                onset = 288 + 480 * note_index + 8 * (index % 3)
                track.append(
                    mido.Message(
                        "note_on",
                        note=base_pitch + note_index,
                        velocity=80,
                        time=onset - previous_tick,
                    )
                )
                track.append(
                    mido.Message(
                        "note_off", note=base_pitch + note_index, time=96
                    )
                )
                previous_tick = onset + 96
            midi.save(path)
            tracks[path.stem] = SimpleNamespace(
                piano=SimpleNamespace(musician=musician, midi_path=str(path)),
                beats=SimpleNamespace(times=np.arange(0, 2.5, 0.5)),
            )

    dataset = SimpleNamespace(
        download=lambda: None,
        load_tracks=lambda: {},
        load_multitracks=lambda: tracks,
        choice_track=lambda: "Synthetic piano track",
        mtrack_ids=list(tracks),
    )
    example = Path(__file__).parents[1] / "examples/plot_jazz_recordings.py"
    numpy_state = np.random.get_state()
    random_state = random.getstate()
    try:
        with pytest.MonkeyPatch.context() as patch:
            patch.setitem(
                sys.modules,
                "mirdata",
                SimpleNamespace(initialize=lambda name: dataset),
            )
            patch.setattr(plt, "show", lambda: None)
            result = runpy.run_path(str(example), run_name="__main__")
        yield result, tracks
    finally:
        np.random.set_state(numpy_state)
        random.setstate(random_state)
        plt.close("all")


def test_jazz_example_reads_midi_onsets_in_seconds(jazz_example):
    example, tracks = jazz_example
    pitches, onsets, beats = example["load_track_annotations"](tracks["60-0"])
    assert pitches == [60, 61, 62, 63]
    np.testing.assert_allclose(onsets, [0.3, 0.8, 1.3, 1.8])
    np.testing.assert_allclose(beats, [0, 0.5, 1, 1.5, 2])


def test_jazz_example_uses_beats_then_upbeats(jazz_example):
    example, _ = jazz_example
    mean, std, slope, tempo = example["rhythm_features"](
        [0.6, 1.6, 2.6], [0, 1, 2, 3]
    )
    assert mean == pytest.approx(np.log2(1.5))
    assert std == pytest.approx(0)
    assert slope == pytest.approx(0)
    assert tempo == pytest.approx(60)


def test_jazz_example_fits_preprocessing_on_training_data(jazz_example):
    example, _ = jazz_example
    model = example["model"]
    training = example["X_train"]
    imputer = model.named_steps["simpleimputer"]
    np.testing.assert_allclose(
        imputer.statistics_, np.nanmean(training, axis=0)
    )
    np.testing.assert_allclose(
        model.named_steps["standardscaler"].mean_,
        imputer.transform(training).mean(axis=0),
    )
    assert model.named_steps["logisticregression"].coef_.shape == (1, 7)
    assert model.predict(example["X_test"]).shape == example["y_test"].shape


def test_jazz_example_handles_entirely_missing_features(jazz_example):
    from sklearn.base import clone

    example, _ = jazz_example
    training = example["X_train"].copy()
    training[:, 3:5] = np.nan
    model = clone(example["model"]).fit(training, example["y_train"])
    assert model.named_steps["logisticregression"].coef_.shape == (1, 7)
    assert np.isfinite(model.predict_proba(training)).all()


def test_jazz_example_handles_all_burs_filtered_out(jazz_example):
    example, _ = jazz_example
    mean, std, _, _ = example["rhythm_features"](
        [0.01, 1.01, 2.01], [0, 1, 2, 3]
    )
    assert np.isnan(mean)
    assert np.isnan(std)


def test_jazz_example_uses_separate_figures(jazz_example):
    example, _ = jazz_example
    assert example["disp"].figure_ is not example["fig"]
    assert example["disp"].ax_ is not example["ax"]
    assert len(example["ax"].patches) == 7
