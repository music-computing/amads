# Design

Here are some notes on the implementation of a fairly complex set of possibilities.

## writescore

### Low-level conversion

- In `m21_export.py`
  - `_score_to_music21`
- In `m21_pdf_export.py`
  - `_music21_to_lilypond`
- In `xml_lilypond_pdf.py`
  - `_lilypond_to_pdf`
  - `_musicxml_to_lilypond`
- In `pt_export.py`
  - `_score_to_partitura`
- In `pm_midi_export.py`
  Since the only thing you can do with PrettyMIDI is export a MIDI
  file, `pm_midi_export.py` only implements the mid-level function
  `pretty_midi_export`.
  
  
### Mid-level output
To get from `write_score` to low-level conversion functions, we use the format 
to determine which preference to use:
- `preferred_midi_writer` ("music21" or "pretty_midi")
- `preferred_xml_writer` ("music21" or "partitura")
- `preferred_kern_writer` ("music21")
- `preferred_mei_writer` ("music21")
- `preferred_pdf_writer` ("music21-lilypond", "music21-xml-lilypond", or 
                          "partitura-xml-lilypond")
and then we use `allowed_subsystems` to check that the preference is allowed,
and then `_subsystem_map` tells us what module to load and what export
function to call.

The export function then calls upon low-level conversion functions to do the 
work.

The modules and export functions are:
- For "music21": `m21_export`, `music21_export`
- For "pretty\_midi": `pm_midi_export`, `pretty_midi_export`
- For "partitura": `pt_export`, `partitura_export`),
- For "music21-lilypond": `m21_pdf_export`, `music21_pdf_export`),
- For "music21-xml-lilypond": `m21_pdf_export`, `music21_xml_pdf_export`
- For "partitura-xml-lilypond": `pt_pdf_export`, `partitura_xml_pdf_export`

The API for all these export functions is:
```python
export_fn(score, filename, format, show)
```
where score is an AMADS Score, filename is the file path (str),
format is optional and implied by filename if format is missing,
and show requests a text output of the intermediate Music21,
Partitura, or PrettyMIDI representation.

### High-level output

- In `writescore.py`
  - `write_score`


# displayscore

### Low-level conversion

### Mid-level output

### High-level output
Options, controlled by the value of `preferred_display_method` are
"pdf", "musescore", or "OSMD". These are implemented directly in the
`display_score` and `display_file` functions.


- In `displayscore.py`
  - `display_score`
  - `display_file`

