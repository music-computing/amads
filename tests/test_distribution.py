import matplotlib
import numpy as np
import pytest

from amads.core.distribution import Distribution
from amads.core.pitch import Pitch

matplotlib.use("Agg")


def make_1d(data=(0.2, 0.3, 0.5), categories=("a", "b", "c")):
    return Distribution(
        name="test",
        data=list(data),
        distribution_type="pitch_class",
        dimensions=[len(data)],
        x_categories=list(categories),
        x_label="x",
        y_categories=None,
        y_label="y",
    )


def make_2d():
    data = [[1, 2], [3, 4]]
    return Distribution(
        name="test2d",
        data=data,
        distribution_type="interval_transition",
        dimensions=[2, 2],
        x_categories=["x0", "x1"],
        x_label="x",
        y_categories=["y0", "y1"],
        y_label="y",
    )


# ---------------------------------------------------------------------------

# __init__ / _validate


def test_valid_1d_construction_ok():
    d = make_1d()
    assert d.dimensions == [3]


def test_valid_2d_construction_ok():
    d = make_2d()
    assert d.dimensions == [2, 2]


def test_bad_dims_length_raises():
    with pytest.raises(ValueError):
        Distribution(
            name="bad",
            data=[[[1]]],
            distribution_type="x",
            dimensions=[1, 1, 1],
            x_categories=["a"],
            x_label="x",
            y_categories=None,
            y_label="y",
        )


def test_data_shape_mismatch_raises():
    with pytest.raises(ValueError):
        Distribution(
            name="bad",
            data=[0.1, 0.2],  # length 2
            distribution_type="pitch_class",
            dimensions=[3],  # says length 3
            x_categories=["a", "b", "c"],
            x_label="x",
            y_categories=None,
            y_label="y",
        )


def test_x_categories_length_mismatch_raises():
    with pytest.raises(ValueError):
        Distribution(
            name="bad",
            data=[0.1, 0.2, 0.7],
            distribution_type="pitch_class",
            dimensions=[3],
            x_categories=["a", "b"],  # only 2, need 3
            x_label="x",
            y_categories=None,
            y_label="y",
        )


def test_1d_with_y_categories_raises():
    with pytest.raises(ValueError):
        Distribution(
            name="bad",
            data=[0.1, 0.2, 0.7],
            distribution_type="pitch_class",
            dimensions=[3],
            x_categories=["a", "b", "c"],
            x_label="x",
            y_categories=["should", "not", "exist"],
            y_label="y",
        )


def test_2d_without_y_categories_raises():
    with pytest.raises(ValueError):
        Distribution(
            name="bad",
            data=[[1, 2], [3, 4]],
            distribution_type="interval_transition",
            dimensions=[2, 2],
            x_categories=["x0", "x1"],
            x_label="x",
            y_categories=None,  # required for 2-D
            y_label="y",
        )


def test_2d_y_categories_length_mismatch_raises():
    with pytest.raises(ValueError):
        Distribution(
            name="bad",
            data=[[1, 2], [3, 4]],
            distribution_type="interval_transition",
            dimensions=[2, 2],
            x_categories=["x0", "x1"],
            x_label="x",
            y_categories=["y0"],  # need 2
            y_label="y",
        )


# ---------------------------------------------------------------------------

# normalize


def test_normalize_default_sum_1d():
    d = make_1d(data=(1, 2, 3, 4), categories=("a", "b", "c", "d"))
    d.normalize()
    assert d.data == pytest.approx([0.1, 0.2, 0.3, 0.4])
    assert sum(d.data) == pytest.approx(1.0)


def test_normalize_2d_sums_whole_matrix_by_default():
    d = make_2d()  # data = [[1, 2], [3, 4]], total = 10
    d.normalize()
    flat = [v for row in d.data for v in row]
    assert sum(flat) == pytest.approx(1.0)
    assert flat == pytest.approx([0.1, 0.2, 0.3, 0.4])


def test_normalize_accepts_alternate_method():
    d = make_1d(data=(3, 4), categories=("a", "b"))
    d.normalize(method="Euclidean")
    norm = np.linalg.norm(d.data)
    assert norm == pytest.approx(1.0)


def test_normalize_returns_self_for_chaining():
    d = make_1d()
    assert d.normalize() is d


# ---------------------------------------------------------------------------

# from_pitches


def test_from_pitches_empty_raises():
    with pytest.raises(ValueError):
        Distribution.from_pitches([])


def test_from_pitches_mismatched_weights_raises():
    with pytest.raises(ValueError):
        Distribution.from_pitches([60, 62, 64], weights=[1, 1])


def test_from_pitches_bad_entry_type_raises():
    with pytest.raises(ValueError):
        Distribution.from_pitches([60, "not a pitch"])


def test_from_pitches_unpitched_raises():
    with pytest.raises(ValueError):
        Distribution.from_pitches([Pitch(None)])


def test_from_pitches_use_spelling_requires_all_pitch_objects():
    with pytest.raises(ValueError):
        Distribution.from_pitches([60, 62], use_spelling=True)


def test_from_pitches_raw_numbers_uses_midi_labels():
    dist = Distribution.from_pitches([60, 62, 64], buffer=0)
    assert dist.distribution_type == "pitch"
    assert dist.dimensions == [5]  # 60..64 inclusive
    assert dist.x_categories == ["60", "61", "62", "63", "64"]
    assert dist.data == [1.0, 0.0, 1.0, 0.0, 1.0]


def test_from_pitches_buffer_extends_range():
    dist = Distribution.from_pitches([60, 64], buffer=2)
    assert dist.x_categories[0] == "58"
    assert dist.x_categories[-1] == "66"


def test_from_pitches_pitch_objects_default_to_spelling():
    # D4 (61) and F4 (65) are never observed, so they fall back to
    # their MIDI numbers -- only observed pitches get spelled labels.
    notes = [Pitch("C4"), Pitch("E4"), Pitch("G4")]
    dist = Distribution.from_pitches(notes, buffer=0)
    assert dist.x_categories == [
        "C4",
        "61",
        "62",
        "63",
        "E4",
        "65",
        "66",
        "G4",
    ]


def test_from_pitches_use_spelling_false_forces_midi_numbers():
    notes = [Pitch("C4"), Pitch("E4")]
    dist = Distribution.from_pitches(notes, buffer=0, use_spelling=False)
    assert dist.x_categories == [str(n) for n in range(60, 65)]


def test_from_pitches_weights_are_applied():
    dist = Distribution.from_pitches([60, 60, 62], weights=[1, 2, 5], buffer=0)
    assert dist.data == [3.0, 0.0, 5.0]
    assert dist.y_label == "Weight"


def test_from_pitches_default_weight_label_is_count():
    dist = Distribution.from_pitches([60], buffer=0)
    assert dist.y_label == "Count"


def test_from_pitches_wide_range_thins_labels_to_one_per_octave():
    # Span of 36 semitones triggers thinning (> PITCH_WIDE_RANGE_SEMITONES).
    dist = Distribution.from_pitches([40, 76], buffer=0)
    assert dist.x_categories[0] == "40"
    assert dist.x_categories[12] == "52"
    assert dist.x_categories[24] == "64"
    assert dist.x_categories[-1] == "76"
    # everything else is blanked out
    kept = {0, 12, 24, 36}
    for i, label in enumerate(dist.x_categories):
        if i not in kept:
            assert label == ""
    # underlying data is untouched by the label-thinning
    assert len(dist.data) == len(dist.x_categories)


def test_from_pitches_narrow_range_keeps_every_label():
    dist = Distribution.from_pitches([60, 64], buffer=0)  # span of 4
    assert "" not in dist.x_categories


def test_from_pitches_mixed_pitch_and_raw_numbers_ok_without_spelling():
    dist = Distribution.from_pitches([Pitch("C4"), 64], buffer=0)
    assert dist.x_categories == [str(n) for n in range(60, 65)]


def test_from_pitches_plot_defaults_to_line():
    dist = Distribution.from_pitches([60, 62, 64], buffer=0)
    fig = dist.plot(show=False)
    ax = fig.axes[0]
    assert len(ax.lines) == 1
    assert len(ax.patches) == 0  # no bars drawn


# ---------------------------------------------------------------------------

# plot_grouped_1d bar-offset arithmetic


def _bar_centers_for_n(n):
    """Build n single-category 1-D bar distributions and return the
    x-position (center) matplotlib actually drew each bar at."""
    dists = [
        Distribution(
            name=f"d{i}",
            data=[1.0],
            distribution_type="pitch_class",
            dimensions=[1],
            x_categories=["only"],
            x_label="x",
            y_categories=None,
            y_label="y",
        )
        for i in range(n)
    ]
    fig = Distribution.plot_grouped_1d(dists, show=False, options="bar")
    ax = fig.axes[0]
    centers = sorted(p.get_x() + p.get_width() / 2 for p in ax.patches)
    return centers


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6])
def test_plot_grouped_1d_bar_offsets_are_symmetric_and_unit_spaced(n):
    centers = _bar_centers_for_n(n)
    assert len(centers) == n
    expected = sorted(i - (n - 1) / 2 for i in range(n))
    assert centers == pytest.approx(expected)


def test_plot_grouped_1d_empty_returns_none():
    assert Distribution.plot_grouped_1d([]) is None


def test_plot_grouped_1d_rejects_mismatched_shapes():
    d1 = make_1d(data=(0.5, 0.5), categories=("a", "b"))
    d2 = make_1d(data=(0.3, 0.3, 0.4), categories=("a", "b", "c"))
    with pytest.raises(ValueError):
        Distribution.plot_grouped_1d([d1, d2], show=False)
