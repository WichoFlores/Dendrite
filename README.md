# Dendrite
Dendrite is a voice-enabled chatbot that uses OpenAI's GPT-3.5-turbo model for generating responses and the Eleven Labs TTS API for speech synthesis. The chatbot can receive text or voice input from the user and respond with synthesized speech.

## Installation
1. Clone the repository or download the source code.

2. Install the required packages using the requirements.txt file:


```
pip install -r requirements.txt
```

3. Create a .env file in the project directory with the following content:

```
OPENAI_API_KEY=<your_openai_api_key>
ELEVEN_LABS_KEY=<your_eleven_labs_api_key>
ELEVEN_LABS_VOICE_ID=<your_eleven_labs_voice_id>
```


## Usage
Run the chatbot script with the following command:

```
python dendrite.py
```

By default, the chatbot uses text input. To enable voice input, use the --voice flag:
```
python dendrite.py --voice
```
To quit the chatbot, type "quit" and press Enter.

## Features
- Text and voice input options
- Uses OpenAI's GPT-3.5-turbo model for generating responses
- Speech synthesis using the Eleven Labs TTS API
- Saves conversation history in a JSON file
- Continues the conversation based on previous history (if available)

## Dependencies
- openai
- requests
- playsound
- python-dotenv
- SpeechRecognition
- argparse
