import os
import subprocess
import sys

# Define the name of the virtual environment
venv_name = 'chatbot_env'

# Check if the virtual environment already exists
if not os.path.exists(venv_name):
    print(f"Creating virtual environment: {venv_name}")
    subprocess.check_call([sys.executable, '-m', 'venv', venv_name])

# Install required packages
required_packages = [
    'gradio',
    'gtts',
    'SpeechRecognition',
    'python-multipart',
    'groq'
]

# Activate the virtual environment and install the packages
venv_pip = os.path.join(venv_name, 'Scripts', 'pip')
try:
    subprocess.check_call([venv_pip, 'install'] + required_packages)
except Exception as e:
    print("Error installing packages:", e)

import gradio as gr
from gtts import gTTS
import speech_recognition as sr
from groq import Groq
import os

# Set your API key directly here
os.environ["GROQ_API_KEY"] = "ENTER YOUR GROQ API KEY HERE"

# Initialize the GROQ client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Initialize speech recognition
recognizer = sr.Recognizer()

chat_history = []
bot_history = []
def add_message(chat_history, message):
    if message["text"] is not None:
        chat_history.append((message["text"], None))
        print("Printing History After adding message: \n",chat_history)
    return chat_history

def bot(message, bot_history):
    print("Printing ChatHistory Before adding message: \n",chat_history)
    user_input = message
    # Add user message to the conversation history
    bot_history.append({
        "role": "user",
        "content": user_input
    })

    # Create a chat completion
    chat_completion = client.chat.completions.create(
        messages=bot_history,
        model="llama3-8b-8192",
    )
    # Get the response from the chatbot
    bot_response = chat_completion.choices[0].message.content

    # Print the bot's response
    print(f"Chatbot: {bot_response}")
    # Add the bot's message to the conversation history
    bot_history.append({
        "role": "assistant",
        "content": bot_response
    })
    print("Printing BotHistory After adding bot response: \n",chat_history)
    return bot_response, chat_history

def speech_to_text(audio_file_path):
    with sr.AudioFile(audio_file_path) as source:
        audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)
    return text

def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    audio_file_path = 'TTS_Audio.mp3'
    tts.save(audio_file_path)
    return audio_file_path

with gr.Blocks(title="Chatbot using LLM") as demo:
    with gr.Row():
        with gr.Column():  # audio processing goes here
            # Define TTS playback component
            TTS_audio = gr.Audio(
                label="TTS - Text to Speech",
                type="filepath",  # Use filepath type
            )

            # Define TTS textbox to hold text for audio conversion
            TTS_textbox = gr.Textbox(
                label="",
                placeholder="Paste the Copied message here to convert it to audio",
                visible=True,
            )

            # Define convert button for converting text to audio
            TTS_convert_button = gr.Button(value="Convert Text to Audio")

            # Function to convert text from TTS_textbox to audio
            def handle_conversion(text):
                if text:
                    audio_file_path = text_to_speech(text)
                    return audio_file_path
                return None

            # Bind the convert button to the handle_conversion function
            TTS_convert_button.click(
                fn=lambda text: handle_conversion(text),
                inputs=[TTS_textbox],
                outputs=[TTS_audio]
            )

            # Define audio recording component
            audio_recording = gr.Microphone(
                label="STT - Speech to Text",
                sources="microphone",
                type="filepath",
            )
            # Define convert audio button
            STT_convert_button = gr.Button(value="Convert Audio to Text")

        with gr.Column():  # chat goes here
            # Define chatbot section
            chatbot = gr.Chatbot(
                elem_id="chatbot",
                bubble_full_width=False,
                scale=1,
                show_copy_button=True,  # Show copy button for each message
            )
            chatbot.has_event("select")
            # Define chat input textbox
            textbox = gr.Textbox(
                placeholder="Type your query or use record button to use Speech-To-Text (STT)...",
            )
            # Define submit button with airplane icon
            submit_button = gr.Button(value="Send")

            state = gr.State([])  # Initialize the state for chat history

            def respond(message, chat_history):
                bot_response, updated_history = bot(message, bot_history)
                updated_history.append((message, bot_response))
                print("Printing Updated ChatHistory after respond: \n",updated_history)
                return updated_history, updated_history, ""

            def handle_audio(audio, history):
                text = speech_to_text(audio)
                return text, None

            # Bind the submit button to the respond function
            submit_button.click(respond, inputs=[textbox, state], outputs=[chatbot, state, textbox])
            textbox.submit(respond, inputs=[textbox, state], outputs=[chatbot, state, textbox])
            STT_convert_button.click(handle_audio, inputs=[audio_recording, state], outputs=[textbox, audio_recording])

    demo.launch() #Replace with 'demo.launch(share=True)' for temproary global link access to the gradio chatbot app