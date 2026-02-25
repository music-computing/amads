# Legacy benchmark values from MIDI toolbox

For a direct comparison of functions in `amads` with those in the `MIDI Toolbox`, a number of basic functions were run in MATLAB using MIDI Toolbox 1.1 with the `sarabande.mid` file included in `amads`.

The script that generated the output is `legacy_benchmark_values_from_miditoolbx.m`. It uses the first 10 notes of the sarabande as input in order to limit the output length of functions that return time series or note transformations.

The script calculates three distributions, twelve summary descriptors, and nine time-series/note-series outputs.

Note that the distributions use Parncutt’s salience modifier for note durations.

The output is structured as a JSON file, `MIDI_toolbox_benchmark_sarabande.json`.

T. Eerola, 15/02/2026
