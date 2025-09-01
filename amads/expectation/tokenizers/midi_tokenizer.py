"""
Tokenization schemes for MIDI data in the AMADS library using miditok implementations.
"""

from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from amads.core.basics import Score, Note, Part
from amads.utils import check_python_package_installed
from amads.expectation.tokenizers.base_tokenizer import Token, Tokenizer
from amads.expectation.tokenizers.midi_tokenizer_utils import preprocess_score, load_score
import warnings


class MIDITokenizer(Tokenizer):
    """Base class for all MIDI tokenization schemes."""
    
    def tokenize(self, input_data: Union[str, 'symusic.Score']) -> List[Token]:
        """Convert a MIDI file or symusic Score into a sequence of Tokens with preserved timing.

        Parameters
        ----------
        input_data : Union[str, 'symusic.Score']
            Path to a MIDI file or a preprocessed symusic Score object

        Returns
        -------
        List[Token]
            Sequence of tokens representing the score with accurate timing
        """
        import symusic
        
        # Handle symusic Score objects (already preprocessed in dataset.py)
        if isinstance(input_data, symusic.Score):
            symusic_score = input_data
        # Handle MIDI file paths
        elif isinstance(input_data, str) and input_data.endswith(('.mid', '.midi')):
            # Process the MIDI file to get a symusic score with timing
            symusic_score = self._process_midi_file(input_data)
        else:
            raise ValueError(f"Expected path to a MIDI file (.mid or .midi) or a symusic.Score object, got {type(input_data)}")
        
        # Get raw tokens from the tokenizer
        raw_tokens = self._encode_tokens(symusic_score)
        # Add timing information using the preprocessed score
        return self._add_timing(raw_tokens, symusic_score)
    
    def decode(self, tokens: List[Token]) -> Optional[Score]:
        """Convert tokens back to a Score.
        
        Note: This is not fully implemented and will not preserve absolute timing information.
        
        Parameters
        ----------
        tokens : List[Token]
            Sequence of tokens to decode
        
        Returns
        -------
        Optional[Score]
            The reconstructed musical score, without precise timing information
        """
        warnings.warn("Decoding from tokens to Score does not preserve absolute timing information")
        miditok_tokens = [t.value for t in tokens]
        try:
            midi_data = self._tokenizer.tokens_to_midi(miditok_tokens)
            return midi_to_score(midi_data)
        except:
            warnings.warn("Failed to decode tokens to Score")
            return None

def score_to_symusic(score: Score) -> 'symusic.Score':
    """Convert our Score format to symusic Score format directly.
    
    Parameters
    ----------
    score : Score
        Our internal score representation
        
    Returns
    -------
    symusic.Score
        Score representation that miditok can use
    """
    check_python_package_installed('symusic')
    import symusic
    
    # First flatten the score to simplify note handling
    flat_score = score.flatten(collapse=True)
    
    # Constants for conversion (assuming 120 BPM)
    TICKS_PER_QUARTER = 480
    SECONDS_PER_QUARTER = 0.5  # at 120 BPM
    TICKS_PER_SECOND = int(TICKS_PER_QUARTER / SECONDS_PER_QUARTER)
    
    # Create notes list
    notes = []
    for note in flat_score.find_all(Note):
        symusic_note = symusic.Note(
            time=int(note.onset * TICKS_PER_SECOND),      # Convert seconds to ticks
            duration=int(note.duration * TICKS_PER_SECOND), # Convert seconds to ticks
            pitch=int(note.pitch.keynum),
            velocity=64  # Default velocity
        )
        notes.append(symusic_note)
    
    # Create a track with the notes
    track = symusic.Track(notes=notes)
    
    # Create a symusic Score
    symusic_score = symusic.Score()
    symusic_score.tracks = [track]
    
    return symusic_score

class SymusicTokenizer(MIDITokenizer):
    """Base class for tokenizers that use symusic/miditok implementations."""
    
    def __init__(self, 
                 tokenizer_class: str, 
                 use_bpe: bool = False,
                 vocab_size: int = 1000,  # Only used if use_bpe=True
                 **params):
        """Initialize the tokenizer.
        
        Parameters
        ----------
        tokenizer_class : str
            Name of the miditok tokenizer class to use ('REMI', 'TSD', or 'MIDILike')
        use_bpe : bool, optional
            Whether to use BPE training for the vocabulary, by default False
        vocab_size : int, optional
            Target vocabulary size when using BPE, by default 1000
        params : dict
            Additional parameters to pass to TokenizerConfig
        """
        check_python_package_installed('miditok')
        from miditok import REMI, TSD, MIDILike, TokenizerConfig
        
        self.tokenizer_class = tokenizer_class
        self.params = params
        self.use_bpe = use_bpe
        self.vocab_size = vocab_size
        
        self.tokenizer_map = {
            'REMI': REMI,
            'TSD': TSD,
            'MIDILike': MIDILike
        }
        
        if tokenizer_class not in self.tokenizer_map:
            raise ValueError(f"Unknown tokenizer class: {tokenizer_class}. Must be one of {list(self.tokenizer_map.keys())}")
        
        # Initialize a basic tokenizer without BPE training
        config = TokenizerConfig(
            use_tempos=True,
            use_bpe=False,  # Always start without BPE
            beat_res={(0,2):50},
            **self.params
        )
        self._tokenizer = self.tokenizer_map[self.tokenizer_class](config)
        
        # Warn if BPE was requested since it's not implemented
        if self.use_bpe:
            warnings.warn("BPE training is not yet implemented. Using default vocabulary.", UserWarning)

            # When implemented, this would look like:
            # self._tokenizer.train(
            #     vocab_size=self.vocab_size,
            #     model="BPE",
            #     files_paths=corpus_paths
            # )

    def _process_midi_file(self, midi_path: str) -> 'symusic.Score':
        """Process a MIDI file to create a symusic Score with absolute timing.
        
        Parameters
        ----------
        midi_path : str
            Path to the MIDI file
            
        Returns
        -------
        symusic.Score
            Preprocessed symusic Score with preserved timing
        """
        # Load the score while preserving absolute time information
        symusic_score = load_score(midi_path)
        # Apply preprocessing to handle note overlaps, short notes, etc.
        return preprocess_score(symusic_score)

    def _encode_tokens(self, symusic_score: 'symusic.Score') -> List[Any]:
        """Get raw tokens from the tokenizer."""
        return self._tokenizer.encode(symusic_score)[0]

    def _add_timing(self, raw_tokens: List[Any], symusic_score: 'symusic.Score') -> List[Token]:
        """Add timing information to tokens.
        
        This method maps the token to the appropriate note/event in the symusic score
        to get accurate timing information.
        
        Args:
            raw_tokens: List of raw token values from the tokenizer
            symusic_score: The preprocessed symusic score with preserved timing
            
        Returns:
            List of Token objects with timing information added where appropriate
        """
        # Create a lookup between tokens and their corresponding time in the symusic score
        # To be implemented by subclasses for token-specific mapping
        raise NotImplementedError("_add_timing must be implemented by subclasses")

    def train_on_corpus(self, corpus_paths: List[Union[str, Path]]) -> None:
        """Train the tokenizer on a corpus of MIDI files.
        
        This is a compatibility method for ScoreDataset.
        
        Parameters
        ----------
        corpus_paths : List[Union[str, Path]]
            List of paths to MIDI files
        """
        if self.use_bpe:
            warnings.warn("BPE training is not yet implemented. Using default vocabulary.", UserWarning)

class REMITokenizer(SymusicTokenizer):
    """REMI tokenizer using miditok's implementation."""
    
    def __init__(self, use_bpe: bool = False, vocab_size: int = 1000, **params):
        super().__init__('REMI', use_bpe=use_bpe, vocab_size=vocab_size, **params)

    def _add_timing(self, raw_tokens: List[Any], symusic_score: 'symusic.Score') -> List[Token]:
        """Add timing to REMI tokens using direct symusic note information."""
        tokens = []
        vocab = {v: k for k, v in self._tokenizer.vocab.items()}
        
        # Get notes from symusic_score for direct time reference
        notes = sorted(symusic_score.tracks[0].notes, key=lambda x: x.time)
        current_note_idx = 0
        current_time = 0  # in milliseconds
        
        # In REMI, Pitch tokens follow a Bar or Position token
        # Use note timing directly from the preprocessed symusic score
        for i, tok in enumerate(raw_tokens):
            token_str = vocab.get(tok, str(tok))
            
            if token_str.startswith('Pitch_'):
                # For Pitch tokens, use the current note's start time (already in milliseconds)
                if current_note_idx < len(notes):
                    current_time = notes[current_note_idx].time
                    tokens.append(Token(value=tok, start_time=current_time / 1000.0, name=token_str))  # Convert ms to seconds
                    current_note_idx += 1
                else:
                    # If we've run out of notes, just use the last known time
                    tokens.append(Token(value=tok, start_time=current_time / 1000.0, name=token_str))
            elif token_str.startswith('Position_'):
                # Position tokens also get timing
                if current_note_idx < len(notes):
                    current_time = notes[current_note_idx].time
                    tokens.append(Token(value=tok, start_time=current_time / 1000.0, name=token_str))
                else:
                    tokens.append(Token(value=tok, name=token_str))
            else:
                # Other tokens don't get timing
                tokens.append(Token(value=tok, name=token_str))
                
        return tokens


class TSDTokenizer(SymusicTokenizer):
    """Time-Shift-Duration (TSD) tokenizer using miditok's implementation."""
    
    def __init__(self, use_bpe: bool = False, vocab_size: int = 1000, **params):
        super().__init__('TSD', use_bpe=use_bpe, vocab_size=vocab_size, **params)
    
    def _add_timing(self, raw_tokens: List[Any], symusic_score: 'symusic.Score') -> List[Token]:
        """Add timing to TSD tokens using direct symusic note information."""
        tokens = []
        vocab = {v: k for k, v in self._tokenizer.vocab.items()}
        
        # Get notes from symusic_score for direct time reference
        notes = sorted(symusic_score.tracks[0].notes, key=lambda x: x.time)
        current_note_idx = 0
        
        # In TSD, note events are represented by NoteOn tokens followed by a pitch
        for i, tok in enumerate(raw_tokens):
            token_str = vocab.get(tok, str(tok))
            
            if token_str.startswith('Pitch_'):
                # For Pitch tokens, use the current note's start time (already in milliseconds)
                if current_note_idx < len(notes):
                    # Convert milliseconds to seconds for the timing
                    time_seconds = notes[current_note_idx].time / 1000.0
                    tokens.append(Token(value=tok, start_time=time_seconds, name=token_str))
                    current_note_idx += 1
                else:
                    tokens.append(Token(value=tok, name=token_str))
            else:
                # Other tokens don't get timing
                tokens.append(Token(value=tok, name=token_str))
                
        return tokens


class MIDILikeTokenizer(SymusicTokenizer):
    """MIDI-Like tokenizer using miditok's implementation."""
    
    def __init__(self, use_bpe: bool = False, vocab_size: int = 1000, **params):
        super().__init__('MIDILike', use_bpe=use_bpe, vocab_size=vocab_size, **params)
    
    def _add_timing(self, raw_tokens: List[Any], symusic_score: 'symusic.Score') -> List[Token]:
        """Add timing to MIDI-Like tokens using direct symusic note information."""
        tokens = []
        vocab = {v: k for k, v in self._tokenizer.vocab.items()}
        
        # Get notes from symusic_score for direct time reference
        notes = sorted(symusic_score.tracks[0].notes, key=lambda x: x.time)
        current_note_idx = 0
        
        # In MIDI-Like, NoteOn tokens correspond directly to notes
        for i, tok in enumerate(raw_tokens):
            token_str = vocab.get(tok, str(tok))
            
            if token_str.startswith('NoteOn_'):
                # For NoteOn tokens, use the current note's start time (already in milliseconds)
                if current_note_idx < len(notes):
                    # Convert milliseconds to seconds for the timing
                    time_seconds = notes[current_note_idx].time / 1000.0
                    tokens.append(Token(value=tok, start_time=time_seconds, name=token_str))
                    current_note_idx += 1
                else:
                    tokens.append(Token(value=tok, name=token_str))
            else:
                # Other tokens don't get timing
                tokens.append(Token(value=tok, name=token_str))
                
        return tokens

def midi_to_score(midi_data) -> Score:
    """Convert MIDI data to our Score format.
    
    Parameters
    ----------
    midi_data : bytes or BytesIO
        Raw MIDI data
        
    Returns
    -------
    Score
        Score object in our internal representation
    """
    # This is a placeholder - you'll need to implement the conversion
    # from MIDI bytes to your Score format
    raise NotImplementedError("Decoding from tokens to Score not yet implemented")




class REMITokenizer(SymusicTokenizer):
    """REMI tokenizer using miditok's implementation."""
    
    def __init__(self, use_bpe: bool = False, vocab_size: int = 1000, **params):
        super().__init__('REMI', use_bpe=use_bpe, vocab_size=vocab_size, **params)

    def _add_timing(self, raw_tokens: List[Any], symusic_score: 'symusic.Score') -> List[Token]:
        """Add timing to REMI tokens using direct symusic note information."""
        tokens = []
        vocab = {v: k for k, v in self._tokenizer.vocab.items()}
        
        # Get notes from symusic_score for direct time reference
        notes = sorted(symusic_score.tracks[0].notes, key=lambda x: x.time)
        current_note_idx = 0
        current_time = 0  # in milliseconds
        
        # In REMI, Pitch tokens follow a Bar or Position token
        # Use note timing directly from the preprocessed symusic score
        for i, tok in enumerate(raw_tokens):
            token_str = vocab.get(tok, str(tok))
            
            if token_str.startswith('Pitch_'):
                # For Pitch tokens, use the current note's start time (already in milliseconds)
                if current_note_idx < len(notes):
                    current_time = notes[current_note_idx].time
                    tokens.append(Token(value=tok, start_time=current_time / 1000.0, name=token_str))  # Convert ms to seconds
                    current_note_idx += 1
                else:
                    # If we've run out of notes, just use the last known time
                    tokens.append(Token(value=tok, start_time=current_time / 1000.0, name=token_str))
            elif token_str.startswith('Position_'):
                # Position tokens also get timing
                if current_note_idx < len(notes):
                    current_time = notes[current_note_idx].time
                    tokens.append(Token(value=tok, start_time=current_time / 1000.0, name=token_str))
                else:
                    tokens.append(Token(value=tok, name=token_str))
            else:
                # Other tokens don't get timing
                tokens.append(Token(value=tok, name=token_str))
                
        return tokens



class TSDTokenizer_Custom(SymusicTokenizer):
    """Custom TSD tokenizer based on miditok's implementation, courtesy of https://github.com/jazz-style-conditioned-generation/jazz-style-conditioned-generation/blob/main/jazz_style_conditioned_generation/data/tokenizer.py"""
    
    def __init__(self, config_params={}, **params):
        """Initialize the tokenizer.
        
        Parameters
        ----------

        """
        check_python_package_installed('miditok')
        from amads.expectation.tokenizers.midi_tokenizer_custom_TSD import CustomTSD, CustomTokenizerConfig, DEFAULT_TOKENIZER_CONFIG
        
        config_dict = DEFAULT_TOKENIZER_CONFIG
        for key, value in config_params.items():
            config_dict[key] = value
        #print(config_dict)
        config = CustomTokenizerConfig(**config_dict)

        self.use_bpe = False
        #self._tokenizer = CustomTSD(tokenizer_config = CustomTokenizerConfig(**DEFAULT_TOKENIZER_CONFIG))
        self._tokenizer = CustomTSD(tokenizer_config = config)
        
    def _process_midi_file(self, midi_path: str) -> 'symusic.Score':
        """Process a MIDI file to create a symusic Score with absolute timing.
        
        Parameters
        ----------
        midi_path : str
            Path to the MIDI file
            
        Returns
        -------
        symusic.Score
            Preprocessed symusic Score with preserved timing
        """
        # Load the score while preserving absolute time information
        symusic_score = load_score(midi_path, as_seconds=True)
        # Apply preprocessing to handle note overlaps, short notes, etc.
        return preprocess_score(symusic_score)

    def _encode_tokens(self, symusic_score: 'symusic.Score') -> List[Any]:
        """Get raw tokens from the tokenizer."""
        return self._tokenizer.encode(symusic_score)[0]
    
    def _add_timing(self, raw_tokens: List[Any], symusic_score: 'symusic.Score') -> List[Token]:
        """Add timing to TSD tokens using direct symusic note information."""
        tokens = []
        vocab = {v: k for k, v in self._tokenizer.vocab.items()}
        
        # Get notes from symusic_score for direct time reference
        notes = sorted(symusic_score.tracks[0].notes, key=lambda x: x.time)
        current_note_idx = 0
        
        # In TSD, note events are represented by NoteOn tokens followed by a pitch
        for i, tok in enumerate(raw_tokens):
            token_str = vocab.get(tok, str(tok))
            
            if token_str.startswith('Pitch_'):
                # For Pitch tokens, use the current note's start time (already in milliseconds)
                if current_note_idx < len(notes):
                    # Convert milliseconds to seconds for the timing
                    time_seconds = notes[current_note_idx].time / 1000.0
                    tokens.append(Token(value=tok, start_time=time_seconds, name=token_str))
                    current_note_idx += 1
                else:
                    tokens.append(Token(value=tok, name=token_str))
            else:
                # Other tokens don't get timing
                tokens.append(Token(value=tok, name=token_str))
                
        return tokens

    def train_on_corpus(self, corpus_paths: List[Union[str, Path]]) -> None:
        """Train the tokenizer on a corpus of MIDI files.
        
        This is a compatibility method for ScoreDataset.
        
        Parameters
        ----------
        corpus_paths : List[Union[str, Path]]
            List of paths to MIDI files
        """
        pass

    @property
    def vocab(self):
        return self._tokenizer.vocab
    
    @property
    def config(self):
        return self._tokenizer.config
