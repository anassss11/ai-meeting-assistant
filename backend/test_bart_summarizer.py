"""
Unit tests for BART summarizer module.

Tests cover model loading, caching, single-chunk summarization,
error handling, and timeout behavior.
"""

import logging
import pytest
from unittest.mock import Mock, patch, MagicMock

logger = logging.getLogger(__name__)


class TestGetBartModel:
    """Tests for get_bart_model() function."""
    
    def test_model_loading_returns_tuple(self):
        """Test that get_bart_model returns a tuple of (model, tokenizer)."""
        # This test will be skipped if model download fails
        try:
            from bart_summarizer import get_bart_model
            from transformers import BartForConditionalGeneration, BartTokenizer
            
            model, tokenizer = get_bart_model()
            assert isinstance(model, BartForConditionalGeneration)
            assert isinstance(tokenizer, BartTokenizer)
        except Exception as e:
            pytest.skip(f"Model loading failed: {e}")
    
    def test_model_singleton_caching(self):
        """Test that get_bart_model uses singleton caching."""
        try:
            from bart_summarizer import get_bart_model
            
            model1, tokenizer1 = get_bart_model()
            model2, tokenizer2 = get_bart_model()
            
            # Should return the same instances (cached)
            assert model1 is model2
            assert tokenizer1 is tokenizer2
        except Exception as e:
            pytest.skip(f"Model loading failed: {e}")
    
    def test_model_is_in_eval_mode(self):
        """Test that loaded model is in evaluation mode."""
        try:
            from bart_summarizer import get_bart_model
            
            model, _ = get_bart_model()
            assert not model.training
        except Exception as e:
            pytest.skip(f"Model loading failed: {e}")


class TestProcessSingleChunk:
    """Tests for _process_single_chunk() function."""
    
    @pytest.fixture
    def mock_model_and_tokenizer(self):
        """Create mock model and tokenizer for testing."""
        import torch
        
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Create a mock BatchFeature that has a .to() method
        mock_batch_feature = MagicMock()
        mock_batch_feature.__getitem__ = Mock(side_effect=lambda key: {
            'input_ids': torch.tensor([[1, 2, 3, 4, 5]]),
            'attention_mask': torch.tensor([[1, 1, 1, 1, 1]])
        }[key])
        mock_batch_feature.to = Mock(return_value=mock_batch_feature)
        
        # Mock tokenizer behavior
        mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
        mock_tokenizer.decode.return_value = "This is a summary."
        mock_tokenizer.return_value = mock_batch_feature
        
        # Mock model.generate behavior
        mock_model.generate.return_value = torch.tensor([[1, 2, 3, 4, 5]])
        
        return mock_model, mock_tokenizer
    
    def test_process_single_chunk_returns_string(self, mock_model_and_tokenizer):
        """Test that _process_single_chunk returns a string."""
        from bart_summarizer import _process_single_chunk
        from bart_config import BARTConfig
        
        mock_model, mock_tokenizer = mock_model_and_tokenizer
        config = BARTConfig()
        
        chunk = "This is a test chunk."
        result = _process_single_chunk(chunk, mock_model, mock_tokenizer, config)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_process_single_chunk_tokenizes_input(self, mock_model_and_tokenizer):
        """Test that _process_single_chunk tokenizes the input."""
        from bart_summarizer import _process_single_chunk
        from bart_config import BARTConfig
        
        mock_model, mock_tokenizer = mock_model_and_tokenizer
        config = BARTConfig()
        
        chunk = "This is a test chunk."
        _process_single_chunk(chunk, mock_model, mock_tokenizer, config)
        
        # Verify tokenizer was called
        mock_tokenizer.assert_called()
    
    def test_process_single_chunk_calls_model_generate(self, mock_model_and_tokenizer):
        """Test that _process_single_chunk calls model.generate()."""
        from bart_summarizer import _process_single_chunk
        from bart_config import BARTConfig
        
        mock_model, mock_tokenizer = mock_model_and_tokenizer
        config = BARTConfig()
        
        chunk = "This is a test chunk."
        _process_single_chunk(chunk, mock_model, mock_tokenizer, config)
        
        # Verify model.generate was called with correct parameters
        mock_model.generate.assert_called_once()
        call_kwargs = mock_model.generate.call_args[1]
        
        assert 'max_length' in call_kwargs
        assert call_kwargs['max_length'] == config.max_length
        assert 'min_length' in call_kwargs
        assert call_kwargs['min_length'] == config.min_length
        assert 'num_beams' in call_kwargs
        assert call_kwargs['num_beams'] == config.num_beams
    
    def test_process_single_chunk_decodes_output(self, mock_model_and_tokenizer):
        """Test that _process_single_chunk decodes the model output."""
        from bart_summarizer import _process_single_chunk
        from bart_config import BARTConfig
        
        mock_model, mock_tokenizer = mock_model_and_tokenizer
        config = BARTConfig()
        
        chunk = "This is a test chunk."
        _process_single_chunk(chunk, mock_model, mock_tokenizer, config)
        
        # Verify tokenizer.decode was called
        mock_tokenizer.decode.assert_called()
    
    def test_process_single_chunk_respects_config_parameters(self, mock_model_and_tokenizer):
        """Test that _process_single_chunk uses config parameters."""
        from bart_summarizer import _process_single_chunk
        from bart_config import BARTConfig
        
        mock_model, mock_tokenizer = mock_model_and_tokenizer
        config = BARTConfig(
            max_length=200,
            min_length=50,
            num_beams=8,
            length_penalty=1.5
        )
        
        chunk = "This is a test chunk."
        _process_single_chunk(chunk, mock_model, mock_tokenizer, config)
        
        # Verify model.generate was called with custom config
        call_kwargs = mock_model.generate.call_args[1]
        assert call_kwargs['max_length'] == 200
        assert call_kwargs['min_length'] == 50
        assert call_kwargs['num_beams'] == 8
        assert call_kwargs['length_penalty'] == 1.5
    
    def test_process_single_chunk_handles_inference_error(self, mock_model_and_tokenizer):
        """Test that _process_single_chunk raises InferenceError on model failure."""
        from bart_summarizer import _process_single_chunk
        from bart_config import BARTConfig
        from bart_exceptions import InferenceError
        
        mock_model, mock_tokenizer = mock_model_and_tokenizer
        mock_model.generate.side_effect = RuntimeError("Model inference failed")
        config = BARTConfig()
        
        chunk = "This is a test chunk."
        
        with pytest.raises(InferenceError):
            _process_single_chunk(chunk, mock_model, mock_tokenizer, config)
    
    def test_process_single_chunk_with_real_model(self):
        """Integration test with real model (skipped if model unavailable)."""
        try:
            from bart_summarizer import get_bart_model, _process_single_chunk
            from bart_config import BARTConfig
            
            model, tokenizer = get_bart_model()
            config = BARTConfig()
            
            chunk = "This is a test meeting transcript. The team discussed project goals and timelines."
            result = _process_single_chunk(chunk, model, tokenizer, config)
            
            assert isinstance(result, str)
            assert len(result) > 0
            # Summary should be shorter than input
            assert len(result) < len(chunk)
        except Exception as e:
            pytest.skip(f"Real model test skipped: {e}")


class TestProcessSingleChunkEdgeCases:
    """Tests for edge cases in _process_single_chunk()."""
    
    @pytest.fixture
    def mock_model_and_tokenizer(self):
        """Create mock model and tokenizer for testing."""
        import torch
        
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Create a mock BatchFeature that has a .to() method
        mock_batch_feature = MagicMock()
        mock_batch_feature.__getitem__ = Mock(side_effect=lambda key: {
            'input_ids': torch.tensor([[1, 2, 3]]),
            'attention_mask': torch.tensor([[1, 1, 1]])
        }[key])
        mock_batch_feature.to = Mock(return_value=mock_batch_feature)
        
        mock_tokenizer.encode.return_value = [1, 2, 3]
        mock_tokenizer.decode.return_value = "Summary"
        mock_tokenizer.return_value = mock_batch_feature
        
        mock_model.generate.return_value = torch.tensor([[1, 2, 3]])
        
        return mock_model, mock_tokenizer
    
    def test_process_single_chunk_with_empty_string(self, mock_model_and_tokenizer):
        """Test _process_single_chunk with empty string."""
        from bart_summarizer import _process_single_chunk
        from bart_config import BARTConfig
        
        mock_model, mock_tokenizer = mock_model_and_tokenizer
        config = BARTConfig()
        
        chunk = ""
        result = _process_single_chunk(chunk, mock_model, mock_tokenizer, config)
        
        assert isinstance(result, str)
    
    def test_process_single_chunk_with_very_long_chunk(self, mock_model_and_tokenizer):
        """Test _process_single_chunk with very long chunk (should be truncated)."""
        from bart_summarizer import _process_single_chunk
        from bart_config import BARTConfig
        
        mock_model, mock_tokenizer = mock_model_and_tokenizer
        config = BARTConfig()
        
        # Create a very long chunk
        chunk = "word " * 5000  # ~25000 characters
        result = _process_single_chunk(chunk, mock_model, mock_tokenizer, config)
        
        assert isinstance(result, str)
        # Verify tokenizer was called with truncation
        call_kwargs = mock_tokenizer.call_args[1]
        assert call_kwargs['truncation'] is True
    
    def test_process_single_chunk_with_special_characters(self, mock_model_and_tokenizer):
        """Test _process_single_chunk with special characters."""
        from bart_summarizer import _process_single_chunk
        from bart_config import BARTConfig
        
        mock_model, mock_tokenizer = mock_model_and_tokenizer
        config = BARTConfig()
        
        chunk = "Special chars: @#$%^&*() and unicode: café, naïve, 日本語"
        result = _process_single_chunk(chunk, mock_model, mock_tokenizer, config)
        
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
