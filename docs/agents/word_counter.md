# Word Count Agent (word_counter)

The WordCountAgent is a simple, built-in OmniNexus agent that counts the total number of words across a collection of data items provided to it.

## Functionality

*   Accepts a list of [Standard Data Items](../../protocol/data_item_structure.md) as input.
*   For each valid data item, it accesses the primary textual content stored in the payload['content'] field.
*   It uses a simple regular expression (\b\w+\b) to identify sequences of "word characters" (letters, numbers, underscore).
*   It counts the total number of such words found across all processed data items.
*   It reports the total word count, the number of data items successfully processed, and the number of items skipped due to missing or invalid structure/content.

## Configuration Parameters

This agent type currently does not require any specific configuration parameters when it is created or run. Its behavior is fixed.

*   `type` (string, Internal)
    *   Must be set to "word_counter". Handled automatically by the framework/CLI.

## Input Format

The execute method expects data_inputs to be a list of dictionaries, where each dictionary conforms to the [Standard Data Item Structure](../../protocol/data_item_structure.md). The agent specifically looks for the payload['content'] key within each item and expects its value to be a string.

## Output Format

The execute method returns a dictionary with the following keys:

*   `total_words` (int): The total count of words found in the payload['content'] of all successfully processed data items.
*   `items_processed` (int): The number of data items in the input list that had a valid structure and string content in payload['content'].
*   `items_skipped` (int): The number of data items in the input list that were skipped because they didn't conform to the expected structure or payload['content'] was missing or not a string.
*   `error` (str, Optional): Included only if the top-level data_inputs was not a list.

## Example Output:

{
  "total_words": 4116,
  "items_processed": 5,
  "items_skipped": 0
}

## Usage Example (CLI)
OmniNexus> run_word_count <connector_id>


Replace <connector_id> with the ID of an activated connector (e.g., my_local_docs or my_real_email). The orchestrator will query the connector, get the data items, create an instance of the WordCountAgent, and pass the items to its execute method. The resulting dictionary will be printed.

## Notes

The word counting method is simple and based on whitespace and common punctuation separation via the regex. It may not perfectly match word counts from sophisticated word processors in all edge cases.

The agent currently processes the combined text from all input items together to produce a single total count.