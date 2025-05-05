# Keyword Extraction Agent (keyword_extractor)

The KeywordExtractAgent is a built-in OmniNexus agent that performs simple keyword extraction from the text content of provided data items. It identifies potential keywords based on word frequency after removing common English stop words.

## Functionality

*   Accepts a list of [Standard Data Items](../../protocol/data_item_structure.md) as input.
*   For each valid data item, it attempts to find usable text content:
    *   It prioritizes the payload['content'] field.
    *   If payload['content'] is missing or not a string, it falls back to combining the text from payload['subject'] and payload['from'] (useful for email headers).
*   It converts the extracted text to lowercase.
*   It splits the text into words using a regular expression (\b\w+\b).
*   It filters out common English stop words (from a predefined list within the agent) and words shorter than a configurable minimum length.
*   It counts the frequency of the remaining words across all processed data items.
*   It returns a list of the most frequent words (keywords) up to a configurable limit, along with their counts (scores).
*   It also reports the number of items processed and skipped.

## Configuration Parameters

This agent allows optional configuration *during execution* via the parameters argument passed to the execute method (e.g., specified on the CLI). It does not currently use persistent configuration stored in the datastore.

*   `type` (string, Internal)
    *   Must be set to "keyword_extractor". Handled automatically by the framework.

*   Runtime Parameters (Optional):
    *   `num_keywords` (int): The maximum number of keywords to return in the results. Defaults to 10.
    *   `min_word_length` (int): The minimum number of characters a word must have to be considered a potential keyword (after stop word removal). Defaults to 3.

## Input Format

The execute method expects data_inputs to be a list of dictionaries conforming to the [Standard Data Item Structure](../../protocol/data_item_structure.md). The agent looks for payload['content'] (string) or falls back to payload['subject'] (string) and payload['from'] (string).

## Output Format

The execute method returns a dictionary with the following keys:

*   `keywords` (list[dict]): A list containing the extracted keywords, sorted by frequency (highest first). Each dictionary in the list has:
    *   word (str): The extracted keyword (lowercase).
    *   score (int): The frequency count of the keyword across the processed items.
*   `items_processed` (int): The number of data items from which usable text content was successfully extracted and analyzed.
*   `items_skipped` (int): The number of data items that were skipped due to invalid structure or lack of usable text content (no content, subject, or from).
*   `error` (str, Optional): Included only if the top-level data_inputs was not a list.

## Example Output:

{
  "keywords": [
    { "word": "https", "score": 91 },
    { "word": "com", "score": 78 },
    { "word": "image", "score": 39 },
    { "word": "www", "score": 33 },
    { "word": "2025", "score": 27 },
    { "word": "ethiopia", "score": 20 },
    { "word": "google", "score": 19 },
    { "word": "capital", "score": 19 },
    { "word": "view", "score": 17 },
    { "word": "news", "score": 17 }
  ],
  "items_processed": 5,
  "items_skipped": 0
}

## Usage Example (CLI)

* Run with default parameters:

OmniNexus> run_keyword_extractor <connector_id>

(Uses default num_keywords=10, min_word_length=3)

* Run with custom parameters:

OmniNexus> run_keyword_extractor <connector_id> num_keywords=5 min_word_length=4

(Returns top 5 keywords with at least 4 characters)

Replace <connector_id> with the ID of an activated connector.

## Notes

The keyword extraction method is naive (based purely on frequency and stop word removal). It doesn't use advanced NLP techniques like TF-IDF, stemming, lemmatization, or part-of-speech tagging.

The built-in stop word list is basic and English-centric.

The agent aggregates counts across all input documents for a single execution run.