"""
Provides the `midi2hz` function.

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&
              doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=50
"""

def _convert_Midi_to_Hz(singleMidiNoteNumber):
        """
        Convert a single MIDI note number to frequency in Hz.

        Parameters
        ----------
        singleMidiNoteNumber : float
            A non-negative MIDI note number.

        Returns
        -------
        float
            Frequency in Hz corresponding to the given MIDI note number.

        Raises
        ------
        ValueError
            If the MIDI note number is negative.
        """
        if singleMidiNoteNumber < 0:
            raise ValueError(
                f"Need nonnegative MIDI note, got {singleMidiNoteNumber}"
            )

        return 440 * (2 ** ((singleMidiNoteNumber - 69) / 12))

def midi2hz(midi):
    """
    Convert MIDI note number(s) to frequency in Hertz (Hz).

    Parameters
    ----------
    midi : float or list of float
        The MIDI note number or a list of MIDI note numbers to convert. 
        Must be non-negative.

    Returns
    -------
    hz : float or list of float
        The corresponding frequency or list of frequencies in Hz.

    Raises
    ------
    ValueError
        If any MIDI note number is negative.
    """
    
    
    
    if isinstance(midi, list):
        return [_convert_Midi_to_Hz(m) for m in midi]
    else:
        return _convert_Midi_to_Hz(midi)