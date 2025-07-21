import logging
import threading
import time
from typing import Type
import sys
import assemblyai as aai
from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    StreamingSessionParameters,
    TerminationEvent,
    TurnEvent,
)
from translate import Translator
import os
import dotenv
dotenv.load_dotenv()
api_key = os.getenv("API_KEY")

# global variables
transcript_history = []
full_transcript = ""
# global variables from args
default_model = "llama3.2"
translate_to_language = "es"
stream_spoken_data = True 

# Check if command line arguments are provided
if len(sys.argv) > 1:
    translate_to_language = sys.argv[1]
if len(sys.argv) > 2:
    stream_spoken_data = sys.argv[2]
if len(sys.argv) > 3:
    default_model = sys.argv[3]


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global shared time variable
last_audio_time = time.time()
timeout_seconds = 4
translator= Translator(to_lang=translate_to_language)


# Basic envent hanlers 
def on_begin(self: Type[StreamingClient], event: BeginEvent):
    print(f"Session started: {event.id}")

def on_turn(self: Type[StreamingClient], event: TurnEvent):
    global last_audio_time
    last_audio_time = time.time() 

    if event.transcript:
        # translated_text = translator.translate(event.transcript)
        transcript_history.append(event.transcript)

    print(f"{event.transcript} ({event.end_of_turn})")

    if event.end_of_turn and not event.turn_is_formatted:
        params = StreamingSessionParameters(
            format_turns=True,
        )
        self.set_params(params)

def on_terminated(self: Type[StreamingClient], event: TerminationEvent):
    print(f"Session terminated: {event.audio_duration_seconds} seconds of audio processed")

    full_transcript = " ".join(transcript_history)
    print(f"Full transcript---\n{full_transcript}")
    print(f"Translated text: {translator.translate(full_transcript)}")
    os._exit(0) 

def on_error(self: Type[StreamingClient], error: StreamingError):
    print(f"Error occurred: {error}")

def monitor_inactivity(client: StreamingClient):
    while True:
        time.sleep(1)
        if time.time() - last_audio_time > timeout_seconds:
            print("No audio received for 4 seconds. Terminating session...")
            client.disconnect(terminate=True)
            break



# Main function to handle all the functionality
def main():
    global last_audio_time
    last_audio_time = time.time()

    client = StreamingClient(
        StreamingClientOptions(
            api_key=api_key
        )
    )

    client.on(StreamingEvents.Begin, on_begin)
    client.on(StreamingEvents.Turn, on_turn)
    client.on(StreamingEvents.Termination, on_terminated)
    client.on(StreamingEvents.Error, on_error)

    client.connect(
        StreamingParameters(
            sample_rate=16000,
            format_turns=True,
        )
    )

    # Start inactivity monitor thread
    threading.Thread(target=monitor_inactivity, args=(client,), daemon=True).start()

    try:
        client.stream(
            aai.extras.MicrophoneStream(sample_rate=16000)
        )
    finally:
        client.disconnect(terminate=True)


main()
