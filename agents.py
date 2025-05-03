# OmniNexus - agents.py
# Defines the base structure for AI agents and implements specific agents.

from abc import ABC, abstractmethod
import re # For simple word counting

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
    A simple agent that counts words in the provided text data.
    """

    @classmethod
    def get_config_schema(cls):
        # This agent has no specific configuration parameters needed at creation time
        return {}

    def validate_config(self):
        """No specific configuration to validate for this agent."""
        # Could add checks if config is not empty, if desired
        if self.config:
             print(f"Warning: WordCountAgent '{self.agent_id}' received unexpected config: {self.config}")
        pass # No validation needed for empty config

    def get_metadata(self):
        """Returns metadata about the WordCountAgent."""
        return {
            "agent_id": self.agent_id,
            "type": "word_counter",
            "description": "Counts the total number of words in provided text inputs.",
            "input_format": "List of dictionaries, each with a 'content' key containing text.",
            "output_format": "Dictionary {'total_words': count}"
        }

    def execute(self, data_inputs, parameters=None):
        """
        Counts words in the 'content' field of each item in data_inputs.
        :param data_inputs: List of dicts, e.g., [{'content': 'text one'}, {'content': 'text two'}]
        :param parameters: Ignored by this agent.
        :return: Dictionary {'total_words': count}
        """
        total_words = 0
        if not isinstance(data_inputs, list):
             print(f"Error: WordCountAgent expects a list of data inputs, got {type(data_inputs)}")
             return {"total_words": 0, "error": "Invalid input format"}

        print(f"WordCountAgent '{self.agent_id}' executing on {len(data_inputs)} data inputs...")

        for item in data_inputs:
            if isinstance(item, dict) and 'content' in item:
                content = item['content']
                if isinstance(content, str):
                    # Simple word count: split by whitespace and count non-empty tokens
                    words = re.findall(r'\b\w+\b', content) # Find sequences of word characters
                    count = len(words)
                    total_words += count
                    # print(f"  - Processed input with {count} words.") # Optional: uncomment for debugging
                else:
                    print(f"Warning: Input item 'content' is not a string: {type(content)}")
            else:
                print(f"Warning: Skipping invalid input item format: {item}")

        print(f"WordCountAgent '{self.agent_id}' finished execution. Total words: {total_words}")
        return {"total_words": total_words}


# --- Agent Registry and Factory ---

# Dictionary to hold available agent *classes*
_agent_types = {
    "word_counter": WordCountAgent
    # Future: Add more agent types here (e.g., "summarizer", "keyword_extractor")
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