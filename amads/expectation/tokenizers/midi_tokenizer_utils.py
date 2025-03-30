"""Files for loading and preprocessing score objects"""
"""Ported and mildly-modified from https://github.com/jazz-style-conditioned-generation/jazz-style-conditioned-generation/blob/main/jazz_style_conditioned_generation/data/tokenizer.py"""
from symusic import Score, Note, Track, Tempo, TimeSignature

OVERLAP_MILLISECONDS = 0  # If two notes with the same pitch have less than this offset-onset time, they will be merged
MIN_DURATION_MILLISECONDS = 50  # We remove notes that have a duration of less than this value


MIDI_PIANO_PROGRAM = 0
PIANO_KEYS = 88
MIDI_OFFSET = 21
MAX_VELOCITY = 127
MIDDLE_C = 60
OCTAVE = 12

# We'll resample input files to use these values
TICKS_PER_QUARTER = 500
TEMPO = 120
TIME_SIGNATURE = 2

MAX_SEQUENCE_LENGTH = 2048  # close to Music Transformer
# This is important: it ensures that two chunks overlap slightly, to allow a causal chain between the
#  end of one chunk and the beginning of the next. The MIDITok default is 1: increasing this seems to work better
CHUNK_OVERLAP_BARS = 8

def get_notes_from_score(score: Score) -> list[Note]:
    """Given a score that may have multiple tracks, we only want to get the notes from the correct (piano) track"""
    # If we somehow have more than one track
    if len(score.tracks) > 1:
        # Combine all notes from all tracks into a single list
        all_notes = []
        for track in score.tracks:
            all_notes.extend(track.notes)
        return sorted(all_notes, key=lambda x: x.start)
    # Otherwise, we can just grab the track directly
    else:
        return sorted(score.tracks[0].notes, key=lambda x: x.start)


def load_score(filepath: str) -> Score:
    """Load a MIDI file and resample it to use millisecond-based timing.
    
    This function loads a MIDI file and resamples it so that 1 tick equals 1 millisecond of real time.
    The process works as follows:
    
    1. Load the MIDI file as a symusic.Score with time in seconds, preserving tempo and time signature
    2. Create a new empty Score with time in ticks, using these fixed parameters:
        - Time signature: 2/4
        - Tempo: 120 BPM  
        - Ticks per quarter: 500
    3. Convert all note timings from seconds to millisecond ticks:
        - 1000 ticks per 2/4 bar
        - Each 2/4 bar lasts exactly 1 second
        - Note timings are rounded to nearest 10ms
    
    When used with MIDITok tokenizer (beat_res={(0,2):50}):
        - Each 2/4 bar gets 100 tokens
        - Each token represents 10ms of time
        - Longer time shifts use multiple sequential tokens
    
    Returns
    -------
    symusic.Score
        Resampled score with millisecond-based timing
    """
    # Load as a symusic object with time sampled in seconds and sort the notes by onset time
    score_as_secs = Score(filepath, ttype="Second")  # this preserves tempo, time signature information etc.
    secs_notes = get_notes_from_score(score_as_secs)
    # Create an EMPTY symusic object with time sampled in ticks
    score_as_ticks = Score(ttype="Tick").resample(tpq=TICKS_PER_QUARTER)
    # Add in required attributes: tracks, tempo, time signatures
    score_as_ticks.tracks = [Track(program=0, ttype="Tick")]
    score_as_ticks.tempos = [Tempo(time=0, qpm=TEMPO, ttype="Tick")]
    score_as_ticks.time_signatures = [
        TimeSignature(time=0, numerator=TIME_SIGNATURE, denominator=4, ttype="Tick")
    ]
    # Iterate over the notes sampled in seconds
    newnotes = []
    for n in secs_notes:
        # Convert their time into ticks/milliseconds
        new_start = base_round(n.time * 1000, 10)  # rounding to the nearest 10 milliseconds
        new_duration = base_round(n.duration * 1000, 10)  # rounding to the nearest 10 milliseconds
        newnote = Note(
            time=new_start,
            duration=new_duration,
            pitch=n.pitch,
            velocity=n.velocity,
            ttype="Tick"
        )
        newnotes.append(newnote)
    # Set the notes correctly
    score_as_ticks.tracks[0].notes = newnotes
    return score_as_ticks


def remove_short_notes(note_list: list[Note], min_duration_milliseconds: int = MIN_DURATION_MILLISECONDS) -> list[Note]:
    """Removes symusic.Note objects with a duration of less than min_duration_milliseconds from a list of Notes"""
    newnotes = []
    for note in note_list:
        # Notes with a duration this short are transcription errors usually
        if note.duration >= min_duration_milliseconds:
            newnotes.append(note)
    return newnotes


def merge_repeated_notes(note_list: list[Note], overlap_milliseconds: int = OVERLAP_MILLISECONDS) -> list[Note]:
    """Merge successive notes at the same pitch with an offset-onset time < overlap_milliseconds to a single note"""
    newnotes = []
    # Iterate over all MIDI pitches
    for pitch in range(MIDI_OFFSET, MIDI_OFFSET + PIANO_KEYS + 1):
        # Get the notes played at this pitch
        notes_at_pitch = [note for note in note_list if note.pitch == pitch]
        # If this pitch only appears once
        if len(notes_at_pitch) < 2:
            # We can just use it straight away
            newnotes.extend(notes_at_pitch)
        # Otherwise, if we have multiple appearances of this pitch
        else:
            # Sort notes by onset time
            notes_sorted = sorted(notes_at_pitch, key=lambda x: x.time)
            seen_notes = []  # Tracks already processed notes
            # Iterate over successive pairs of notes (note1, note2), (note2, note3)...
            for note_idx in range(len(notes_sorted) - 1):
                # Unpack to get desired notes
                note1 = notes_sorted[note_idx]
                note2 = notes_sorted[note_idx + 1]
                # Check if this note pair has already been merged and processed
                if note1 in seen_notes:
                    continue
                # Unpack everything
                note1_end = note1.time + note1.duration
                note2_start = note2.time
                overlap = note2_start - note1_end
                # If the overlap between these two notes is short
                if overlap < overlap_milliseconds:
                    # Combine both notes into a single note
                    newnote = Note(
                        # Just use the onset time of the earliest note
                        time=note1.time,
                        # Combine the durations of both notes + the overlap duration
                        duration=note1.duration + overlap + note2.duration,
                        # Pitch should just be the same
                        pitch=note1.pitch,
                        # Take the midpoint of both velocity values
                        velocity=(note1.velocity + note2.velocity) // 2,
                        ttype=note1.ttype
                    )
                    newnotes.append(newnote)
                    seen_notes.append(note1)  # Mark note1 as processed
                    seen_notes.append(note2)  # Mark note2 as processed
                else:
                    # No overlap, append note1 to the newnotes list
                    newnotes.append(note1)
                    seen_notes.append(note1)  # Mark note1 as processed
            # Ensure the last note is added (it might not be part of any overlap)
            if notes_sorted[-1] not in seen_notes:
                newnotes.append(notes_sorted[-1])
    return newnotes


def remove_out_of_range_notes(note_list: list[Note]) -> list[Note]:
    """Remove notes from a list that are outside the range of the piano keyboard"""
    return [n for n in note_list if MIDI_OFFSET <= n.pitch <= MIDI_OFFSET + PIANO_KEYS]


def note_list_to_score(note_list: list[Note], ticks_per_quarter: int) -> Score:
    """Converts a list of symusic.Note objects to a single symusic.Score"""
    # This API is fairly similar to pretty_midi
    newscore = Score()
    newscore.ticks_per_quarter = ticks_per_quarter
    newscore.tracks = [Track()]
    newscore.tracks[0].notes = note_list
    return newscore


def preprocess_score(
        score: Score,
        min_duration_milliseconds: int = MIN_DURATION_MILLISECONDS,
        overlap_milliseconds: int = OVERLAP_MILLISECONDS
) -> Score:
    """Applies our own preprocessing to a Score object: removes short notes, merges duplicates"""
    # Get the notes from the score
    note_list = get_notes_from_score(score)
    # First, we remove notes that are outside the range of the piano keyboard
    validated_notes = remove_out_of_range_notes(note_list)
    # Then, we remove notes with a very short duration
    no_short_notes = remove_short_notes(validated_notes, min_duration_milliseconds=min_duration_milliseconds)
    # Next, we merge successive notes with the same pitch and a very short onset-offset time into the same pitch
    merged_notes = merge_repeated_notes(no_short_notes, overlap_milliseconds=overlap_milliseconds)
    # Finally, we convert everything back to a Score object that can be passed to our tokenizer
    score.tracks[0].notes = sorted(merged_notes, key=lambda x: x.start)
    return score

def base_round(x: float, base: int = 10) -> int:
    """Rounds a number to the nearest base"""
    return int(base * round(float(x) / base))


# if __name__ == "__main__":
#     import os

#     from miditok import MIDILike, TokenizerConfig

#     from jazz_style_conditioned_generation.data.tokenizer import DEFAULT_TOKENIZER_CONFIG

#     file = "data/raw/pijama/mehldaub-blackbirdlive-unaccompanied-xxxx-wf4yk8ao/piano_midi.mid"
#     mf = os.path.join(utils.get_project_root(), file)
#     loaded = load_score(mf)

#     tokenizer = MIDILike(TokenizerConfig(**DEFAULT_TOKENIZER_CONFIG))

#     preproc = preprocess_score(loaded)
#     enc = tokenizer.encode(preproc)
#     dec = tokenizer.decode(enc)
#     dec.dump_midi(os.path.join(utils.get_project_root(), f"preproc_bbird.mid"))