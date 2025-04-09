from google import genai
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
ytt_api = YouTubeTranscriptApi()
console = Console()

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
    while True:
        video_id = answer_chek("[#77DD77]Enter the [#E66761]YouTube[/] link or the [#E66761]video ID[/]:[/] ").split('=')[-1]
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

        with Live(refresh_per_second=60) as live:
            full_text = ""
            for chunk in stream:
                if chunk.text:
                    full_text += chunk.text
                    # Обновляем содержимое рамки
                    live.update(Panel(Markdown(full_text), title="Gemini's Answer", border_style="bold green"))

        question = answer_chek("[#77DD77]Your question is: [/]")
        if question.lower() == '/skip':
            return ""

def clear_history(**kwargs) -> None:
    """
    Clear the chat history.
    """
    global chat
    chat = client.chats.create(model="gemini-2.0-flash-001", history=[])
    console.print("[#77DD77]Chat history has been cleared.[/]")

def exit(**kwargs):
    print("Exiting the program. exit")
    sys.exit()

tasks = {
    '1': send_question,
    '2': send_question,
    "3": clear_history,
    '4': exit
}
questions = {
    '1': "Retell without advertising and a unnecessary information. Make the reply more lively and intersting.",
    '2': "Перескажи без рекламы и неважной информации. Сделай ответ более живым и интересным.",
    '3': "Clear chat history.",
    '4': "Exit."
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
        options += f"{i}. {question}\n"

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

main()