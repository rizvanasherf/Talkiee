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
import tempfile
import PyPDF2
import docx
import time
import random


# -------------------------
# 1. LOGGING DECORATOR
# -------------------------
def log_time(func):
    """Decorator to log execution time of functions."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        print(f"{func.__name__} executed in {execution_time:.4f} seconds.")
        
        return result
    return wrapper

# -------------------------
# 1. CONFIGURATION
# -------------------------

load_dotenv()

@log_time
async def configure_llm():
    """Configure and validate API key for LLM.
    
    Returns:
    - str: The Open AI client 
    
    Raises:
    - ValueError: If the API key is not found in the environment variables.
    """
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise ValueError("API key not found")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1"
    )
    return client

async def call_grok(prompt, max_retries=3, timeout=10):
    """
    Asynchronous Grok API call with retries.

    Args:
    - prompt (str): The prompt.
    - max_retries (int): Maximum retries.
    - timeout (int): Timeout for the request.

    Returns:
    - str: Grok response.
    """
    client = await configure_llm()  # Use the configured OpenAI client

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
            # Use the client to call the Grok API directly (no need for headers)
            response = await asyncio.to_thread(
                client.chat.completions.create,
                **payload
            )

            if response and response.choices:
                return response.choices[0].message.content
            else:
                print(f"No content in response (Attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(2)

        except Exception as e:
            print(f"Error: {e} (Retry {attempt + 1}/{max_retries})")
            await asyncio.sleep(2)

    return "Exceeded retries. Please try again later."

# -------------------------
# 2. AUDIO INPUT & ANALYSIS
# -------------------------

@log_time
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
            recognizer.adjust_for_ambient_noise(source, duration=1) 
            
            print("Listening...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=60)

            # Save audio for analysis
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

@log_time
def analyze_audio(file_path):
    """
    Analyze the pitch and pace of the audio file.
    
    Args:
    - file_path (str): The path to the audio file.

    Returns:
    - tuple: (float, float)
        - Average pitch in Hz.
        - Pace in words per second.
    """
    y, sr = librosa.load(file_path, sr=None)

    # Pitch analysis
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    pitch_values = pitches[pitches > 0]

    avg_pitch = np.mean(pitch_values) if len(pitch_values) > 0 else 0

    # Pace estimation (words/sec)
    duration = librosa.get_duration(y=y, sr=sr)
    words = len(librosa.effects.split(y))
    pace = words / duration if duration > 0 else 0

    return avg_pitch, pace

@log_time
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

@log_time
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

@log_time
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
            # Extract text from PDF
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                text += page.extract_text() or ""

        elif file_extension == "docx":
            # Extract text from DOCX
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

@log_time
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
        return temp_file.name
    except Exception as e:
        print(f"TTS Failed")
        return None


# -------------------------
# 5. FEEDBACK GENERATION
# -------------------------

@log_time
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
@log_time
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
        f"You are a professional communication coach tasked with providing insightful feedback on vocal delivery. "
        f"Analyze the following metrics:\n"
        f"- Pitch: {pitch:.2f} Hz\n"
        f"- Pace: {pace:.2f} words/sec\n"
        f"- Filler words: {', '.join(fillers)} (Total: {filler_count})\n\n"
        f"Transcribed Text: {text}\n\n"
        f"Provide structured feedback:\n"
        f"1. **Positive Aspects**: Highlight what's working well.\n"
        f"2. **Areas for Improvement**: Identify specific aspects that could be enhanced.\n"
        f"3. **Actionable Suggestions**: Offer practical tips to improve.\n"
        f"Keep the tone encouraging, professional, and concise."
    )

    response = asyncio.run(call_grok(prompt))

    # Store the new exchange in the chat history
    chat_history.append(f"User: {text}")
    chat_history.append(f"Assistant: {response}")

    return response
@log_time
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
        f"You are a seasoned HR interview expert providing detailed feedback on a candidate's performance. "
        f"Analyze the following metrics:\n"
        f"- **Pitch**: {pitch:.2f} Hz (indicates tone quality)\n"
        f"- **Pace**: {pace:.2f} words/sec (indicates speaking speed)\n"
        f"- **Filler words**: {', '.join(fillers)} (Total: {filler_count})\n\n"
        f"🗨️ **Candidate's Answer:**\n{text}\n\n"
        f"💡 Provide structured feedback:\n"
        f"1. **Strengths:** Highlight the candidate's strong points (clarity, confidence, articulation).\n"
        f"2. **Improvement Areas:** Identify specific areas where the candidate can improve (conciseness, clarity, tone).\n"
        f"3. **Communication Tips:** Offer actionable suggestions for better responses.\n"
        f"4. **Overall Impression:** Give an overall rating or impression on their interview readiness.\n"
        f"Keep the tone professional, supportive, and clear."
    )

    response = asyncio.run(call_grok(prompt))

    # Store exchange in chat history
    chat_history.append(f"User: {text}")
    chat_history.append(f"Assistant: {response}")

    return response
@log_time
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
    f"You are a masterful storyteller and literary critic. "
    f"Your task is to evaluate the user's narrated story with a focus on **imagination, picturization, emotional impact, narrative flow, and vocabulary**. "
    f"Consider the following audio metrics:\n"
    f"- **Pitch:** {pitch:.2f} Hz (indicates tone quality)\n"
    f"- **Pace:** {pace:.2f} words/sec (indicates speaking speed)\n"
    f"- **Filler words:** {', '.join(fillers)} (Total: {filler_count})\n\n"
    f"📖 **User's Story:**\n{text}\n\n"
    f"💡 Provide detailed feedback by evaluating:\n"
    
    # 🖼️ **Picturization & Imagination**
    f"1. **Picturization & Imagination:**\n"
    f"   - Describe how vividly the story paints a picture. Are the scenes and settings well-described?\n"
    f"   - Does it evoke visual, sensory, or emotional imagery effectively?\n\n"
    
    # 📚 **Narrative Flow & Structure**
    f"2. **Narrative Flow & Structure:**\n"
    f"   - Assess the overall coherence and progression of the story.\n"
    f"   - Does the story have a clear beginning, middle, and end?\n"
    f"   - Are there smooth transitions between scenes?\n"
    f"   - Comment on the pacing: Is it engaging or does it feel rushed/dragged?\n\n"
    
    # 🎭 **Emotional Impact**
    f"3. **Emotional Impact:**\n"
    f"   - Analyze the emotional depth of the story.\n"
    f"   - Does it effectively convey feelings (e.g., suspense, joy, sadness)?\n"
    f"   - Are the characters relatable and their emotions believable?\n\n"
    
    # ✍️ **Language & Vocabulary**
    f"4. **Language & Vocabulary:**\n"
    f"   - Critique the richness and creativity of the vocabulary.\n"
    f"   - Is the language expressive and engaging?\n"
    f"   - Does it use descriptive or poetic language effectively?\n\n"
    
    # 🎙️ **Delivery & Expression**
    f"5. **Delivery & Expression:**\n"
    f"   - Comment on the voice delivery based on the pitch, pace, and filler words.\n"
    f"   - Does the narration enhance or weaken the story's impact?\n"
    f"   - Identify areas where voice modulation could improve engagement.\n\n"
    
    # 🌟 **Overall Evaluation**
    f"6. **Overall Evaluation:**\n"
    f"   - Provide a comprehensive summary of the strengths and areas for improvement.\n"
    f"   - Suggest specific tips to enhance storytelling skills (e.g., pacing, descriptive language, emotional connection).\n"
    f"   - Keep the tone **descriptive, engaging, and constructive**, offering thoughtful and insightful critique."
)

    response = asyncio.run(call_grok(prompt))

    # Store the exchange in the chat history
    chat_history.append(f"User Story: {text}")
    chat_history.append(f"LLM Feedback: {response}")

    return response
@log_time
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

    # Detect filler words
    fillers, filler_count = detect_filler_words(text)

    # Structured Prompt Sections
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
@log_time
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
    
    # Get the response
    response = asyncio.run(call_grok(hr_prompt))
    
    # Fallback in case of no response
    if not response:
        response = f"Describe a time when you faced a challenge related to {topic} and how you handled it."

    return response

@log_time
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

@log_time
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