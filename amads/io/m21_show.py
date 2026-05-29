# m21_show.py - print Music21 score content

from typing import Union

from music21 import metadata, stream


def music21_show(
    m21score: Union[stream.Score, stream.Part], filename: str
) -> None:
    """print Music21 score structure"""
    print("Music21 score structure", end="")
    if filename is not None:
        print(f" for {filename}:")
    else:
        print(":")
    for element in m21score:
        if isinstance(element, metadata.Metadata):
            print(element.all())

    # Print tempo changes
    print("\nTempo changes:")
    tempos = m21score.flatten().getElementsByClass("MetronomeMark")
    if tempos:
        for tempo in tempos:
            print(f"  Offset {tempo.offset}: {tempo.number} BPM")
    else:
        print("  No explicit tempo marks found")

    # Print elements
    print(m21score.show("text", addEndTimes=True))
