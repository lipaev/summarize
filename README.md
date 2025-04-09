# YouTube Transcript Summarizer

This Python script allows users to retrieve YouTube video transcripts and summarize them using Google's Gemini AI model. It provides an interactive console interface for users to input YouTube video links or IDs, ask questions, and receive summarized responses.

## Features

- **YouTube Transcript Retrieval**: Fetch transcripts from YouTube videos in multiple languages (e.g., English, Russian, Spanish, etc.).
- **AI-Powered Summarization**: Summarize transcripts and answer user questions using the Gemini AI model.
- **Interactive Console**: User-friendly console interface with options to input questions, clear chat history, or exit the program.
- **Customizable Questions**: Predefined tasks and the ability to input custom questions.
- **Real-Time Streaming**: Displays AI responses in real-time using the `rich` library.

## Requirements

- Python 3.8 or higher
- A valid Google API key for the Gemini AI model
- Required Python libraries (see below)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/lipaev/summarize.git
   cd summarize
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your `.env` file:
   - Create a `.env` file in the root directory.
   - Add your Google API key:
     ```
     GOOGLE_API_KEY=your_google_api_key
     ```

## Usage

1. Run the script:
   ```bash
   python summarize.py
   ```

2. Follow the interactive prompts:
   - Enter a YouTube video link or ID to fetch the transcript.
   - Choose a predefined task or type your custom question.
   - View the AI-generated response in real-time.

3. Available tasks:
   - **1**: Summarize the transcript in English.
   - **2**: Summarize the transcript in Russian.
   - **3**: Clear chat history.
   - **4**: Exit the program.

4. Use `/exit` to quit the program or `/skip` to skip a step.

## File Structure

- `summarize.py`: Main script for the summarizer.
- `.env`: Environment file for storing the Google API key.
- `requirements.txt`: List of required Python libraries.

## Dependencies

The script uses the following Python libraries:
- `google-genai`: For interacting with the Gemini AI model.
- `youtube-transcript-api`: For fetching YouTube video transcripts.
- `rich`: For creating a visually appealing console interface.
- `python-dotenv`: For managing environment variables.

Install all dependencies using:
```bash
pip install -r requirements.txt
```

## Error Handling

- If the transcript cannot be retrieved, an error message will be displayed, and the user will be prompted to try again.
- Unexpected errors are caught and displayed in the console.

## License

This project is licensed under the MIT License.

## Acknowledgments

- [YouTube Transcript API](https://github.com/jdepoix/youtube-transcript-api)
- [Rich Library](https://github.com/Textualize/rich)
- [Google GenAI](https://cloud.google.com/genai)

Feel free to contribute or report issues in the repository!