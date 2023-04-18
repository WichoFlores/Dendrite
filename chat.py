import openai
import requests
import json
import os
from playsound import playsound
from dotenv import load_dotenv
import threading
import speech_recognition as sr
import argparse
import random


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
eleven_labs_key = os.getenv("ELEVEN_LABS_KEY")
eleven_labs_voice = os.getenv("ELEVEN_LABS_VOICE_ID")


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
    parser.add_argument("--voice", action="store_true",
                        help="Enable voice input")
    args = parser.parse_args()
    return args


def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Calibrating microphone... Please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=1)

    while True:
        print("Recognizing...")
        with sr.Microphone() as source:
            audio = recognizer.listen(source)
        try:
            speech = recognizer.recognize_google(audio)
            return speech
        except sr.UnknownValueError:
            print("Could not understand. Please try again.")
        except sr.RequestError as e:
            print(f"Error: {e}. Please try again.")


def generate_response(conversation_history):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation_history,
        max_tokens=150,
        n=1,
        temperature=0.8,
    )
    message = response.choices[0].message.content.strip()
    return message


def save_conversation_history(conversation_history, file_path="conversation_history.json"):
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

tts_headers = {
    "Content-Type": "application/json",
    "xi-api-key": eleven_labs_key
}


def eleven_labs_speech(text):
    tts_url = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}".format(
        voice_id=eleven_labs_voice)
    formatted_message = {"text": text}
    response = requests.post(
        tts_url, headers=tts_headers, json=formatted_message)

    if response.status_code == 200:
        with mutex_lock:
            with open("speech.mpeg", "wb") as f:
                f.write(response.content)

            playsound("speech.mpeg", True)

            os.remove("speech.mpeg")
        return True
    else:
        print("Request failed with status code:", response.status_code)
        print("Response content:", response.content)
        return False


def speak_thread(response):
    eleven_labs_speech(response)


def chat(voice_to_text=False):
    conversation_history = load_conversation_history()
    initial_message = get_initial_message(conversation_history)
    print("Assistant:", initial_message)

    t = threading.Thread(target=speak_thread, args=(initial_message,))
    conversation_history.append(
        {"role": "assistant", "content": initial_message})
    t.start()

    while True:
        if voice_to_text:
            user_input = recognize_speech()
            if user_input is None:
                print("Please try again.")
                continue
        else:
            user_input = input("You: ")

        if user_input.lower() == "quit":
            break

        print("Assistant: Thinking...")

        conversation_history.append({"role": "user", "content": user_input})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            max_tokens=150,
            n=1,
            temperature=0.8,
        )

        response_text = response.choices[0].message['content']
        t = threading.Thread(target=speak_thread, args=(response_text,))
        conversation_history.append(
            {"role": "assistant", "content": response_text})

        print("Assistant:", response_text)

        # Start a new thread to play the response
        t.start()

        save_conversation_history(conversation_history)


if __name__ == "__main__":
    args = parse_arguments()
    chat(voice_to_text=args.voice)
