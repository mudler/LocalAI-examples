from RealtimeSTT import AudioToTextRecorder
from openai import OpenAI
import os
import json
import pygame
import tempfile
import threading
import soundfile as sf
import numpy as np
import time

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'qwen3-0.6b')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'http://localhost:8080')
OPENAI_TTS_VOICE = os.getenv('OPENAI_TTS_VOICE', '')
OPENAI_TTS_MODEL = os.getenv('OPENAI_TTS_MODEL', 'voice-en-us-amy-low')
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'whisper-large-turbo-q5_0')
WHISPER_LANGUAGE = os.getenv('WHISPER_LANGUAGE', 'it')
SYSTEM_PROMPT = os.getenv('SYSTEM_PROMPT', 'You are a helpful assistant.')
BACKGROUND_AUDIO = os.getenv('BACKGROUND_AUDIO', 'false').lower() in ['true', '1', 'yes', 'on']
DEBUG_PLAYBACK = os.getenv('DEBUG_PLAYBACK', 'false').lower() in ['true', '1', 'yes', 'on']
WAKE_WORD = os.getenv('WAKE_WORD', '')  # Empty string means no wake word

# Initialize OpenAI client
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

# Initialize pygame mixer for audio playback
pygame.mixer.init()

# Conversation history
conversation_history = []

# Global variables for audio control
audio_playing = False
audio_thread = None

def start_callback():
    global audio_playing
    print("🎤 Recording started!")
    
    # Stop any playing audio when recording starts (only if background audio is enabled)
    if BACKGROUND_AUDIO and audio_playing:
        print("🔇 Stopping audio for recording...")
        pygame.mixer.music.stop()
        audio_playing = False

def stop_callback():
    print("⏹️ Recording stopped!")


def play_audio_background(audio_file_path):
    """Play audio in background thread"""
    global audio_playing
    
    def audio_worker():
        global audio_playing
        try:
            audio_playing = True
            pygame.mixer.music.load(audio_file_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy() and audio_playing:
                pygame.time.wait(100)
            
            # Clean up
            if os.path.exists(audio_file_path):
                os.unlink(audio_file_path)
            
            audio_playing = False
            print("✅ Background audio playback completed")
            
        except Exception as e:
            print(f"❌ Background audio error: {str(e)}")
            audio_playing = False
            # Clean up file if it exists
            if os.path.exists(audio_file_path):
                os.unlink(audio_file_path)
    
    # Start audio in background thread
    audio_thread = threading.Thread(target=audio_worker, daemon=True)
    audio_thread.start()

def play_audio_blocking(audio_file_path):
    """Play audio in foreground (blocking)"""
    global audio_playing
    try:
        audio_playing = True
        pygame.mixer.music.load(audio_file_path)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        
        # Clean up temporary file
        os.unlink(audio_file_path)
        
        audio_playing = False
        print("✅ Speech playback completed")
        
    except Exception as e:
        print(f"❌ Blocking audio error: {str(e)}")
        audio_playing = False
        # Clean up file if it exists
        if os.path.exists(audio_file_path):
            os.unlink(audio_file_path)

def clean_text_for_tts(text):
    """Clean text for TTS by removing markdown, emojis and newlines"""
    import re
    
    # Remove emojis and special characters
    # Remove emoji ranges
    text = re.sub(r'[\U0001F600-\U0001F64F]', '', text)  # Emoticons
    text = re.sub(r'[\U0001F300-\U0001F5FF]', '', text)  # Misc Symbols and Pictographs
    text = re.sub(r'[\U0001F680-\U0001F6FF]', '', text)  # Transport and Map
    text = re.sub(r'[\U0001F1E0-\U0001F1FF]', '', text)  # Regional indicator symbols
    text = re.sub(r'[\U00002600-\U000026FF]', '', text)  # Miscellaneous symbols
    text = re.sub(r'[\U00002700-\U000027BF]', '', text)  # Dingbats
    text = re.sub(r'[\U0001F900-\U0001F9FF]', '', text)  # Supplemental Symbols and Pictographs
    text = re.sub(r'[\U0001FA70-\U0001FAFF]', '', text)  # Symbols and Pictographs Extended-A
    
    # Remove other common emoji patterns
    text = re.sub(r'[🔥🚀💡🎤⏹️🔊✅❌⚠️📝🎤🗣️🌐🔑🎯👤🤖]', '', text)
    
    # Remove markdown formatting
    # Remove bold/italic
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic*
    text = re.sub(r'__(.*?)__', r'\1', text)      # __bold__
    text = re.sub(r'_(.*?)_', r'\1', text)        # _italic_
    
    # Remove code blocks
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # ```code```
    text = re.sub(r'`(.*?)`', r'\1', text)        # `code`
    
    # Remove headers
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # # Header
    
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # [text](url)
    
    # Remove newlines and extra whitespace
    text = re.sub(r'\n+', ' ', text)              # Replace newlines with space
    text = re.sub(r'\s+', ' ', text)             # Replace multiple spaces with single space
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text

def text_to_speech(text):
    """Convert text to speech using OpenAI TTS API"""
    try:
        print("🔊 Generating speech...")
        
        # Clean text for TTS
        cleaned_text = clean_text_for_tts(text)
        
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL+"/v1"
        )     
        # Call OpenAI TTS API
        response = client.audio.speech.create(
            model=OPENAI_TTS_MODEL,
            voice=OPENAI_TTS_VOICE,
            input=cleaned_text
        )
        
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name
        
        # Play audio based on configuration
        if BACKGROUND_AUDIO:
            # Play audio in background (non-blocking)
            play_audio_background(temp_file_path)
        else:
            # Play audio in foreground (blocking)
            play_audio_blocking(temp_file_path)
        
    except Exception as e:
        print(f"❌ TTS Error: {str(e)}")

def get_openai_response(user_text):
    """Get response from OpenAI API"""
    try:
        # Add user message to conversation history
        conversation_history.append({"role": "user", "content": user_text})
        
        # Prepare messages for API call
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ] + conversation_history[-10:]  # Keep last 10 messages for context
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
        )
        
        assistant_response = response.choices[0].message.content
        
        # Add assistant response to conversation history
        conversation_history.append({"role": "assistant", "content": assistant_response})
        
        return assistant_response
        
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

def validate_config():
    """Validate configuration and exit if invalid"""
    if not OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY environment variable is not set!")
        print("💡 Please set it with: export OPENAI_API_KEY='your-api-key-here'")
        exit(1)

def process_text(text):
    """Process the recorded text and get AI response"""
    if text and text.strip():
        print(f"\n👤 You: {text}")
        
        # Get AI response
        ai_response = get_openai_response(text)
        print(f"🤖 Jarvis: {ai_response}")
        
        # Convert response to speech and play
        if ai_response:
            text_to_speech(ai_response)
        
        print()  # Add spacing after response
        return ai_response
    return None

def play_wav_file(wav_file_path):
    """Play a WAV file for debugging"""
    try:
        print(f"🔊 Playing WAV file: {wav_file_path}")
        
        # Check if file exists
        if not os.path.exists(wav_file_path):
            print(f"❌ WAV file not found: {wav_file_path}")
            return False
        
        # Get file size for debugging
        file_size = os.path.getsize(wav_file_path)
        print(f"📁 File size: {file_size} bytes")
        
        # Play the audio file
        pygame.mixer.music.load(wav_file_path)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        
        print("✅ WAV file playback completed")
        return True
        
    except Exception as e:
        print(f"❌ Error playing WAV file: {str(e)}")
        return False

def save_audio_data_as_wav(audio_data, sample_rate=16000, filename="recorded.wav", play_for_debug=False):
    """Save audio data (numpy array) as a WAV file"""
    try:
        if audio_data is not None and len(audio_data) > 0:
            # Ensure audio data is in the correct format (float32, normalized)
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Save as WAV file
            sf.write(filename, audio_data, sample_rate)
            print(f"💾 Audio saved as {filename} (shape: {audio_data.shape})")
            
            # Play for debugging if requested
            if play_for_debug:
                play_wav_file(filename)
            
            return filename
        else:
            print("❌ No audio data to save")
            return None
    except Exception as e:
        print(f"❌ Error saving audio data: {str(e)}")
        return None

def save_audio_frames_as_wav(frames, sample_rate=16000, filename="recorded.wav"):
    """Save audio frames as a WAV file"""
    try:
        # Convert frames to numpy array
        if frames:
            # Join all frames into a single byte string
            audio_bytes = b''.join(frames)
            # Convert to numpy array
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            # Convert to float32 and normalize
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # Save as WAV file
            sf.write(filename, audio_float, sample_rate)
            print(f"💾 Audio saved as {filename}")
            return filename
        else:
            print("❌ No audio frames to save")
            return None
    except Exception as e:
        print(f"❌ Error saving audio: {str(e)}")
        return None

def transcribe_wav_with_openai(wav_file_path):
    """Transcribe WAV file using OpenAI Whisper API"""
    try:
        print("🎤 Transcribing with OpenAI Whisper...")
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL+"/v1"
        )    
        with open(wav_file_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model=WHISPER_MODEL,
                file=audio_file,
                language=WHISPER_LANGUAGE  # Italian language
            )
        
        return transcript.text
    except Exception as e:
        print(f"❌ OpenAI Whisper transcription error: {str(e)}")
        return None

class CustomAudioRecorder(AudioToTextRecorder):
    """Custom AudioToTextRecorder that allows access to audio data"""
    
    def get_audio_data(self):
        """Get the processed audio data as numpy array"""
        return self.audio if hasattr(self, 'audio') and self.audio is not None else None
    
    def get_audio_frames(self):
        """Get the current audio frames (before processing)"""
        return self.frames if hasattr(self, 'frames') else []
    
    def get_last_audio_frames(self):
        """Get the last recorded audio frames (before processing)"""
        return self.last_frames if hasattr(self, 'last_frames') else []
    
    def clear_frames(self):
        """Clear the audio frames and data"""
        if hasattr(self, 'frames'):
            self.frames.clear()
        if hasattr(self, 'last_frames'):
            self.last_frames.clear()
        if hasattr(self, 'audio'):
            self.audio = None

def process_audio_with_openai_whisper(recorder):
    """Process recorded audio using OpenAI Whisper API"""
    try:
        print("🔊 Processing audio with OpenAI Whisper...")
        
        # Get the processed audio data (numpy array)
        audio_data = recorder.get_audio_data()
        print(f"📊 Audio data available: {audio_data is not None}")
        
        if audio_data is not None:
            print(f"📊 Audio data shape: {audio_data.shape}, dtype: {audio_data.dtype}")
            
            # Save audio data as WAV file
            wav_filename = f"temp_audio_{int(time.time())}.wav"
            wav_path = save_audio_data_as_wav(audio_data, sample_rate=16000, filename=wav_filename, play_for_debug=DEBUG_PLAYBACK)
            
            if wav_path:
                # Transcribe using OpenAI Whisper
                transcription = transcribe_wav_with_openai(wav_path)
                
                # Clean up temporary file
                try:
                    os.unlink(wav_path)
                except:
                    pass
                
                return transcription
            else:
                return None
        else:
            print("❌ No audio data available")
            return None
            
    except Exception as e:
        print(f"❌ Error processing audio: {str(e)}")
        return None

if __name__ == '__main__':
    # Validate configuration
    validate_config()
    
    print("🚀 Jarvis Voice Assistant Started!")
    print("💡 Configuration:")
    print(f"   📝 Chat Model: {OPENAI_MODEL}")
    print(f"   🎤 TTS Model: {OPENAI_TTS_MODEL}")
    print(f"   🗣️ TTS Voice: {OPENAI_TTS_VOICE}")
    print(f"   🌐 Base URL: {OPENAI_BASE_URL}")
    print(f"   🔊 Background Audio: {'✅ Enabled' if BACKGROUND_AUDIO else '❌ Disabled'}")
    print(f"   🎵 Debug Playback: {'✅ Enabled' if DEBUG_PLAYBACK else '❌ Disabled'}")
    print(f"   🎯 Wake Word: {'✅ ' + WAKE_WORD if WAKE_WORD else '❌ Disabled'}")
    print(f"   🔑 API Key: ✅ Set")
    print("🎯 Starting voice assistant...")
    if WAKE_WORD:
        print(f"💡 Say '{WAKE_WORD}' to activate the assistant!\n")
    else:
        print("💡 Just start speaking - no wake word needed!\n")
    
    # Configure wake word based on environment variable
    wake_word_config = {}
    if WAKE_WORD:
        wake_word_config["wake_words"] = WAKE_WORD
        wake_word_config["wakeword_backend"] = "pvporcupine"  # Enable wake word backend
    else:
        wake_word_config["wakeword_backend"] = ""  # Disable wake word backend
    
    recorder = CustomAudioRecorder(on_recording_start=start_callback,
                                 model="tiny",  # Use smallest model since we're not using it for transcription
                                 on_recording_stop=stop_callback,
                                 **wake_word_config)
    
    # Start listening for voice activity
    recorder.listen()
    
    while True:
        try:
            print("🎧 Waiting for voice input...")
            
            # Use the built-in wait_audio method to handle voice activity detection
            recorder.wait_audio()
            
            print("✅ Audio recording completed, processing...")
            # Process the recorded audio with OpenAI Whisper
            recorded_text = process_audio_with_openai_whisper(recorder)
            
            if recorded_text:
                # Process the transcribed text
                process_text(recorded_text)
            else:
                print("⚠️ No audio was captured, please try again")
            
            # Clear frames for next recording
            recorder.clear_frames()
            
            # Start listening again for the next interaction
            recorder.listen()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {str(e)}")
            continue
