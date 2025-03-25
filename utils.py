# -------------------------
# TALKIEE - AI Communication Coach
# -------------------------

import speech_recognition as sr
import librosa
import aiohttp
import asyncio
from openai import OpenAI
import numpy as np
from dotenv import load_dotenv
import os
import re
from gtts import gTTS
import functools
import tempfile
import PyPDF2
import docx
import time
import random

# -------------------------
# 1. CONFIGURATION
# -------------------------
_GLOBAL_LLM_CLIENT = None

load_dotenv()

async def configure_llm():
    """Configure and validate API key for LLM.
    
    Returns:
    - str: The Open AI client 
    
    Raises:
    - ValueError: If the API key is not found in the environment variables.
    """
    global _GLOBAL_LLM_CLIENT
    
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise ValueError("API key not found")

    _GLOBAL_LLM_CLIENT = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1"
    )
    return _GLOBAL_LLM_CLIENT

async def call_grok(prompt, max_retries=3):
    """
    Asynchronous Grok API call with retries.

    Args:
    - prompt (str): The prompt.
    - max_retries (int): Maximum retries.
    - timeout (int): Timeout for the request.

    Returns:
    - str: Grok response.
    """
    global _GLOBAL_LLM_CLIENT
    if _GLOBAL_LLM_CLIENT is None:
        try:
           await  configure_llm()
        except Exception as config_error:
            return f"Configuration Error: {config_error}"
    payload = {
        "model": "grok-2-latest",
        "messages": [
            {"role": "system", "content": "You are an AI assistant"},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 512,    
        "temperature": 0.7
    }

    for attempt in range(max_retries):
        try:
            response = await asyncio.to_thread(
                _GLOBAL_LLM_CLIENT.chat.completions.create,
                **payload
            )
            if response and response.choices:
                return response.choices[0].message.content
            else:
            
                continue

        except Exception as e:
            print(f"API Call Error (Attempt {attempt + 1}/{max_retries}): {e}")
            if hasattr(e, 'http_status') and e.http_status == 429:
                print("Rate limit exceeded. Backing off.")
                await asyncio.sleep(2 ** attempt)
                continue
            elif hasattr(e, 'type') and e.type == 'invalid_request_error':
                print("Invalid request. Check your payload.")
                break

    return "Failed to get a response after multiple attempts."

# -------------------------
# 2. AUDIO INPUT & ANALYSIS
# -------------------------

def speech_to_text():
    """
    Capture voice input from the microphone and transcribe it to text.
    
    Returns:
    - tuple: (str, str or None) 
        - The transcribed text (str).
        - The path to the saved audio file (str) .
    
    Exceptions:
    - sr.WaitTimeoutError: Raised when no speech is detected within the timeout period.
    - sr.UnknownValueError: Raised when speech cannot be understood.
    - sr.RequestError: Raised when there's an issue with the speech recognition service.
    - Exception: Captures any other unexpected errors.
    """
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        try:
            recognizer.adjust_for_ambient_noise(source, duration=0.5) 
            
            print("Listening...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=60)
            audio_file = "temp_audio.wav"
            with open(audio_file, "wb") as f:
                f.write(audio.get_wav_data())
                
            spoken_text = recognizer.recognize_google(audio)
            return spoken_text, audio_file
        
        except sr.WaitTimeoutError:
            return "Timeout: No speech detected", None
        except sr.UnknownValueError:
            return "Could not understand audio", None
        except sr.RequestError as e:
            return f"Speech recognition service error: {e}", None
        except Exception as e:
            return f"Unexpected error: {e}", None

def analyze_audio(file_path,chunk_size=10):
    """
    Analyze the pitch and pace of the audio file.
    
    Args:
    - file_path (str): The path to the audio file.

    Returns:
    - tuple: (float, float)
        - Average pitch in Hz.
        - Pace in words per second.
    """
   # Load the audio file
    y, sr = librosa.load(file_path, sr=None)
<<<<<<< HEAD
    total_duration = librosa.get_duration(y=y, sr=sr)
    
    pitches = []
    paces = []
    

    for start in range(0, int(total_duration), chunk_size):
        end = min(start + chunk_size, total_duration)
        chunk_y = y[int(start * sr):int(end * sr)]
        
        chunk_pitches, magnitudes = librosa.piptrack(y=chunk_y, sr=sr)
        pitch_values = chunk_pitches[chunk_pitches > 0]
        avg_pitch = np.mean(pitch_values) if len(pitch_values) > 0 else 0

        duration = librosa.get_duration(y=chunk_y, sr=sr)
        
        words = len(librosa.effects.split(chunk_y))  
        pace = words / duration if duration > 0 else 0
        pitches.append(avg_pitch)
        paces.append(pace)

    # Average results from all chunks
    final_pitch = float(np.mean(pitches) if len(pitches) > 0 else 0)
    final_pace =float(np.mean(paces) if len(paces) > 0 else 0)
    
    return final_pitch, final_pace
=======
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    pitch_values = pitches[pitches > 0]
    avg_pitch = np.mean(pitch_values) if len(pitch_values) > 0 else 0
    duration = librosa.get_duration(y=y, sr=sr)
    words = len(librosa.effects.split(y))
    pace = words / duration if duration > 0 else 0

    return avg_pitch, pace
>>>>>>> refactor1

@functools.lru_cache(maxsize=100)
def detect_filler_words(transcribed_text):
    """
    Identify and count filler words in transcribed text.
    
    Args:
    - transcribed_text (str): The transcribed speech or text content.

    Returns:
    - tuple: (list, int)
        - List of detected filler words.
        - Total count of filler words.
    """
    filler_patterns = re.compile(r'\b(um|uh|like|you know|so|well|actually|basically|literally|right|okay)\b', re.IGNORECASE)
    fillers = filler_patterns.findall(transcribed_text)
    
    filler_count = len(fillers)
    return fillers, filler_count


def analyze_uploaded_audio(file_path, status_callback=None,chunk_duration=30):
    """
    Analyze pitch, pace, and transcribe the uploaded audio file.
    
    Args:
    - file_path (str): Path to the uploaded audio file.
    - status_callback (function, optional): Callback function to update status messages during processing.

    Returns:
    - tuple: (str, float, float)
        - Transcribed text from the audio.
        - Average pitch in Hz.
        - Speaking pace in words per second.

    Exceptions:
    - FileNotFoundError: Raised if the file path is invalid.
    - sr.UnknownValueError: Raised if speech recognition fails to understand the audio.
    - sr.RequestError: Raised if speech recognition service is unavailable.
    - Exception: Catches unexpected errors.
    """
    if status_callback:
        status_callback("Starting transcription...")
    
    # Transcribe the audio
    recognizer = sr.Recognizer()
    full_transcription = ""

    with sr.AudioFile(file_path) as source:
        audio_length = int(librosa.get_duration(path=file_path))
        for offset in range(0, audio_length, chunk_duration):
            try:
                audio = recognizer.record(source, duration=chunk_duration)
                spoken_text = recognizer.recognize_google(audio, language="en-US")
                
                full_transcription += spoken_text + " "
                
            except sr.UnknownValueError:
                full_transcription += "[Unclear Audio] "
            except sr.RequestError as e:
                full_transcription += f"[Error: {e}] "

            if status_callback:
                status_callback(f"Processed {min(offset + chunk_duration, audio_length)} of {audio_length} seconds")
    
    if status_callback:
        status_callback("Analyzing audio characteristics...")

    # Analyze pitch and pace
    pitch, pace = analyze_audio(file_path)

    return full_transcription.strip(), pitch, pace


# -------------------------
# 3. DOCUMENT PROCESSING
# -------------------------

@functools.lru_cache(maxsize=100)
def extract_text_from_file(uploaded_file, file_extension):
    """
    Extract text from PDF or DOCX file.

    Args:
    - uploaded_file (File object): The uploaded PDF or DOCX file.
    - file_extension (str): The file extension ('pdf' or 'docx').

    Returns:
    - str: Extracted text from the file.

    Exceptions:
    - ValueError: Raised if the file extension is not supported.
    - Exception: Catches unexpected errors.
    """
    try:
        text = ""

        if file_extension == "pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                text += page.extract_text() or ""

        elif file_extension == "docx":
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"

        else:
            raise ValueError("Unsupported file format. Only PDF and DOCX are supported.")

        return text

    except ValueError as ve:
        print(f"ValueError: {ve}")
        return 

    except Exception as e:
        print(f"Unexpected error: {e}")
        return 

    
# -------------------------
# 4. AUDIO OUTPUT
# -------------------------


def text_to_speech(response):
    """
    Convert feedback text to speech and save it as an audio file.

    Args:
    - response (str): The text to be converted into speech.

    Returns:
    - str: The file path of the generated speech audio.
    """
    try:
        tts = gTTS(text=response, lang='en')
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp_file.name)
        audio_path = os.path.normpath(temp_file.name)
        return audio_path

    except Exception as e:
        print(f"TTS Failed")
        return None


# -------------------------
# 5. FEEDBACK GENERATION
# -------------------------

def get_text_feedback(text, chat_history):
    """
    Send text to Grok and get general communication feedback.

    Args:
    - text (str): The input text to analyze.
    - chat_history (list): The conversation history for context.

    Returns:
    - str: Feedback on tone, clarity, grammar, and delivery.
    """
    if not text:
        return "No valid input detected."

    history = "\n".join(chat_history)
    prompt = (
        f"You are a professional communication improvement coach. Your role is to assist users "
        f"in enhancing their verbal and written communication skills. Provide feedback on tone, clarity, grammar, "
        f"and delivery.\n\n"
        f"Conversation History:\n{history}\n"
        f"User: {text}\nAssistant:"
    )

    response = asyncio.run(call_grok(prompt))

    if response:
        # Append to chat history
        chat_history.append(f"User: {text}")
        chat_history.append(f"Assistant: {response}")
        
        return response
    else:
        return "Failed to get a response from Talkiee."
    
def get_voice_feedback(text, pitch, pace, chat_history):
    """
    Send text and audio metrics to Grok and get vocal delivery feedback.

    Args:
    - text (str): The transcribed speech text.
    - pitch (float): The average pitch of the speech in Hz.
    - pace (float): The speaking pace in words per second.
    - chat_history (list): List of conversation history.

    Returns:
    - str: Feedback on vocal delivery, including strengths, improvement areas, and tips.
    """
    if not text:
        return "No valid input detected."

    fillers, filler_count = detect_filler_words(text)
    
    prompt = (
        f"Vocal Delivery Analysis:\n"
        f"- Pitch: {pitch:.2f} Hz\n"
        f"- Pace: {pace:.2f} words/sec\n"
        f"- Filler words: {', '.join(fillers)}\n\n"
        f"Text Analyzed: {text}\n\n"
        f"Feedback:\n"
        f"1. Strengths: What works well\n"
        f"2. Improvement Areas: Key communication gaps\n"
        f"3. Practical Tips: Actionable advice\n"
        "Tone: Encouraging, direct, constructive."
    )

    response = asyncio.run(call_grok(prompt))

    chat_history.append(f"User: {text}")
    chat_history.append(f"Assistant: {response}")

    return response

def get_interview_feedback(text, pitch, pace, chat_history):
    """
    Send interview response and audio metrics to Grok for HR interview feedback.

    Args:
    - text (str): The candidate's transcribed response.
    - pitch (float): The average pitch of the response in Hz (indicates tone quality).
    - pace (float): The speaking pace in words per second.
    - chat_history (list): List storing the conversation history.

    Returns:
    - str: Detailed HR interview feedback, including strengths, improvement areas, and tips.
    - str: Error message if no input is detected or the API fails.

    """
    if not text:
        return "No valid input detected."

    fillers, filler_count = detect_filler_words(text)

    prompt = (
        f"As an HR interview expert, analyze candidate performance:\n"
        f"- Pitch: {pitch:.2f} Hz\n"
        f"- Pace: {pace:.2f} words/sec\n"
        f"- Filler words: {', '.join(fillers)}\n\n"
        f"Evaluate:\n"
        f"1. Strengths: Key communication positives\n"
        f"2. Improvement Areas: Specific communication gaps\n"
        f"3. Actionable Advice: Practical communication tips\n"
        f"4. Interview Readiness: Overall potential"
    )

    response = asyncio.run(call_grok(prompt))

    # Store exchange in chat history
    chat_history.append(f"User: {text}")
    chat_history.append(f"Assistant: {response}")

    return response

def get_storytelling_feedback(text, pitch, pace, chat_history):
    """
    Send story narration and audio metrics to Grok for storytelling feedback.

    Args:
    - text (str): The user's narrated story.
    - pitch (float): The average pitch of the audio in Hz (indicates tone quality).
    - pace (float): The speaking pace in words per second.
    - chat_history (list): List storing the conversation history.

    Returns:
    - str: Detailed storytelling feedback, including picturization, narrative flow, emotional impact, and language critique.
    """
    if not text:
        return "No valid input detected."

    fillers, filler_count = detect_filler_words(text)

    prompt = (
        f"Analyze the storytelling voice based on audio metrics:\n"
        f"- Pitch: {pitch:.2f} Hz\n"
        f"- Pace: {pace:.2f} words/sec\n"
        f"- Filler words: {', '.join(fillers)}\n\n"
        "Evaluate:\n"
        "1. Voice Dynamics\n"
        "2. Emotional Engagement\n"
        "3. Narrative Rhythm\n"
        "4. Storytelling Effectiveness\n\n"
        "Provide brief, constructive feedback on storytelling performance."
    )

    response = asyncio.run(call_grok(prompt))

    chat_history.append(f"User Story: {text}")
    chat_history.append(f"LLM Feedback: {response}")

    return response

def get_presentation_feedback(text, pitch, pace):
    """
    Analyze presentation delivery and provide feedback with Grok.

    Args:
    - text (str): The transcribed content of the user's presentation.
    - pitch (float): The average pitch of the audio in Hz (tone quality).
    - pace (float): The speaking pace in words per second.

    Returns:
    - str: Detailed feedback on the presentation covering clarity, structure, delivery, and professionalism.

    """
    if not text:
        return "No valid input detected."

    fillers, filler_count = detect_filler_words(text)


    audio_metrics = (
        f"- **Pitch:** {pitch:.2f} Hz (tone quality)\n"
        f"- **Pace:** {pace:.2f} words/sec (speaking speed)\n"
        f"- **Filler words:** {', '.join(fillers)} (Total: {filler_count})"
    )

    user_presentation = f"📊 **User's Presentation Content:**\n{text}"

    prompt = (
       f"🔎 **Audio Metrics:**\n{audio_metrics}\n\n"
        f"{user_presentation}\n\n"
        f"💡 Evaluate the presentation focusing on:\n"
        f"- Clarity & structure\n"
        f"- Content relevance\n"
        f"- Delivery & tone\n"
        f"- Pace & timing\n"
        f"- Language & vocabulary\n"
        f"- Overall presentation skills\n"
        f"📌 Provide actionable feedback with specific improvement suggestions."
    )

    response = asyncio.run(call_grok(prompt))
    return response

# -------------------------
# 6. CONTENT GENERATION
# -------------------------

def get_hr_question():
    """
    Get a unique HR interview question from Grok.

    Description:
    - This function generates a realistic HR interview question with added randomization.
    - It sends a dynamic and varied prompt to Grok to ensure unique questions each time.
    
    Args:
    - None

    Returns:
    - str: A unique HR interview question.
    """
    question_types = [
        "behavioral", 
        "situational", 
        "cultural fit", 
        "strengths and weaknesses", 
        "conflict resolution", 
        "communication skills", 
        "team collaboration"
    ]
    
    topic = random.choice(question_types)

    hr_prompt = (
        f"You are an HR interview coach. Generate a realistic and unique {topic} HR interview question. "
        "Ensure the question is clear, concise, and avoids technical or domain-specific content. "
        "Each time, the question should be distinct and creative."
    )
 
    response = asyncio.run(call_grok(hr_prompt))
    
    if not response:
        response = f"Describe a time when you faced a challenge related to {topic} and how you handled it."

    return response

def generate_passage():
    """
    Generate a short passage using LLM for summarization exercises.

    Description:
    - This function generates a short, insightful passage consisting of three sentences. 
    - The sentences highlight different professional skills such as communication, leadership, 
      time management, adaptability, collaboration, or problem-solving. 
    - The content is concise, meaningful, and workplace-relevant.

    Args:
    - None

    Returns:
    - str: The generated passage or a fallback passage in case of API failure.
    """
    subjects = [
        "communication, collaboration, and empathy",
        "leadership, decision-making, and conflict resolution",
        "time management, productivity, and goal setting",
        "adaptability, resilience, and creativity",
        "problem-solving, critical thinking, and innovation",
        "teamwork, collaboration, and motivation",
        "personal growth, discipline, and self-awareness",
        "influence, negotiation, and persuasion",
        "public speaking, confidence, and presence"
    ]

   
    random_subject = random.choice(subjects)
    
    passage_prompt = (
        f"Generate three unique and insightful sentences about {random_subject}. "
        "Ensure each sentence highlights a different aspect of the topic and its impact "
        "in a workplace or personal growth context. Keep the sentences clear, concise, and meaningful."
    )
    
    try:
        response = asyncio.run(call_grok(passage_prompt))


        if response:
            if isinstance(response, list) and len(response) > 0:
                passage = response[0]
            elif isinstance(response, dict) and "content" in response:
                passage = response["content"]
            elif isinstance(response, str) and len(response.strip()) > 0:
                passage = response
            else:
                passage = "No valid passage generated."
        else:
            passage = "No valid passage generated."
            
        if passage and passage != "No valid passage generated.":
            return passage
        else:
            return (
                "Effective communication is key to building trust and empathy. "
                "Listening actively helps understand others' perspectives. "
                "Clear communication promotes teamwork and collaboration."
            )

    except Exception as e:
        print(f"Error generating passage: {e}")
        return f"Error generating passage: {str(e)}"

def get_summary_feedback(passage, user_summary):
    """
    Get feedback on the user's summary compared to the original passage.

    Description:
    - This function generates detailed feedback on a user's summary of a given passage.
    - It evaluates the summary based on **accuracy, coherence, and conciseness**.
    - The feedback highlights strengths and provides areas for improvement.

    Args:
    - passage (str): The original passage to be summarized.
    - user_summary (str): The user's summarized version of the passage.

    Returns:
    - str: Feedback on the summary if successful.
    """
    
    feedback_prompt = (
        f"Provide detailed feedback on the following summary in terms of accuracy, coherence, and conciseness. "
        f"Original Passage: {passage}\n"
        f"User Summary: {user_summary}\n"
        "Highlight strengths and areas for improvement. Be detailed and constructive."
    )
    
    try:
        feedback_response = asyncio.run(call_grok(feedback_prompt))

        if feedback_response:
            return feedback_response
        else:
            return "Couldn't generate feedback. Please try again."

    except Exception as e:
        return f"Error generating feedback"