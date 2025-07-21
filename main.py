import logging
import threading
import time
from typing import Type
# import sys
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
import elevenlabs
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import os
import dotenv
dotenv.load_dotenv()
api_key = os.getenv("API_KEY")

transcript_history = []
full_transcript = ""

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global shared time variable
last_audio_time = time.time()
timeout_seconds = 4

def on_begin(self: Type[StreamingClient], event: BeginEvent):
    print(f"Session started: {event.id}")

def on_turn(self: Type[StreamingClient], event: TurnEvent):
    global last_audio_time
    last_audio_time = time.time() 

    if event.transcript:
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
    text_to_sppech(full_transcript)
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

def text_to_sppech(text):
    elevenlabs = ElevenLabs(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
    )
    audio = elevenlabs.text_to_speech.convert(
        text=text,
        voice_id="bIHbv24MWmeRgasZH58o",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )

    play(audio)

# text_to_sppech()
main()
