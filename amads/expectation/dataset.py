from abc import ABC, abstractmethod
from typing import List, Iterator, TypeVar, Generic, Any, Union, Dict, Optional
from pathlib import Path
from amads.core.basics import Score
from amads.expectation.tokenizer import Tokenizer, Token, SymusicTokenizer
from amads.io.pt_midi_import import partitura_midi_import
from amads.utils import check_python_package_installed
from amads.expectation.tokenizers.midi_tokenizer_utils import load_score, preprocess_score

# Generic type variables
InputType = TypeVar('InputType')
TokenSeq = List[Token]

class Dataset(ABC, Generic[InputType]):
    """Abstract base class for datasets that can be used to train expectation models."""
    
    def __init__(self, sequences: List[InputType], tokenizer: Tokenizer, precompute_tokens: bool = True):
        """Initialize the dataset.
        
        Parameters
        ----------
        sequences : List[InputType]
            List of input sequences to tokenize
        tokenizer : Tokenizer
            Tokenizer instance to convert sequences to tokens
        precompute_tokens : bool, default=True
            If True, tokenize all sequences during initialization
            If False, tokenize sequences lazily when first accessed
        """
        self.sequences = sequences
        self.tokenizer = tokenizer
        self._tokenized_sequences = None
        self._vocabulary = None  # cache for vocabulary
        
        # Optionally precompute tokens during initialization
        if precompute_tokens:
            self.tokenize_all()
    
    @abstractmethod
    def validate_data(self) -> bool:
        pass
    
    def tokenize_all(self) -> None:
        """Explicitly tokenize all sequences.
        
        This can be called to precompute all tokens at a specific time,
        rather than waiting for the first access to tokenized_sequences.
        """
        if self._tokenized_sequences is None:
            self.validate_data()
            print(f"Tokenizing {len(self.sequences)} sequences...")
            self._tokenized_sequences = [
                self.tokenizer.tokenize(sequence)
                for sequence in self.sequences
            ]
            print(f"Tokenization complete.")
    
    @property
    def tokenized_sequences(self) -> List[TokenSeq]:
        """Get tokenized sequences, computing them if necessary."""
        if self._tokenized_sequences is None:
            self.tokenize_all()
        return self._tokenized_sequences
    
    def __len__(self) -> int:
        return len(self.sequences)
    
    def __iter__(self) -> Iterator[TokenSeq]:
        return iter(self.tokenized_sequences)
    
    def __getitem__(self, idx: int) -> TokenSeq:
        return self.tokenized_sequences[idx]

    @property
    def vocabulary(self) -> Dict[str, int]:
        """Get or create vocabulary mapping from all unique tokens in the dataset.
        
        Returns
        -------
        Dict[str, int]
            Mapping of token values to unique integer IDs
        """
        if self._vocabulary is None:
            # Get all unique token values from tokenized sequences
            unique_values = set()
            for sequence in self.tokenized_sequences:
                for token in sequence:
                    unique_values.add(token.value)
            
            # Create vocabulary mapping
            self._vocabulary = {
                value: idx for idx, value in enumerate(sorted(unique_values))
            }
        
        return self._vocabulary
    
    @property
    def vocab_size(self) -> int:
        """Get the size of the vocabulary."""
        return len(self.vocabulary)


class ScoreDataset(Dataset[Score]):
    """Dataset implementation for Score input data that can handle both Score objects 
    and MIDI file paths."""
    
    def __init__(self, 
                 scores: Union[List[Score], List[str], List[Path]], 
                 tokenizer: Tokenizer,
                 use_symusic: bool = False):
        """Initialize the ScoreDataset.

        Parameters
        ----------
        scores : Union[List[Score], List[str], List[Path]]
            List of Score objects or paths to MIDI files
        tokenizer : Tokenizer
            Tokenizer instance for Score objects
        use_symusic : bool, optional
            If True, store symusic Score objects instead of partitura Score objects.
            This provides faster loading but may not be compatible with all tokenizers.
        """
        if use_symusic:
            check_python_package_installed('symusic')
            import symusic
            
            # Check if tokenizer is compatible with symusic
            if not isinstance(tokenizer, SymusicTokenizer):
                raise ValueError(
                    "When use_symusic=True, tokenizer must be a SymusicTokenizer or its subclass. "
                    f"Got {type(tokenizer).__name__} instead."
                )
        
        processed_scores: List[Union[Score, 'symusic.Score']] = []
        score_paths: List[Union[str, Path]] = []
        
        # Process each input item
        for item in scores:
            if isinstance(item, Score):
                if use_symusic:
                    raise ValueError("Cannot use Score objects with use_symusic=True")
                processed_scores.append(item)
                score_paths.append(None)
            elif isinstance(item, (str, Path)):
                path = Path(item)
                score_paths.append(path)
                if use_symusic:
                    # Use the custom load_score function to preserve absolute timing
                    score = load_score(str(path))
                    # Apply preprocessing to handle note overlaps, short notes, etc.
                    score = preprocess_score(score)
                else:
                    score = partitura_midi_import(path, ptprint=False)
                processed_scores.append(score)
            else:
                raise ValueError(f"Unsupported input type: {type(item)}")
        
        self.use_symusic = use_symusic
        # Check if any paths are None, if so set score_paths to None
        if any(path is None for path in score_paths):
            self.score_paths = None
        else:
            self.score_paths = score_paths

        # Initialize tokenizer if it's a SymusicTokenizer
        if isinstance(tokenizer, SymusicTokenizer) and tokenizer.use_bpe and self.score_paths:
            # Only call train_on_corpus if the tokenizer uses BPE and we have valid paths
            valid_paths = [str(path) for path in self.score_paths if path is not None]
            if valid_paths:
                tokenizer.train_on_corpus(valid_paths)
            
        # Initialize the parent class with the processed scores
        super().__init__(processed_scores, tokenizer)
    
    def validate_data(self) -> bool:
        """Validate that all items are the correct Score type."""
        if self.use_symusic:
            import symusic
            if not all(isinstance(sequence, symusic.Score) for sequence in self.sequences):
                raise ValueError("All items must be symusic Score objects when use_symusic=True")
        else:
            if not all(isinstance(sequence, Score) for sequence in self.sequences):
                raise ValueError("All items must be Score objects when use_symusic=False")
        return True
    
    def get_score(self, idx: int) -> Union[Score, 'symusic.Score']:
        """Get the Score object at the given index."""
        return self.sequences[idx]


class AudioDataset(Dataset[str]):
    """Dataset implementation for audio input data that can handle audio file paths.
    
    This dataset is designed to work with audio tokenizers like WavTokenizerAudio.
    """
    
    def __init__(self, 
                 audio_files: List[Union[str, Path]], 
                 tokenizer: Tokenizer):
        """Initialize the AudioDataset.

        Parameters
        ----------
        audio_files : List[Union[str, Path]]
            List of paths to audio files
        tokenizer : Tokenizer
            Tokenizer instance for audio files, e.g., WavTokenizerAudio
        """
        from amads.expectation.tokenizers.audio_tokenizer import AudioTokenizer
        
        if not isinstance(tokenizer, AudioTokenizer):
            raise ValueError(
                f"Tokenizer must be an AudioTokenizer or its subclass. "
                f"Got {type(tokenizer).__name__} instead."
            )
        
        processed_files = []
        audio_paths = []
        
        # Process each input path
        for item in audio_files:
            path = Path(item)
            if not path.exists():
                raise FileNotFoundError(f"Audio file not found: {path}")
            
            # Store the absolute path to the audio file
            abs_path = str(path.absolute())
            processed_files.append(abs_path)
            audio_paths.append(abs_path)
        
        self.audio_paths = audio_paths
        
        # Initialize the parent class with the processed paths
        super().__init__(processed_files, tokenizer)
    
    def validate_data(self) -> bool:
        """Validate that all items are valid audio file paths."""
        valid_extensions = {'.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac', '.wma'}
        
        for path in self.sequences:
            path_obj = Path(path)
            if not path_obj.exists():
                raise ValueError(f"File does not exist: {path}")
                
            if not any(path.lower().endswith(ext) for ext in valid_extensions):
                raise ValueError(f"Invalid audio file format: {path}")
        
        return True
    
    def get_audio_path(self, idx: int) -> str:
        """Get the audio file path at the given index."""
        return self.sequences[idx]


class SpectrogramDataset(Dataset[Any]):
    def validate_data(self) -> bool:
        return True
