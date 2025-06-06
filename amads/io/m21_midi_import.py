from music21 import converter, metadata, stream

from ..core.basics import Score
from .m21_xml_import import music21_convert_part


def music21_midi_import(
    filename: str, flatten: bool = False, collapse: bool = False, show: bool = False
) -> Score:
    """Use music21 to import a MIDI file and convert it to a Score."""
    # Load the MIDI file using music21
    m21score = converter.parse(
        filename, format="midi", forceSource=True, quantizePost=False
    )

    if show:
        # Print the music21 score structure for debugging
        print(f"Music21 score structure from {filename}:")
        for element in m21score:
            if isinstance(element, metadata.Metadata):
                print(element.all())
        print(m21score.show("text", addEndTimes=True))

    # Create an empty Score object
    score = Score()

    # Iterate over parts in the music21 score
    for m21part in m21score:
        if isinstance(m21part, stream.Part):
            # Convert the music21 part into a part and append it to the Score
            music21_convert_part(m21part, score)
        else:
            print("Ignoring non-Part element:", m21part)

    # this might be optimized by building a flattened score to start with:
    if flatten or collapse:
        score = score.flatten(collapse=collapse)

    return score
