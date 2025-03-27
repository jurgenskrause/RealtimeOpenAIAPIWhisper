import os
import math
import uuid
import ffmpeg
import json
import wave
import pyaudio
import threading
import queue
import time
import difflib
from openai import OpenAI
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime

# CONFIG
CHUNK_LEN_SEC = 4  # Shorter chunks for more responsive output
CHUNK_SIZE = 1024  # Number of frames per buffer
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
MODEL_NAME = "whisper-1"
OVERLAP_SEC = 1  # Reduced overlap between chunks

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AudioRecorder:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.recording = False
        self.chunk_queue = queue.Queue()
        self.current_chunk = []
        self.total_samples = 0
        self.samples_per_chunk = RATE * CHUNK_LEN_SEC
        self.chunk_number = 0

    def start(self):
        """Start recording from microphone"""
        self.stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )
        self.recording = True
        self.total_samples = 0
        self.current_chunk = []
        self.chunk_number = 0
        
        # Start recording thread
        self.record_thread = threading.Thread(target=self._record_loop)
        self.record_thread.start()

    def stop(self):
        """Stop recording"""
        self.recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, 'record_thread'):
            self.record_thread.join()

    def _record_loop(self):
        """Main recording loop"""
        while self.recording:
            try:
                data = self.stream.read(CHUNK_SIZE)
                self.current_chunk.append(data)
                self.total_samples += CHUNK_SIZE

                # Check if we have a complete chunk
                if self.total_samples >= self.samples_per_chunk:
                    # Send the chunk for processing
                    self.chunk_number += 1
                    self.chunk_queue.put(b''.join(self.current_chunk))
                    
                    # Reset for next chunk
                    self.current_chunk = []
                    self.total_samples = 0

            except Exception as e:
                print(f"Error in recording loop: {e}")
                break

class TranscriptionManager:
    def __init__(self):
        self.transcription_queue = queue.Queue()
        self.processing = False
        self.last_word_end = 0
        self.chunk_number = 0
        self.prev_words = []
        self.overlap_samples = RATE * OVERLAP_SEC

    def start(self):
        """Start the transcription processing loop"""
        self.processing = True
        self.process_thread = threading.Thread(target=self._process_loop)
        self.process_thread.start()

    def stop(self):
        """Stop the transcription processing loop"""
        self.processing = False
        if hasattr(self, 'process_thread'):
            self.process_thread.join()

    def _process_loop(self):
        """Main processing loop for transcriptions"""
        while self.processing:
            try:
                # Get next chunk to process
                audio_data = self.transcription_queue.get(timeout=1)
                self.chunk_number += 1
                
                # Transcribe the chunk
                response = self._transcribe_chunk(audio_data)
                if response and hasattr(response, 'words'):
                    # Update the transcript
                    self._update_transcript(response.words)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in processing loop: {e}")

    def _transcribe_chunk(self, audio_data):
        """Transcribe a single chunk"""
        try:
            # Create a temporary WAV file in memory
            with wave.open('temp.wav', 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)  # 16-bit audio
                wf.setframerate(RATE)
                wf.writeframes(audio_data)

            # Send to OpenAI
            with open('temp.wav', 'rb') as f:
                response = client.audio.transcriptions.create(
                    model=MODEL_NAME,
                    file=f,
                    response_format="verbose_json",
                    timestamp_granularities=["word"]
                )

            # Clean up temp file
            try:
                os.remove('temp.wav')
            except:
                pass

            return response
        except Exception as e:
            print(f"Error transcribing chunk: {e}")
            return None

    def _update_transcript(self, words):
        """Update the current transcript with new words"""
        if not words:
            return

        # Get the overlap regions
        prev_overlap = [(w.word.strip().lower(), w.end) for w in self.prev_words 
                       if w.end > (self.prev_words[-1].end - OVERLAP_SEC)]
        curr_overlap = [(w.word.strip().lower(), w.start) for w in words 
                       if w.start < OVERLAP_SEC]

        # Use sequence matcher to find best overlap trim point
        prev_words_only = [w for w, _ in prev_overlap]
        curr_words_only = [w for w, _ in curr_overlap]
        sm = difflib.SequenceMatcher(None, prev_words_only, curr_words_only)
        match = sm.find_longest_match(0, len(prev_words_only), 0, len(curr_words_only))

        # Determine where to start in the current chunk
        trim_index = 0
        if match.size > 2:  # Require minimum match length
            trim_index = match.b + match.size

        # Get the new words to add
        new_words = words[trim_index:]
        
        if new_words:
            # Update the last word end time
            self.last_word_end = new_words[-1].end
            
            # Print the new words on the same line
            print(" " + " ".join(w.word.strip() for w in new_words), end="", flush=True)

        # Update previous words for next comparison
        self.prev_words = words

def main():
    # Initialize components
    recorder = AudioRecorder()
    manager = TranscriptionManager()
    
    try:
        # Start the transcription manager
        manager.start()
        
        # Start recording
        print("🎤 Recording... (Press Ctrl+C to stop)")
        recorder.start()
        
        # Main loop
        while True:
            # Get chunks from recorder and send to manager
            try:
                audio_data = recorder.chunk_queue.get(timeout=1)
                manager.transcription_queue.put(audio_data)
            except queue.Empty:
                continue
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    finally:
        # Clean up
        recorder.stop()
        manager.stop()
        print("\n✅ Recording stopped")

if __name__ == "__main__":
    main() 