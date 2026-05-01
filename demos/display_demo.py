# display_demo.py - display an AMADS score using various methods

from amads.io.displayscore import (
    display_score,
    preferred_display_method,
    set_preferred_display_method,
)
from amads.io.readscore import read_score
from amads.io.writescore import preferred_pdf_writer, set_preferred_pdf_writer
from amads.music import example


def main() -> None:
    """Read an example score, convert through music21, and display it."""
    xml_file = example.fullpath("musicxml/short2staff.mxl")
    assert xml_file is not None

    score = read_score(xml_file)

    assert (
        preferred_pdf_writer == "music21-xml-lilypond"
    ), "Preferred PDF writer must be 'music21-xml-lilypond' for this demo."
    assert (
        preferred_display_method == "pdf"
    ), "Preferred display method must be 'pdf' for this demo."

    default_display_method = preferred_display_method

    # display with Open Sheet Music Display (OSMD)
    set_preferred_display_method("OSMD")
    display_score(score)

    # convert to lilypond using music21, then use LilyPond to create a PDF
    set_preferred_display_method("pdf")
    # When the display method is "pdf", there are multiple PDF writers/methods
    #   available, set by calling set_preferred_pdf_writer.  We will try each
    #   of the three available PDF writers in turn, and then restore the
    #   default at the end.
    # Convert to .ly file with music21's built-in LilyPond converter, then
    #   use LilyPond to create a PDF to display:
    default_pdf_writer = set_preferred_pdf_writer("music21-lilypond")
    display_score(score)

    # convert to XML with music21, then use musicxml2ly to create a .ly file,
    #   then use LilyPond to create a PDF to display:
    set_preferred_pdf_writer("music21-xml-lilypond")
    display_score(score)

    # convert to XML with partitura, then use musicxml2ly to create a .ly file,
    #   then use LilyPond to create a PDF to display:
    set_preferred_pdf_writer("partitura-xml-lilypond")
    display_score(score)

    # display with MuseScore
    set_preferred_display_method("musescore")
    display_score(score)

    # display with MuseScore
    set_preferred_display_method("pianoroll")
    display_score(score)

    # restore defaults
    set_preferred_pdf_writer(default_pdf_writer)
    set_preferred_display_method(default_display_method)


if __name__ == "__main__":
    main()
