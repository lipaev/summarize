import re
import sys
import time
import dotenv
import requests

from pprint import pprint
from bs4 import BeautifulSoup

from rich.live import Live
from rich.panel import Panel
from rich.console import Console
from rich.markdown import Markdown

from google import genai
from google.genai import types
from google.api_core import retry
from google.genai.errors import ClientError

from youtube_transcript_api._errors import CouldNotRetrieveTranscript
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    NoTranscriptFound,
    TranscriptsDisabled,
)


client = genai.Client(api_key=dotenv.get_key("C:/repos/tg-bot/.env", "GOOGLE_API_KEY"))
config_with_search = types.GenerateContentConfig(
    tools=[types.Tool(google_search=types.GoogleSearch())],
    temperature=0.8,
    top_p=0.9,
    thinking_config=types.ThinkingConfig(include_thoughts=False),
)
chat = client.chats.create(
    model="models/gemini-2.5-flash", config=config_with_search, history=[]
)
# chat_2 = client.chats.create(model="gemini-2.5-pro-preview-05-06", history=[])
is_retriable = lambda e: isinstance(e, genai.errors.APIError) and e.code in {
    429,
    503,
}  # Определяем условие для повторных попыток
chat.send_message_stream = retry.Retry(predicate=is_retriable)(
    chat.send_message_stream
)  # Оборачиваем метод в логику повторных попыток
ytt_api = YouTubeTranscriptApi()
console = Console(record=True)


def answer_chek(innput: str = "") -> str:
    """
    Check if the user wants to exit the program and whether they have typed the request.
    """

    words = console.input(innput)

    if words.lower() == "/exit":
        print("Exiting the program.")
        sys.exit()
    elif words.lower() in ["/skip", ""]:
        return "/skip"

    return words


def check_skip(answer: str) -> bool:
    """
    Check if the user input is '/skip'.
    """
    return answer.lower() == "/skip"


def get_trancript() -> str:
    """
    Retrieve the transcript from a YouTube video.
    """

    attempt = 0
    max_retries = 4
    delay_seconds = 6

    uri = answer_chek(
        "[#77DD77]Enter the [#E66761]YouTube[/] link or the [#E66761]video ID[/]:[/] "
    )
    if check_skip(uri):
        return

    while True:
        if "=" in uri:
            video_id = uri.split("=")[1].split("&")[0]
        else:
            video_id = uri
        try:
            transcript = ytt_api.fetch(
                video_id, languages=["ru", "en", "en-US", "uk", "es", "de", "be"]
            )
            break
        except CouldNotRetrieveTranscript as e:
            print(str(e).strip())
            with open("error.log", "w", encoding="utf-8") as f:
                f.write(console.export_text())
            uri = answer_chek(
                "[#77DD77]Enter the [#E66761]YouTube[/] link or the [#E66761]video ID[/]:[/] "
            )
            if check_skip(uri):
                return
        except (NoTranscriptFound, TranscriptsDisabled) as e:
            print(f"Субтитры не найдены или отключены. {e}")
            return

        except Exception as e:
            # Здесь мы ловим все остальные ошибки, включая нашу ParseError
            # и возможные проблемы с сетью.
            print(f"На попытке №{attempt + 1} произошла ошибка: {e}")

            # Если это была последняя попытка, сообщаем о неудаче
            if attempt == max_retries - 1:
                print("Не удалось получить субтитры после нескольких попыток.")
                uri = answer_chek(
                    "[#77DD77]Enter the [#E66761]YouTube[/] link or the [#E66761]video ID[/]:[/] "
                )
                if check_skip(uri):
                    return
                attempt = 0
            else:
                print(f"Ждем {delay_seconds} секунд перед следующей попыткой...")
                time.sleep(delay_seconds)
                attempt += 1

    text = ""

    for entry in transcript:
        text += entry.text + " "

    text = (
        text.replace("[аплодисменты]", " ").replace("\n", " ")
    )

    return "Youtube video transcript:\n" + text

def live_update(stream, title="Gemini's Answer", border_style="bold green"):
    """
    Continuously updates a live panel with text and citations from a stream of data.
    Args:
        stream (iterable): An iterable stream of data chunks, where each chunk contains text and optional metadata.
        title (str, optional): The title of the live panel. Defaults to "Gemini's Answer".
        border_style (str, optional): The style of the panel border. Defaults to "bold green".
    Behavior:
        - Iterates over the provided stream of data chunks.
        - Appends text from each chunk to the displayed content.
        - If grounding metadata is present in a chunk, adds citations and links to the content.
        - Updates the live panel in real-time with the processed content.
    Notes:
        - The function uses the `Live` class from the `rich` library to create and update the live panel.
        - Citations are extracted from grounding metadata and formatted as Markdown links.
        - Text segments are replaced with their corresponding citations when applicable.
    """

    with Live(refresh_per_second=6) as live:
        full_text = ""
        for chunk in stream:
            if chunk.text:
                full_text += chunk.text
                grounding_metadata = chunk.candidates[0].grounding_metadata

                if (
                    grounding_metadata
                    and grounding_metadata.grounding_supports
                    and grounding_metadata.grounding_chunks
                ):
                    full_text += "\n\n**Citations:**"
                    chunks = grounding_metadata.grounding_chunks
                    dictionary: dict = {}
                    for i, _chunk in enumerate(chunks, start=1):
                        full_text += f" {i} [{_chunk.web.title}]({_chunk.web.uri})"
                        dictionary[i] = f"[{i}]({_chunk.web.uri})"

                    supports = grounding_metadata.grounding_supports
                    for support in supports:
                        plus: str = support.segment.text

                        for i in support.grounding_chunk_indices:
                            plus += f"~{dictionary[i+1]}"

                        full_text = full_text.replace(support.segment.text, plus)

                    if (
                        grounding_metadata.search_entry_point
                        and grounding_metadata.search_entry_point.rendered_content
                    ):
                        html_content = (
                            grounding_metadata.search_entry_point.rendered_content
                        )

                        # Парсим HTML
                        soup = BeautifulSoup(html_content, "html.parser")

                        # Преобразуем HTML в Markdown
                        html_content = ""
                        for tag in soup.find_all():
                            if tag.name == "h1":
                                html_content += f"# {tag.text}\n"
                            elif tag.name == "p":
                                html_content += f"{tag.text}\n"
                            elif tag.name == "a":
                                html_content += f"[{tag.text}]({tag['href']})\n"

                        full_text += "\n\nGoogle queries: " + html_content

                    def replace_citations_in_block(match_obj):
                        lang = (
                            match_obj.group(1) if match_obj.group(1) else ""
                        )  # Capture language identifier (optional)
                        content = match_obj.group(
                            2
                        )  # Capture the content of the code block
                        # Replace all citation patterns like (1) with (1) inside the content
                        modified_content = re.sub(
                            r"\(\[(\d+)\]\(.*?\)\)", r"", content
                        )  # (\1)
                        # Reconstruct the code block
                        return f"```{lang}\n{modified_content}\n```"

                    # Убирают ссылки внутри кода и сразу после, соответственно
                    full_text = re.sub(
                        r"```([a-zA-Z]*\W*)?\n(.*?)\n```",
                        replace_citations_in_block,
                        full_text,
                        flags=re.DOTALL,
                    )
                    full_text = re.sub(
                        r"\n``` \(\[\d+\]\(.*?\)\)\n",
                        r"\n```\n",
                        full_text,
                        flags=re.DOTALL,
                    )
                    full_text = re.sub(r" \[i\]", r"", full_text)

                # Обновляем содержимое рамки. themes: native fruity
                live.update(
                    Panel(
                        Markdown(full_text, code_theme="native"),
                        title=title,
                        border_style=border_style,
                    )
                )


def send_question(**kwargs) -> None:
    """
    Send a question to the chat and display the response.
    """

    transcript = kwargs.get("transcript", "")
    question = kwargs.get("question", "")
    config = kwargs.get("config", None)
    if transcript:
        question = transcript + "\n" + question

    while True:

        stream = chat.send_message_stream(question, config)

        live_update(stream)

        question = answer_chek("[#77DD77]Your question is: [/]")
        if check_skip(question):
            return


def request_about_video(**kwargs) -> None:
    """
    You can include a YouTube URL with a prompt asking the model to summarize, translate, or otherwise interact with the video content.

    Limitations:
     • You can't upload more than 8 hours of YouTube video per day.
     • You can upload only 1 video per request.
     • You can only upload public videos (not private or unlisted videos).

    Note: Gemini Pro, which has a 2M context window, can handle a maximum video length of 2 hours, and Gemini Flash, which has a 1M context window, can handle a maximum video length of 1 hour.
    """

    uri = answer_chek("[#77DD77]Enter the [#E66761]YouTube[/] link:[/] ")
    if check_skip(uri):
        return

    question = answer_chek("[#77DD77]Your question about the video is: [/]")
    if check_skip(question):
        return

    stream = chat.send_message_stream(
        [types.Part(text=question), types.Part(file_data=types.FileData(file_uri=uri))]
    )

    live_update(stream)

    while True:

        question = answer_chek("[#77DD77]Your question about the video is: [/]")
        if check_skip(question):
            return ""

        stream = chat.send_message_stream(question)

        live_update(stream)


def parse_site(**kwargs):

    url: str = answer_chek("[#77DD77]Enter the [#E66761]link[/]: [/]")
    if check_skip(url):
        return ""

    def return_site_text(url):
        """
        This function fetches the text content of a webpage given its URL.
        Args:
            url: _description_

        Returns:
            _description_
        """
        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(strip=True)

            return text

        except Exception as e:
            return f"Ошибка: {e}"

    question = answer_chek("[#77DD77]Your question is: [/]")
    if check_skip(question):
        return ""

    site: str = return_site_text(url)

    send_question(transcript=site, question=question)


def clear_history(**kwargs) -> None:
    """
    Clear the chat history.
    """
    global chat
    chat = client.chats.create(model="gemini-2.0-flash-001", history=[])
    console.print("[blue]Chat history has been cleared.[/]")


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
    previous_role = ""

    for message in chat_history:
        response = ""
        role = message.role
        for part in message.parts:
            response += "" if part.text is None else part.text
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

    console.print(
        Panel(
            "\n".join(map(prepare, model_responses)),
            title="Chat history",
            border_style="blue",
        )
    )


def exit(**kwargs):
    console.print("Exiting the program.", style="blue")
    sys.exit()


tasks = {
    "1": send_question,
    "2": send_question,
    "3": request_about_video,
    "4": parse_site,
    "5": clear_history,
    "6": show_history,
    "7": exit,
}
questions = {
    "1": "Recount succinctly.",
    "2": "Перескажи лаконично на русском.",
    "3": "Comprehensive video analysis. The video must be less than 2 hour.",
    "4": "Site analysis.",
    "5": "Clear chat history.",
    "6": "Show chat history.",
    "7": "Exit.",
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

    console.print(
        Panel(
            options[:-1],
            title="Select a task or type your question",
            border_style="red",
        )
    )

    task_or_question = answer_chek("[#77DD77]The task number or your question is: [/]")
    if check_skip(task_or_question):
        return ""

    # Check if the input is a task number
    if task_or_question in tasks.keys():
        tasks[task_or_question](
            question=questions[task_or_question], transcript=transcript
        )
    else:
        # Treat the input as a question and send it to the chat
        send_question(question=task_or_question, transcript=transcript)


def main():
    console.rule("YouTube Transcript Summarizer", style="bold green")

    while True:
        try:
            proceed_a_task()
        except ClientError as e:
            pprint(e.details)
            with open("error.log", "w", encoding="utf-8") as f:
                f.write(console.export_text())
        except Exception as e:
            print(e)
            with open("error.log", "w", encoding="utf-8") as f:
                f.write(console.export_text())


if __name__ == "__main__":
    main()
