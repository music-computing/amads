from partitura import save_score_midi

from amads.core.basics import Score
from amads.io.pt_xml_export import score_to_partitura

# DIVS = 480  # divisions per quarter note for Partitura MIDI export

# def get_partitura_notes(part: Part) -> list[dict]:
#     """Extract notes from an AMADS Part and convert to Partitura note dicts."""
#     notes = part.find_all(Note)
#     ptnotes = []
#     for note_event in notes:
#         note_event = cast(Note, note_event)
#         if note_event.pitch is None:
#             pt_note = ptNote()  # rest
#         else:
#             pt_note = ptNote(
#                 step=note_event.step,
#                 octave=note_event.octave,
#                 alter=note_event.pitch.alt,
#                 staff=note_event.staff,
#             )  # type: ignore
#         onset_divs = round(note_event.onset * DIVS)
#         duration_divs = round((note_event.offset - note_event.onset) * DIVS)
#         ptnotes.append(
#             {
#                 "note": pt_note,
#                 "onset_divs": onset_divs,
#                 "duration_divs": duration_divs,
#             }
#         )
#     for staff in part.find_all(Staff):
#         staff = cast(Staff, staff)
#         for note_event in staff.find_all(Note):
#             note_event = cast(Note, note_event)
#             if note_event.pitch is None:
#                 pt_note = ptNote()  # rest
#             else:
#                 pt_note = ptNote(
#                     step=note_event.step,
#                     octave=note_event.octave,
#                     alter=note_event.pitch.alt,
#                     staff=staff.number,
#                 )  # type: ignore
#             onset_divs = round(note_event.onset * DIVS)
#             duration_divs = round((note_event.offset - note_event.onset) * DIVS)
#             notes.append(
#                 {
#                     "note": pt_note,
#                     "onset_divs": onset_divs,
#                     "duration_divs": duration_divs,
#                 }
#             )
#     return notes


# def score_to_partitura_perf(score: Score,
#     show: bool = False,
# ) -> ptScore:
#     """Convert an AMADS Score to a Partitura PerformedPart."""
#     parts = []
#     previous_part_number = 0
#     for part in score.find_all(Part):
#         part = cast(Part, part)
#         part_number = part.number
#         if part_number is None:
#             previous_part_number += 1
#             part_number = previous_part_number
#         else:
#             part_number = int(part_number)
#             previous_part_number = max(previous_part_number, part_number)
#         notes = get_partitura_notes(part)
#         key_signatures = get_partitura_key_signatures(part)
#         time_signatures = get_partitura_time_signatures(part)
#         pt_part = ptPart(notes, part_number, part.instrument,
#                          key_signature=key_signatures,
#                          time_signature=time_signatures,
#                          track=part_number)
#         parts.append(pt_part)
#     if show:
#         print("Partitura Performance:)
#         print("------- here are the performance parts -------")
#         for ptpart in parts:
#             print(ptpart.__class__)
#             print(ptpart.pretty())
#     return parts


def partitura_midi_export(
    score: Score,
    filename: str,
    show: bool = False,
) -> None:
    """Use Partitura to export a Score to a Standard MIDI file.

    Parameters
    ----------
    score : Score
        The Score to export.
    filename : str
        The name of the file to save the MIDI data.
    show : bool, optional
        If True, print the Partitura score structure for debugging.
    """
    pt_score = score_to_partitura(score, show)
    save_score_midi(pt_score, filename)
