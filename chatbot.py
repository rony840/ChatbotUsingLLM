from transformers import pipeline, Conversation
from flask import Flask, request, jsonify, render_template_string, send_file
from getpass import getpass
import os
import pyttsx3  # Text-to-Speech library

app = Flask(__name__)
chatbot = pipeline(task="conversational", model="facebook/blenderbot-400M-distill")

max_length = 128  # Maximum length allowed by the model
conversation_history = []  # To store the entire conversation history

template = """
<!DOCTYPE html>
<html>
<head>
    <title>Chat with Bot</title>
</head>
<body>
    <div style="font-family: Arial; padding: 20px;">
        <h2>Chat with Bot</h2>
        <div id="chat-box" style="border: 1px solid #ccc; height: 300px; overflow-y: scroll; padding: 10px; margin-bottom: 10px;"></div>
        <input type="text" id="user-input" style="width: 100%; padding: 8px;" placeholder="Type your message..." onkeypress="checkEnter(event)">
        <button onclick="sendMessage()">Send</button>
        <p id="status" style="font-style: italic; color: gray;"></p>
        <button id="start-recording-btn" onclick="startListening()">🎙️ Start Recording</button>
        <button id="stop-recording-btn" onclick="stopListening()" disabled>⏹️ Stop Recording</button>
        <p id="recording-status"></p>
    </div>
    <script>
        let recognition;
        let isPlaying = false;
        let isRecording = false;

        async function sendMessage() {
            const userInput = document.getElementById('user-input').value;
            if (!userInput.trim()) return;
            document.getElementById('user-input').value = '';
            document.getElementById('status').innerText = 'Generating response...';

            const response = await fetch('/send_message', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: userInput})
            });
            const data = await response.json();

            const chatBox = document.getElementById('chat-box');
            chatBox.innerHTML += <p style="margin: 5px 0;"><strong>You:</strong> ${userInput} <button onclick="playText(&quot;${encodeURIComponent(userInput)}&quot;)">▶️</button></p>;
            chatBox.innerHTML += <p style="margin: 5px 0;"><strong>Bot:</strong> ${data.response} <button onclick="playText(&quot;${encodeURIComponent(data.response)}&quot;)">▶️</button></p>;
            document.getElementById('status').innerText = '';
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function checkEnter(event) {
            if (event.key === 'Enter' && !isRecording) {
                sendMessage();
            }
        }

        function startListening() {
            if (recognition) {
                recognition.stop();
                recognition = null;
                document.getElementById('status').innerText = '';
                return;
            }

            recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = 'en-US';
            recognition.interimResults = false;
            recognition.continuous = true;
            recognition.start();
            document.getElementById('status').innerText = 'Listening...';
            document.querySelectorAll('button').forEach(btn => btn.disabled = true);
            document.getElementById('stop-recording-btn').disabled = false;
            isRecording = true;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                const currentText = document.getElementById('user-input').value;
                document.getElementById('user-input').value = currentText + ' ' + transcript;
            };

            recognition.onerror = function(event) {
                console.error('Error occurred in recognition: ', event.error);
                stopListening();
            };
        }

        function stopListening() {
            if (recognition) {
                recognition.stop();
                recognition = null;
                document.getElementById('recording-status').innerText = '';
                document.querySelectorAll('button').forEach(btn => btn.disabled = false);
                document.getElementById('stop-recording-btn').disabled = true;
                isRecording = false;
                sendMessage();
            }
        }

        function playText(text) {
            if (isPlaying) return;
            isPlaying = true;
            document.querySelectorAll('button').forEach(btn => btn.disabled = true);
            const audio = new Audio(/tts?text=${text});
            audio.play();
            audio.onended = function() {
                document.querySelectorAll('button').forEach(btn => btn.disabled = false);
                isPlaying = false;
            };
        }
    </script>
</body>
</html>


"""

def truncate_conversation_history(history, max_length):
    total_length = sum(len(entry['text']) for entry in history)
    while total_length > max_length and history:
        total_length -= len(history.pop(0)['text'])

@app.route('/')
def index():
    return render_template_string(template)

@app.route('/send_message', methods=['POST'])
def handle_message():
    global conversation_history  # Declare conversation_history as global
    user_input = request.json.get("message")

    if user_input.lower() == "bye":
        return jsonify({"response": "Goodbye! Have a Wonderful Day!", "conversation": conversation_history})

    # Update conversation history
    conversation_history.append({"role": "user", "text": user_input})

    # Create a single conversation object from the history
    conversation_texts = " ".join([f"{entry['role']}: {entry['text']}" for entry in conversation_history])
    conversation = Conversation(conversation_texts)

    # Ensure the total token length is within the model's limit
    truncate_conversation_history(conversation_history, max_length)
    conversation_texts = " ".join([f"{entry['role']}: {entry['text']}" for entry in conversation_history])
    conversation = Conversation(conversation_texts)

    conversation = chatbot(conversation)
    bot_response = conversation.generated_responses[-1]

    # Update conversation history with bot response
    conversation_history.append({"role": "bot", "text": bot_response})

    return jsonify({"response": bot_response, "conversation": conversation_history})

@app.route('/tts')
def text_to_speech():
    text = request.args.get('text', '')
    engine = pyttsx3.init()
    engine.save_to_file(text, 'response.mp3')
    engine.runAndWait()
    return send_file('response.mp3')

if __name__ == "__main__":
    HUGGINGFACEHUB_API_TOKEN = getpass()
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACEHUB_API_TOKEN
    app.run(debug=True)
