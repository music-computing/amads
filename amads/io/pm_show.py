"""Functions to show PrettyMIDI score structure for debugging purposes.
<small>**Author**: Roger B. Dannenberg</small>
"""

from pretty_midi import PrettyMIDI

from amads.core.pitch import CHROMATIC_NAMES

__author__ = "Roger B. Dannenberg"


def pretty_midi_show(pmscore: PrettyMIDI, filename: str) -> None:
    # Print the PrettyMIDI score structure for debugging
    print(f"PrettyMIDI score structure for {filename}:")
    print(f"end_time: {pmscore.get_end_time()}")
    if pmscore.key_signature_changes and len(pmscore.key_signature_changes) > 0:
        for sig in pmscore.key_signature_changes:
            key = CHROMATIC_NAMES[sig.key_number % 12]
            key += " major" if sig.key_number < 12 else " minor"
            print(
                f"    KeySignature(time={sig.time},"
                f" key_number={sig.key_number}) {key}"
            )
    if (
        pmscore.time_signature_changes
        and len(pmscore.time_signature_changes) > 0
    ):
        for sig in pmscore.time_signature_changes:
            print(
                f"    TimeSignature(time={sig.time},"
                f" numerator={sig.numerator},"
                f" denominator={sig.denominator})"
            )
    for ins in pmscore.instruments:
        drum_str = ", is_drum" if ins.is_drum else ""
        print(
            f"    Instrument(name={ins.name},"
            f" program={ins.program}{drum_str})"
        )
        if ins.pitch_bends and len(ins.pitch_bends) > 0:
            print(f"        ignoring {len(ins.pitch_bends)} pitch bends")
        if ins.control_changes and len(ins.control_changes) > 0:
            print(
                f"        ignoring {len(ins.control_changes)}"
                " control changes"
            )
        for note in ins.notes:
            print(
                f"        Note(start={note.start},"
                f" duration={note.get_duration()},"
                f" pitch={note.pitch},"
                f" velocity={note.velocity})"
            )
    if pmscore.lyrics and len(pmscore.lyrics) > 0:
        for lyric in pmscore.lyrics:
            print(f"    Lyric(time={lyric.time}, text={lyric.text})")
    if (
        hasattr(pmscore, "text_events")
        and pmscore.text_events
        and len(pmscore.text_events) > 0
    ):
        print("    Text events (not imported by AMADS):")
        for text in pmscore.text_events:
            print(f"        Text(time={text.time}, text={text.text})")
