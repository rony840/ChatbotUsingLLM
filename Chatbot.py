import gradio as gr
from gtts import gTTS
import speech_recognition as sr
from transformers import pipeline, Conversation
import os

# Initialize the conversational model
init_chatbot = pipeline("conversational", model="facebook/blenderbot-400M-distill")

# Initialize speech recognition
recognizer = sr.Recognizer()

def add_message(history, message):
    if message["text"] is not None:
        history.append((message["text"], None))
    return history

def bot(message, history):
    user_input = message
    conversation = Conversation(user_input)
    result = init_chatbot(conversation)
    bot_response = result.generated_responses[-1]
    return bot_response, history

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

            def respond(message, history):
                bot_response, updated_history = bot(message, history)
                updated_history.append((message, bot_response))
                return updated_history, updated_history, ""

            def handle_audio(audio, history):
                text = speech_to_text(audio)
                return text, None

            # Bind the submit button to the respond function
            submit_button.click(respond, inputs=[textbox, state], outputs=[chatbot, state, textbox])
            textbox.submit(respond, inputs=[textbox, state], outputs=[chatbot, state, textbox])
            STT_convert_button.click(handle_audio, inputs=[audio_recording, state], outputs=[textbox, audio_recording])

    demo.launch() #Replace with 'demo.launch(share=True)' for temproary global link access to the gradio chatbot app
