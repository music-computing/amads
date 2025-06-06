"""
Provides the `midi2hz` function.

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=50
"""

def midi2hz(midi):
    """
    Converts a midi note number to the corresponding frequency in hz. 
    Validates input to make sure that the input is non-negative. 

    Parameters:
    midi (float or a list of floats): The midi note number or a list of midi note numbers. 

    Returns:
    hz (float or a list of floats): The corresponding hz measurements for the midi note numbers.

    Raises:
    ValueError: If any midi note number is negative. 
    """
    
    def convertMidi2Hz(singleMidiNoteNumber):
        """
        A helper function that turns one midi note number, input as a single float, and returns
        the hz measurement as a float; also validates that the input midi is nonnegative. 
        """
        if singleMidiNoteNumber < 0:
            raise ValueError(f"The midi note number must be nonnegative, got {singleMidiNoteNumber}")

        return 440 * (2 ** ((singleMidiNoteNumber - 69) / 12))
    
    if isinstance(midi, list):
        result = []
        for midiNote in midi:
            result.append(convertMidi2Hz(midiNote))
        return result
    else:
        return convertMidi2Hz(midi)
