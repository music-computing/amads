from music21 import converter, stream, note, chord

def music21_midi_import(filename, m21print=False):
    """
    Import a MIDI file using Music21.
    
    Parameters:
    - filename (str): Path to the MIDI file.
    - m21print (bool): If True, prints the musical parts in textual format.
    
    Returns:
    - score (music21.stream.Score): A Music21 score object containing the imported parts.
    """
    # Parse the MIDI file into a Music21 stream object
    midi_stream = converter.parse(filename)
    
    # Optionally display the parsed stream as text (helpful for debugging or inspection)
    if m21print:
        midi_stream.show('text')
    
    # Create a new empty score to hold all parts
    score = stream.Score()

    # Iterate through each part in the parsed MIDI stream
    for part in midi_stream.parts:
        # Create a new empty part to hold notes and rests from the current part
        new_part = stream.Part()
        
        # Flatten the part to make all notes and rests accessible in sequence
        # (ignores hierarchical structure like measures for simplicity)
        for element in part.flat.notesAndRests:
            # Append each note or rest to the new part
            new_part.append(element)
        
        # Add the fully populated part to the score
        score.append(new_part)

    # Return the fully constructed score containing all parts
    return score
