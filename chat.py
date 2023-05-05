import openai
import requests
import json
import os
from playsound import playsound
from dotenv import load_dotenv
import threading
import argparse
import random
import speech_recognition as sr


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
eleven_labs_key = os.getenv("ELEVEN_LABS_KEY")
eleven_labs_voice = os.getenv("ELEVEN_LABS_VOICE_ID")
gpt_model = "gpt-4"


def listen_for_input(recognizer, microphone, playback_finished_event):
    # Wait for the playback to finish
    playback_finished_event.wait()

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening...")
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print("You said:", text)
        return text
    except sr.UnknownValueError:
        print("Could not understand audio")
        return None
    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))
        return None


def get_initial_message(conversation_history):
    if not conversation_history:
        greetings = ["Hello!", "Hi!", "Hey there!"]
        return random.choice(greetings)
    else:
        last_message = conversation_history[-1]["content"]
        options = [
            # f"Last time we talked about {last_message}. Do you want to continue?",
            # f"Welcome back! We were discussing {last_message}. What's next?",
            # f"Hi again! Let's pick up where we left off: {last_message}."
            "Hello!"
        ]
        return random.choice(options)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Voice-enabled Chatbot")
    parser.add_argument("--voice", action="store_true", help="Enable voice input")
    args = parser.parse_args()
    return args


def generate_response(conversation_history):
    response = openai.ChatCompletion.create(
        model=gpt_model,
        messages=conversation_history,
        max_tokens=150,
        n=1,
        temperature=0.8,
    )
    message = response.choices[0].message.content.strip()
    return message


def save_conversation_history(
    conversation_history, file_path="conversation_history.json"
):
    with open(file_path, "w") as f:
        json.dump(conversation_history, f)


def load_conversation_history(file_path="conversation_history.json"):
    try:
        with open(file_path, "r") as f:
            conversation_history = json.load(f)
    except FileNotFoundError:
        conversation_history = []

    return conversation_history


mutex_lock = threading.Lock()

tts_headers = {"Content-Type": "application/json", "xi-api-key": eleven_labs_key}


def eleven_labs_speech(text, playback_finished_event):
    tts_url = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}".format(
        voice_id=eleven_labs_voice
    )
    formatted_message = {"text": text}
    response = requests.post(tts_url, headers=tts_headers, json=formatted_message)

    if response.status_code == 200:
        with mutex_lock:
            with open("speech.mpeg", "wb") as f:
                f.write(response.content)

            playsound("speech.mpeg", True)

            os.remove("speech.mpeg")

        # Signal that playback has finished
        playback_finished_event.set()
        return True
    else:
        print("Request failed with status code:", response.status_code)
        print("Response content:", response.content)
        return False


def speak_thread(response, playback_finished_event):
    eleven_labs_speech(response, playback_finished_event)


def chat(args):
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    playback_finished_event = threading.Event()

    conversation_history = load_conversation_history()

    conversation_history.append(
        {
            "role": "system",
            "content": (
                "Your name is Dendrite. Address yourself as such."
                "Limit your responses to a maximum of 200 tokens."
                "If you understand, reply only to this message with a variation of 'Hello'. Don't explicitely say you understand."
            ),
        }
    )

    response = openai.ChatCompletion.create(
        model=gpt_model,
        messages=conversation_history,
        max_tokens=300,
        n=1,
        temperature=0.8,
    )

    response_text = response.choices[0].message["content"]
    playback_finished_event.clear()
    t = threading.Thread(
        target=speak_thread, args=(response_text, playback_finished_event)
    )
    conversation_history.append({"role": "assistant", "content": response_text})

    print("Assistant:", response_text)

    t.start()
    if args.voice:
        playback_finished_event.wait()

    while True:
        if args.voice:
            user_input = listen_for_input(
                recognizer, microphone, playback_finished_event
            )
            if user_input is None:
                continue
        else:
            user_input = input("You: ")

        if user_input.lower() == "quit":
            break

        print("Assistant: Thinking...")

        conversation_history.append({"role": "user", "content": user_input})

        response = openai.ChatCompletion.create(
            model=gpt_model,
            messages=conversation_history,
            max_tokens=150,
            n=1,
            temperature=0.8,
        )

        response_text = response.choices[0].message["content"]
        playback_finished_event.clear()
        t = threading.Thread(
            target=speak_thread, args=(response_text, playback_finished_event)
        )
        conversation_history.append({"role": "assistant", "content": response_text})

        print("Assistant:", response_text)

        # Start a new thread to play the response and wait for the playback to finish if voice flag is active
        t.start()
        if args.voice:
            playback_finished_event.wait()

        save_conversation_history(conversation_history)


if __name__ == "__main__":
    args = parse_arguments()
    chat(args)
