## Input

The main function for input is [readscore.read_score](#amads.io.readscore.read_score) described below.
It calls upon various file readers to read Standard MIDI Files and Music XML files.
Much of the work is done by various subsystems including Music21, Partitura, and
pretty_midi. Use `readscore` to get the best implementation automatically.

::: amads.io.readscore 


## Output

::: amads.io.readscore 

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
