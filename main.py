from google import genai
from google.api_core import retry
from google.genai import types
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import CouldNotRetrieveTranscript
from rich.markdown import Markdown
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
import sys
import dotenv

client = genai.Client(api_key=dotenv.get_key('C:/repos/tg-bot/.env', 'GOOGLE_API_KEY'))
chat = client.chats.create(model="gemini-2.0-flash-001", history=[])
is_retriable = lambda e: isinstance(e, genai.errors.APIError) and e.code in {429, 503}# Определяем условие для повторных попыток
chat.send_message_stream = retry.Retry(predicate=is_retriable)(chat.send_message_stream)# Оборачиваем метод в логику повторных попыток
ytt_api = YouTubeTranscriptApi()
console = Console()
uri = ""

def answer_chek(innput: str='') -> str:
    """
    Check if the user wants to exit the program and whether they have typed the request.
    """
    while True:

        words = console.input(innput)

        if words.lower() == '/exit':
            print("Exiting the program.")
            sys.exit()
        #elif words == '':
            #if "Your text is empty." not in innput:
                #innput = "[#E66761]Your text is empty.[/] " + innput
            #continue
        elif words.lower() in ['/skip', '']:
            return '/skip'

        return words

def get_trancript() -> str:
    """
    Retrieve the transcript from a YouTube video.
    """
    global uri
    while True:
        uri = answer_chek("[#77DD77]Enter the [#E66761]YouTube[/] link or the [#E66761]video ID[/]:[/] ")
        video_id = uri.split('=')[-1]
        if video_id.lower() == '/skip':
            return ""
        try:
            transcript = ytt_api.fetch(video_id, languages=['ru', 'en', 'en-US', 'es', 'de'])
            break
        except CouldNotRetrieveTranscript as e:
            console.print(f"Error retrieving transcript: {e}", style='red')

    text = ""
    for entry in transcript:
        text += entry.text + " "
    #" ".join([entry.text for entry in transcript]).replace('[музыка]', ' ').replace('[аплодисменты]', ' ')
    text = text.replace('[музыка]', ' ').replace('[аплодисменты]', ' ').replace('\n', " ")
    return text

def send_question(**kwargs) -> None:
    """
    Send a question to the chat and display the response.
    """

    transcript = kwargs.get("transcript", "")
    question = kwargs.get("question", "")
    if transcript:
        question = transcript + "\n" + question

    while True:

        stream = chat.send_message_stream(question)

        with Live(refresh_per_second=10) as live:
            full_text = ""
            for chunk in stream:
                if chunk.text:
                    full_text += chunk.text
                    # Обновляем содержимое рамки
                    live.update(Panel(Markdown(full_text), title="Gemini's Answer", border_style="bold green"))

        question = answer_chek("[#77DD77]Your question is: [/]")
        if question.lower() == '/skip':
            return ""

def request_about_video(**kwargs) -> None:
    """
    You can include a YouTube URL with a prompt asking the model to summarize, translate, or otherwise interact with the video content.

    Limitations:
     • You can't upload more than 8 hours of YouTube video per day.
     • You can upload only 1 video per request.
     • You can only upload public videos (not private or unlisted videos).

    Note: Gemini Pro, which has a 2M context window, can handle a maximum video length of 2 hours, and Gemini Flash, which has a 1M context window, can handle a maximum video length of 1 hour.
    """
    global uri

    while True:

        question = answer_chek("[#77DD77]Your question about the video is: [/]")
        if question.lower() == '/skip':
            return ""

        stream = client.models.generate_content_stream(
            model='models/gemini-2.0-flash-001',
            contents=types.Content(
                parts=[
                    types.Part(text=question),
                    types.Part(
                        file_data=types.FileData(file_uri=uri)
                    )
                ]
            )
        )

        with Live(refresh_per_second=10) as live:
            full_text = ""
            for chunk in stream:
                if chunk.text:
                    full_text += chunk.text
                    # Обновляем содержимое рамки
                    live.update(Panel(Markdown(full_text), title="Gemini's Answer", border_style="bold green"))

def clear_history(**kwargs) -> None:
    """
    Clear the chat history.
    """
    global chat
    chat = client.chats.create(model="gemini-2.0-flash-001", history=[])
    console.print("[#77DD77]Chat history has been cleared.[/]")

def show_history(**kwargs):
    """
    Displays the chat history by iterating through the messages and formatting
    them based on their roles.
    The function retrieves the chat history using `chat.get_history()`, processes
    the messages to group consecutive messages from the same role, and prints
    the formatted responses to the console.
    Args:
        **kwargs: Arbitrary keyword arguments (not used in the current implementation).
    Returns:
        None
    """
    chat_history = chat.get_history()
    model_responses = []
    previous_role = ''
    for message in chat_history:
        response = ''
        role = message.role
        for part in message.parts:
                response += part.text
        if previous_role == role:
            model_responses[-1] += response
        else:
            previous_role = role
            response = f"{role.capitalize()}: {response}"
            model_responses.append(response)

    def prepare(x: str) -> str:
        if x.startswith("User"):
            x = "[#FFDC33]" + x.rstrip() + "[/]"
        else:
            x = "[#0BDA51]" + x.rstrip() + "[/]"
        return x

    console.print(Panel("\n".join(map(prepare, model_responses)), title="Chat history", border_style="blue"))

def exit(**kwargs):
    console.print("Exiting the program.", style='blue')
    sys.exit()

tasks = {
    '1': send_question,
    '2': send_question,
    "3": request_about_video,
    '4': clear_history,
    '5': show_history,
    '6': exit
}
questions = {
    '1': "Retell without advertising and a unnecessary information.",
    '2': "Перескажи без рекламы и неважной информации.",
    '3': "Comprehensive video analysis.",
    '4': "Clear chat history.",
    '5': "Show chat history.",
    '6': "Exit."
}

def proceed_a_task() -> None:
    """
    Handles the selection of a task or processes a user-provided question.
    This function displays a list of available tasks to the user and prompts them
    to either select a task by its number or input a custom question. If a task
    number is selected, the corresponding task is executed. If a question is
    provided, it is sent for further processing.
    """
    transcript = get_trancript()
    options = ""

    for i, question in questions.items():
        options += f"[bold #FF6E4A]{i}.[/] [#FFB02E]{question}[/]\n"

    console.print(Panel(options[:-1], title="Select a task or type your question", border_style="red"))

    task_or_question = answer_chek("[#77DD77]The task number or your question is: [/]")
    if task_or_question.lower() == '/skip':
        return ""

    # Check if the input is a task number
    if task_or_question in tasks.keys():
        tasks[task_or_question](question=questions[task_or_question], transcript=transcript)
    else:
        # Treat the input as a question and send it to the chat
        send_question(question=task_or_question, transcript=transcript)

def main():
    console.rule("YouTube Transcript Summarizer", style="bold green")
    while True:
        try:
            proceed_a_task()
        except KeyboardInterrupt:
            print("\nExiting the program. main")
            sys.exit()
        except Exception as e:
            console.print(f"An unexpected error occurred: {e}", style='red')

if __name__ == "__main__":
    main()