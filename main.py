import gradio as gr
import os 
from dotenv import load_dotenv
import assemblyai as aai
from translate import Translator
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import uuid

# Load API Key
load_dotenv()
aai.settings.api_key = os.getenv("API_KEY")

def voice_translation(audio_path): 
    try:
        transcriber = aai.Transcriber()
        config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.slam_1)
        transcript = transcriber.transcribe(audio_path, config=config)

        if transcript.error:
            return f"Transcription Error: {transcript.error}"
        else:
            text = transcript.text

        text = translate_text(text)
        audio = text_to_speech(text)
        return text, audio

    except Exception as e:
        return f"Error: {str(e)}"

def translate_text(text):
    
    translator_es = Translator(to_lang="es")
    text_es = translator_es.translate(text)
    return text_es

def text_to_speech(text):
    elevenlabs = ElevenLabs(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        ) 
    audio = elevenlabs.text_to_speech.convert(
        text=text,
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    file_path = f"{uuid.uuid4()}.mp3"
    with open(file_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    return file_path


demo = gr.Interface(
    fn=voice_translation,
    inputs=gr.Audio(sources=["microphone", "upload"], type="filepath", label="Speak or Upload Audio"),
    outputs=[gr.Textbox(label="Transcribed Text"), gr.Audio(label="Translated Audio")],
    title="Voice to Voice Translator"
)

demo.launch()
