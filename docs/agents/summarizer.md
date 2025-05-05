# Summarization Agent (summarizer)

The SummarizationAgent provides basic extractive summarization capabilities within OmniNexus. It identifies and extracts the most "important" sentences from the combined text of input data items, based on a simple word frequency scoring method.

Dependency: This agent requires the NLTK library (pip install nltk) and associated data files (punkt, stopwords, punkt_tab) to be downloaded (python -m nltk.downloader ...).

## Functionality

*   Accepts a list of [Standard Data Items](../../protocol/data_item_structure.md) as input.
*   Concatenates the text content from all processable items (prioritizing payload['content'], falling back to payload['subject'] + payload['from']).
*   Uses nltk.tokenize.sent_tokenize to split the combined text into individual sentences.
*   Calculates the frequency of relevant words (using nltk.tokenize.word_tokenize and excluding NLTK's English stopwords list and basic punctuation).
*   Scores each sentence based on the sum of the frequencies of the relevant words it contains.
*   Selects the top N sentences with the highest scores, where N is configurable (defaults to 3).
*   Sorts the selected sentences by their original order in the text.
*   Joins the selected sentences to form the final summary string.
*   Reports the summary, the number of items processed, and the number skipped.

## Configuration Parameters

This agent allows optional configuration *during execution* via the parameters argument.

*   `type` (string, Internal)
    *   Must be set to "summarizer".

*   Runtime Parameters (Optional):
    *   `summary_sentences` (int): The desired number of sentences in the output summary. Defaults to 3.

## Input Format

The execute method expects data_inputs to be a list of dictionaries conforming to the [Standard Data Item Structure](../../protocol/data_item_structure.md). The agent attempts to extract text primarily from payload['content'].

## Output Format

The execute method returns a dictionary with the following keys:

*   `summary` (str): The generated summary text, composed of the top-ranked sentences joined by spaces. Will be empty if no usable text was found or summarization failed.
*   `items_processed` (int): The number of data items from which usable text content was successfully extracted.
*   `items_skipped` (int): The number of data items that were skipped due to invalid structure or lack of usable text content.
*   `error` (str, Optional): Included if a major error occurred (e.g., input not a list, tokenization failed).

## Example Output:

{
  "summary": "US stocks rallied on Friday as investors reacted to a strong jobs report and easing recession fears. All three major indexes rose for a second-straight week. S&P and Nasdaq recovered all losses from 'Liberation Day' one month ago.",
  "items_processed": 5,
  "items_skipped": 0
}

## Usage Example (CLI)

* Run with default summary length (3 sentences):

OmniNexus> run_summarizer <connector_id>


* Run requesting a 1-sentence summary:

OmniNexus> run_summarizer <connector_id> summary_sentences=1


Replace <connector_id> with the ID of an activated connector (e.g., my_local_docs or my_real_email).

## Notes

This is an extractive summarization method; it selects existing sentences, it does not generate new ones (abstractive summarization).

The sentence scoring method is basic (sum of non-stop word frequencies) and may not always capture semantic importance accurately. More advanced algorithms exist (e.g., TF-IDF, graph-based methods like TextRank).

Requires NLTK installation and data download (punkt, stopwords, punkt_tab). The agent performs basic checks at startup.

Currently hardcoded to use English stopwords.