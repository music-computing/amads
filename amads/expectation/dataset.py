from abc import ABC, abstractmethod
from typing import List, Iterator, TypeVar, Generic, Any, Union, Dict, Optional
from pathlib import Path
from amads.core.basics import Score
from amads.expectation.tokenizer import Tokenizer, Token
from amads.io.pt_midi_import import partitura_midi_import

# Generic type variables
InputType = TypeVar('InputType')
TokenSeq = List[Token]

class Dataset(ABC, Generic[InputType]):
    """Abstract base class for datasets that can be used to train expectation models."""
    
    def __init__(self, sequences: List[InputType], tokenizer: Tokenizer):
        self.sequences = sequences
        self.tokenizer = tokenizer
        self._tokenized_sequences = None
    
    @abstractmethod
    def validate_data(self) -> bool:
        pass
    
    @property
    def tokenized_sequences(self) -> List[TokenSeq]:
        if self._tokenized_sequences is None:
            self.validate_data()
            self._tokenized_sequences = [
                self.tokenizer.tokenize(sequence)
                for sequence in self.sequences
            ]
        return self._tokenized_sequences
    
    def __len__(self) -> int:
        return len(self.sequences)
    
    def __iter__(self) -> Iterator[TokenSeq]:
        return iter(self.tokenized_sequences)
    
    def __getitem__(self, idx: int) -> TokenSeq:
        return self.tokenized_sequences[idx]


class ScoreDataset(Dataset[Score]):
    """Dataset implementation for Score input data that can handle both Score objects 
    and MIDI file paths."""
    
    def __init__(self, 
                 scores: Union[List[Score], List[str], List[Path]], 
                 tokenizer: Tokenizer):
        """Initialize the ScoreDataset.

        Parameters
        ----------
        scores : Union[List[Score], List[str], List[Path]]
            List of Score objects or paths to MIDI files
        tokenizer : Tokenizer
            Tokenizer instance for Score objects
        """
        processed_scores: List[Score] = []
        
        # Process each input item
        for item in scores:
            if isinstance(item, Score):
                processed_scores.append(item)
            elif isinstance(item, (str, Path)):
                path = Path(item)
                score = self._load_midi(path)
                processed_scores.append(score)
            else:
                raise ValueError(f"Unsupported input type: {type(item)}")
        
        # Initialize the parent class with the processed scores
        super().__init__(processed_scores, tokenizer)
    
    def _load_midi(self, path: Path) -> Score:
        """Load a MIDI file and convert it to a Score object."""
        return partitura_midi_import(path, ptprint=False)
    
    def validate_data(self) -> bool:
        """Validate that all items in data are Score objects."""
        if not all(isinstance(sequence, Score) for sequence in self.sequences):
            raise ValueError("All items must be Score objects")
        return True
    
    def get_score(self, idx: int) -> Score:
        """Get the Score object at the given index."""
        return self.sequences[idx]


# Other dataset implementations remain the same
class AudioDataset(Dataset[str]):
    def validate_data(self) -> bool:
        valid_extensions = {'.wav', '.mp3', '.flac'}
        for path in self.data:
            if not any(path.endswith(ext) for ext in valid_extensions):
                raise ValueError(f"Invalid audio file format: {path}")
        return True


class SpectrogramDataset(Dataset[Any]):
    def validate_data(self) -> bool:
        return True
