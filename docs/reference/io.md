## Input

The main function for input is
[readscore.read_score](#amads.io.readscore.read_score) described below.
It calls upon various file readers to read Standard MIDI Files and Music XML
files. Much of the work is done by various subsystems including Music21,
Partitura, and pretty_midi. Use `read_score` to get the recommended
implementation automatically.

::: amads.io.readscore 

## Output

Similar to input functions, you should use 
[writescore.write_score](#amads.io.writescore.write_score) described 
below to write an AMADS Score to a file. 

::: amads.io.writescore

## Display

Similar to output functions, you should use 
[displayscore.display_score](#amads.io.displayscore.display_score) described 
below to display an AMADS Score. You can use Music21 to write directly
to a LilyPond file and use LilyPond to render the file as a PDF, you
can use Music21 or Partitura to write a musicxml file, convert that
with musicxml2ly and render with LilyPond, you can write a musicxml
file and open it with MuseScore, or you can write a musicxml file and
embed it in an HTML file along with Open Sheet Music Display (OSDM)
and open it in a browser.

You will need to install LilyPond and/or MuseScore to use them for
music display. OSDM is installed automatically as part of AMADS.

::: amads.io.displayscore

## Piano Roll Display

::: amads.io.pianoroll 


## Low-Level Input Functions 

::: amads.io.pm_midi_import.pretty_midi_import 

::: amads.io.m21_import.music21_import

::: amads.io.pt_import.partitura_import 


## Low-Level Output Functions 

::: amads.io.pm_midi_export.pretty_midi_export 

::: amads.io.m21_export.music21_export 

::: amads.io.pt_export.partitura_export 

::: amads.io.m21_pdf_export.music21_pdf_export 

::: amads.io.m21_pdf_export.music21_xml_pdf_export 

::: amads.io.pt_pdf_export.partitura_xml_pdf_export


## Built-In Scores

::: amads.music.example
