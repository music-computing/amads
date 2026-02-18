## Input

The main function for input is [readscore.read_score](#amads.io.readscore.read_score) described below.
It calls upon various file readers to read Standard MIDI Files and Music XML files.
Much of the work is done by various subsystems including Music21, Partitura, and
pretty_midi. Use `read_score` to get the recommended implementation automatically.

::: amads.io.readscore 


## Output

Similar to input functions, you should use
[writescore.write_score](#amads.io.writescore.write_score) described
below to write an AMADS Score to a file. 

::: amads.io.writescore

## Piano Roll Display

::: amads.io.pianoroll 


## Low-Level Input Functions 

::: amads.io.m21_midi_import.music21_midi_import 

::: amads.io.pm_midi_import.pretty_midi_midi_import 

::: amads.io.m21_xml_import.music21_xml_import 

::: amads.io.pt_xml_import.partitura_xml_import 


## Low-Level Output Functions 

::: amads.io.m21_midi_export.music21_midi_export 

::: amads.io.pm_midi_export.pretty_midi_midi_export 

::: amads.io.m21_xml_export.music21_xml_export 

::: amads.io.pt_xml_export.partitura_xml_export 


## Built-In Scores

::: amads.music.example
