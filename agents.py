# OmniNexus - agents.py
# Defines the base structure for AI agents and implements specific agents.

from abc import ABC, abstractmethod
import re # For simple word counting
import collections

# --- Base Agent Class ---

class BaseAgent(ABC):
    """
    Abstract base class for all OmniNexus AI agents.
    Defines the common interface for executing tasks.
    """
    def __init__(self, agent_id, config):
        """
        Initializes the agent.
        :param agent_id: A unique identifier for this agent instance.
        :param config: A dictionary containing configuration specific to this agent instance (e.g., model parameters, behavior flags).
        """
        self.agent_id = agent_id
        self.config = config if config else {} # Ensure config is at least an empty dict
        self.validate_config() # Call validation during initialization

    @abstractmethod
    def validate_config(self):
        """
        Validates the provided configuration for the specific agent type.
        Should raise ValueError or TypeError for invalid configs.
        """
        pass

    @abstractmethod
    def get_metadata(self):
        """
        Returns metadata about the agent itself.
        Example: type, description, capabilities, required input format.
        """
        pass

    @abstractmethod
    def execute(self, data_inputs, parameters=None):
        """
        The core method where the agent performs its task.
        :param data_inputs: A list of data chunks provided by the orchestrator
                           (likely results from one or more connector queries).
                           The exact format might evolve, but for PoC, assume it's
                           a list of dictionaries like {'content': '...', 'source': '...'}.
        :param parameters: Optional dictionary with specific instructions or
                           parameters for this execution run (e.g., query keywords).
        :return: The result of the agent's computation. Format depends on the agent.
        """
        pass

    @classmethod
    @abstractmethod
    def get_config_schema(cls):
        """
        Returns a description of the required configuration parameters
        for this agent type. Useful for UI/CLI setup.
        :return: Dictionary describing config keys, types, and if they are required.
        """
        pass

# --- Specific Agent Implementations ---

class WordCountAgent(BaseAgent):
    """
    A simple agent that counts words in the text data provided via
    standard Data Item format (Phase 2).
    """

    @classmethod
    def get_config_schema(cls):
        return {}

    def validate_config(self):
        if self.config and self.config != {'type': 'word_counter'}: # Allow the type key from factory
             print(f"Warning: WordCountAgent '{self.agent_id}' received unexpected config: {self.config}")
        pass

    def get_metadata(self):
        """Returns metadata about the WordCountAgent."""
        return {
            "agent_id": self.agent_id,
            "type": "word_counter",
            "description": "Counts the total number of words in the 'content' field of the payload within standard Data Items.",
            "input_format": "List[Dict] conforming to protocol.DATA_ITEM_STRUCTURE with text in payload['content']",
            "output_format": "Dictionary {'total_words': count, 'items_processed': N, 'items_skipped': M}"
        }

    def execute(self, data_inputs, parameters=None):
        """
        Counts words in payload['content'] of each valid Data Item.
        :param data_inputs: List[Dict] conforming to protocol.DATA_ITEM_STRUCTURE
        :param parameters: Ignored by this agent.
        :return: Dictionary {'total_words': count, 'items_processed': N, 'items_skipped': M}
        """
        total_words = 0
        items_processed = 0
        items_skipped = 0

        if not isinstance(data_inputs, list):
             print(f"Error: WordCountAgent expects a list of data inputs, got {type(data_inputs)}")
             return {"total_words": 0, "items_processed": 0, "items_skipped": len(data_inputs) if isinstance(data_inputs, list) else 1 , "error": "Invalid input format: Expected list"}

        print(f"WordCountAgent '{self.agent_id}' executing on {len(data_inputs)} data inputs...")

        for item in data_inputs:
            # Validate basic structure
            if not isinstance(item, dict) or 'payload' not in item or not isinstance(item['payload'], dict) or 'content' not in item['payload']:
                print(f"Warning: Skipping item due to missing structure (payload or payload['content']): {item.get('item_id', 'N/A')}")
                items_skipped += 1
                continue

            content = item['payload']['content']
            if isinstance(content, str):
                # Simple word count using regex
                words = re.findall(r'\b\w+\b', content)
                count = len(words)
                total_words += count
                items_processed += 1
                # Debug print (optional):
                # source = item.get('source_uri', item.get('item_id', 'N/A'))
                # print(f"  - Processed item {source} with {count} words.")
            else:
                print(f"Warning: Skipping item {item.get('item_id', 'N/A')} because payload['content'] is not a string: {type(content)}")
                items_skipped += 1

        print(f"WordCountAgent '{self.agent_id}' finished execution. Words: {total_words}, Processed: {items_processed}, Skipped: {items_skipped}")
        return {
            "total_words": total_words,
            "items_processed": items_processed,
            "items_skipped": items_skipped
        }


# Basic English stop words list (can be expanded significantly)
STOP_WORDS = set([
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd",
    "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
    "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own",
    "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they", "they'd",
    "they'll", "they're", "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very",
    "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where",
    "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't",
    "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves",
    # Consider adding common short words or context-specific words if needed
    "fig", "figure", "table", "also", "data", "using", "used" # Example additions
])

class KeywordExtractAgent(BaseAgent):
    """
    A simple agent that extracts potential keywords based on word frequency,
    after removing common stop words. Uses standard Data Items (Phase 2).
    """

    @classmethod
    def get_config_schema(cls):
        return {
            "num_keywords": {"type": "integer", "required": False, "default": 10, "description": "Maximum number of keywords to return per execution."},
            "min_word_length": {"type": "integer", "required": False, "default": 3, "description": "Minimum length of a word to be considered a keyword."}
        }

    def validate_config(self):
        """Validate configuration."""
        schema = self.get_config_schema()
        num_k = self.config.get("num_keywords", schema['num_keywords']['default'])
        min_len = self.config.get("min_word_length", schema['min_word_length']['default'])

        if not isinstance(num_k, int) or num_k <= 0:
            raise ValueError("'num_keywords' must be a positive integer.")
        if not isinstance(min_len, int) or min_len < 1:
            raise ValueError("'min_word_length' must be a positive integer >= 1.")

        # Ensure defaults are set in the instance config if not provided
        self.config['num_keywords'] = num_k
        self.config['min_word_length'] = min_len

    def get_metadata(self):
        """Returns metadata about the KeywordExtractAgent."""
        return {
            "agent_id": self.agent_id,
            "type": "keyword_extractor",
            "description": "Extracts keywords from text content in Data Items based on frequency (excluding stop words).",
            "config_schema": self.get_config_schema(),
            "input_format": "List[Dict] conforming to protocol.DATA_ITEM_STRUCTURE with text in payload['content']",
            "output_format": "Dictionary {'keywords': [{'word': w, 'score': count}, ...], 'items_processed': N, 'items_skipped': M}"
        }

    def execute(self, data_inputs, parameters=None):
        """
        Extracts keywords from relevant text fields within the payload
        of each valid Data Item. Prioritizes 'content', falls back to
        'subject' and 'from'.
        :param data_inputs: List[Dict] conforming to protocol.DATA_ITEM_STRUCTURE
        :param parameters: Optional dictionary, potentially overriding config for this run (e.g., {"num_keywords": 5}). Ignored if not provided.
        :return: Dictionary {'keywords': List[Dict{'word', 'score'}], 'items_processed': N, 'items_skipped': M}
        """
        items_processed = 0
        items_skipped = 0
        word_counts = collections.Counter()

        # Determine parameters for this run (override config if provided)
        run_params = self.config.copy() # Start with agent's base config
        if isinstance(parameters, dict):
            num_k_override = parameters.get("num_keywords")
            min_len_override = parameters.get("min_word_length")
            try:
                if num_k_override is not None: run_params['num_keywords'] = int(num_k_override)
                if min_len_override is not None: run_params['min_word_length'] = int(min_len_override)
                if run_params['num_keywords'] <= 0: raise ValueError("num_keywords must be positive")
                if run_params['min_word_length'] < 1: raise ValueError("min_word_length must be >= 1")
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid execution parameter provided, using agent default config. Error: {e}")
                run_params = self.config.copy() # Revert to original on error

        num_keywords_to_return = run_params['num_keywords']
        min_word_length = run_params['min_word_length']

        print(f"KeywordExtractAgent '{self.agent_id}' executing on {len(data_inputs)} data inputs...")
        print(f"  Parameters: num_keywords={num_keywords_to_return}, min_word_length={min_word_length}")

        if not isinstance(data_inputs, list):
            print(f"Error: KeywordExtractAgent expects a list, got {type(data_inputs)}")
            return {"keywords": [], "items_processed": 0, "items_skipped": len(data_inputs) if isinstance(data_inputs, list) else 1, "error": "Invalid input format: Expected list"}

        for item in data_inputs:
            text_to_process = None # Initialize text source for this item

            # Validate basic structure - check for payload dictionary first
            if not isinstance(item, dict) or 'payload' not in item or not isinstance(item['payload'], dict):
                print(f"Warning: Skipping item due to missing or invalid 'payload': {item.get('item_id', 'N/A')}")
                items_skipped += 1
                continue

            payload = item['payload']

            # Prioritize 'content' key if it exists and is a string
            if isinstance(payload.get('content'), str):
                text_to_process = payload['content']
            # Fallback: If no 'content', try combining 'subject' and 'from'
            elif not text_to_process:
                subject = payload.get('subject', '')
                sender = payload.get('from', '')
                # Ensure they are strings before concatenating
                if isinstance(subject, str) or isinstance(sender, str):
                    combined_text = f"{str(subject)} {str(sender)}" # Combine available text
                    if combined_text.strip(): # Check if there's actually text after combining
                        text_to_process = combined_text
                        # print(f"Debug: Using combined subject/from for item {item.get('item_id', 'N/A')}") # Optional debug
                    else:
                        print(f"Warning: Skipping item {item.get('item_id', 'N/A')} - No 'content', and 'subject'/'from' are empty/invalid.")
                        items_skipped += 1
                        continue
                else:
                    print(f"Warning: Skipping item {item.get('item_id', 'N/A')} - No 'content', and 'subject'/'from' payload keys are missing or not strings.")
                    items_skipped += 1
                    continue

            # Check if we successfully got text to process for this item
            if text_to_process is not None and isinstance(text_to_process, str):
                # Naive keyword extraction: lowercase, split, filter stop words & length
                words = re.findall(r'\b\w+\b', text_to_process.lower())
                potential_keywords = [
                    word for word in words
                    if word not in STOP_WORDS and len(word) >= min_word_length
                ]
                word_counts.update(potential_keywords)
                items_processed += 1
            # This else shouldn't be strictly necessary due to checks above, but acts as a safeguard
            elif text_to_process is None:
                # Warning message already printed in the logic above
                # items_skipped counter already incremented
                pass
            else: # Should not happen if logic above is correct, but catch non-string case
                print(f"Warning: Skipping item {item.get('item_id', 'N/A')} - derived text_to_process was not a string: {type(text_to_process)}")
                items_skipped += 1


        # Get the most common keywords
        most_common = word_counts.most_common(num_keywords_to_return)

        # Format output
        result_keywords = [{"word": word, "score": count} for word, count in most_common]

        print(f"KeywordExtractAgent '{self.agent_id}' finished. Found {len(result_keywords)} keywords. Processed: {items_processed}, Skipped: {items_skipped}")
        return {
            "keywords": result_keywords,
            "items_processed": items_processed,
            "items_skipped": items_skipped
        }

# --- Agent Registry and Factory ---

# Add the new agent class to the registry dictionary
_agent_types = {
    "word_counter": WordCountAgent,
    "keyword_extractor": KeywordExtractAgent # Add the new type here
}


def get_available_agent_types():
    """Returns a list of registered agent type names."""
    return list(_agent_types.keys())

def get_agent_class(agent_type):
    """Gets the class for a given agent type name."""
    return _agent_types.get(agent_type)

def create_agent_instance(agent_id, config):
    """
    Factory function to create agent instances based on config type.
    :param agent_id: Unique ID for this instance.
    :param config: Dictionary containing configuration, MUST include 'type'.
    :return: An instance of a BaseAgent subclass, or None if type is invalid/missing.
    """
    if not config or not isinstance(config, dict):
        print("Error: Agent config must be a dictionary.")
        return None

    agent_type = config.get("type")
    if not agent_type:
        print("Error: Agent config must include a 'type' key.")
        return None

    AgentClass = get_agent_class(agent_type)
    if AgentClass:
        try:
            # Instantiate the specific agent class
            instance = AgentClass(agent_id=agent_id, config=config)
            print(f"Successfully created agent instance '{agent_id}' of type '{agent_type}'.")
            return instance
        except (ValueError, TypeError) as e:
            print(f"Error creating agent '{agent_id}' of type '{agent_type}': Invalid config - {e}")
            return None
        except Exception as e:
            print(f"Unexpected error creating agent '{agent_id}': {e}")
            return None
    else:
        print(f"Error: Unknown agent type '{agent_type}'. Available types: {get_available_agent_types()}")
        return None


# Example of how to use it (will be called from main.py later)
if __name__ == "__main__":
    print("Running agents module directly for testing...")

    # --- Test WordCountAgent ---
    print("\n--- Testing WordCountAgent ---")

    # 1. Test valid creation
    valid_config = {"type": "word_counter"} # No extra config needed
    agent = create_agent_instance("wc_agent_01", valid_config)

    if agent:
        print("Metadata:", agent.get_metadata())

        # 2. Test execution with sample data
        sample_data = [
            {"content": "This is the first piece of text.", "source": "doc1"},
            {"content": "Here is some more text, \n with line breaks.", "source": "doc2"},
            {"content": "", "source": "empty_doc"}, # Empty content
            {"content": "Punctuation! Should? Be Handled.", "source": "doc3"},
            {"not_content": "Invalid format", "source": "bad_doc"}, # Missing 'content' key
             123 # Invalid list item
        ]
        print("\nExecuting agent with sample data...")
        result = agent.execute(sample_data)
        print("Execution Result:", result)

        # Expected word count:
        # "This is the first piece of text." -> 7 words
        # "Here is some more text, with line breaks." -> 8 words (simple split)
        # "" -> 0 words
        # "Punctuation Should Be Handled" -> 4 words (using regex \b\w+\b)
        # Total = 7 + 8 + 0 + 4 = 19

    # 3. Test creation with invalid type
    print("\n--- Testing Invalid Type ---")
    invalid_config_type = {"type": "non_existent_agent"}
    create_agent_instance("test_invalid_type", invalid_config_type)