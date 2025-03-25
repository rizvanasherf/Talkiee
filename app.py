import streamlit as st
import os
import time
from data_handler import save_chat_history_json, load_chat_history, track_progress
from utils import (
    speech_to_text,
    analyze_audio,
    get_text_feedback,
    get_voice_feedback,
    text_to_speech,
    get_hr_question,
    get_interview_feedback,
    get_storytelling_feedback,
    generate_passage,
    get_summary_feedback,
    extract_text_from_file,
    analyze_uploaded_audio,
    get_presentation_feedback,
)


def lottie_spinner():
    """Display a Lottie animation as a spinner."""
    lottie_file_path = "lodingtry.json"
    with open(lottie_file_path, "r") as f:
        lottie_json = f.read()

    st.components.v1.html(
        f"""
        <div id="lottie-container" style="width: 200px; height: 50px; text-align: left; margin: auto;"></div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.9.1/lottie.min.js"></script>
        <script>
            var animation = lottie.loadAnimation({{
                container: document.getElementById("lottie-container"),
                renderer: "svg",
                loop: true,
                autoplay: true,
                animationData: {lottie_json}
            }});
            animation.setSpeed(0.2);
        </script>
        """,
        height=200,
    )


def main():
    """Main function to run the Streamlit application."""
    st.set_page_config(
        page_title="TALKIEE.AI",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    st.markdown(
        """
        <style>
            .main-title {
                text-align: center;
                font-size: 48px;
                font-weight: bold;
                background: linear-gradient(90deg, #6a11cb, #2575fc);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-family: 'Segoe UI', sans-serif;
                margin: 0;
                line-height: 1.2;
            }
            .app-container {
                max-width: 400px;
                margin: 0 auto;
                padding: 20px;
                background-color: #1e1e1e;
                border-radius: 15px;
                box-shadow: 0 10px 20px rgba(0,0,0,0.3);
                margin-top: 50px;
                margin-bottom: 50px;
            }
            .highlight {
                color: #ffcc00;
                font-weight: bold;
            }
            .stTabs [aria-selected="true"] {
                color: #3d6aff !important;
                box-shadow: 0 0 10px rgba(61, 106, 255, 0.5);
            }
            .stTabs [data-baseweb="tab"] {
                flex: 1;
                text-align: center;
                font-size: 16px;
                font-weight: bold;
                justify-content: center;
                color: silver;
                border-bottom: 2px solid transparent;  /* Subtle border effect */
                transition: all 0.3s ease-in-out;
            }
            .stButton > button {
                position: relative;
                padding: 10px 20px;
                border-radius: 7px;
                border: 1px solid rgb(61, 106, 255);
                font-size: 14px;
                text-transform: uppercase;
                font-weight: 600;
                letter-spacing: 2px;
                background: transparent;
                color: #fff;
                overflow: hidden;
                box-shadow: 0 0 0 0 transparent;
                transition: all 0.2s ease-in;
            }
            .stButton > button:hover {
                background: rgb(61, 106, 255);
                color: #fff;
                border: 1px solid rgb(61, 106, 255);
                box-shadow: 0 0 12px rgba(61, 106, 255, 0.8);
                transform: translateY(-2px);
            }
            .stButton > button:active,
            .stButton > button:focus {
                background: rgb(61, 106, 255);
                color: #fff;
                border: 1px solid rgb(61, 106, 255);
                outline: none;
                box-shadow: 0 0 10px rgba(61, 106, 255, 0.8);
            }
            .metric-box {
                    color: white;
                    padding: 15px;
                    border-radius: 10px;
                    text-align: center;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    margin-bottom: 10px;
                }
            .metric-label {
                    font-size: 14px;
                    font-weight: bold;
                    color: #3d6aff;
                }
            .metric-value {
                    font-size: 24px;
                    font-weight: bold;
                    color: #ffffff;
                }
            .stTextArea {
                color: #333;
                padding: 10px;
                font-size: 16px;
            }
            .stMarkdown {
                font-size: 18px;
            }
            .intro-paragraph {
                font-family: 'Segoe UI', sans-serif;
                font-size: 20px;
                color: silver;
                line-height: 2;
                text-align: justify;
                margin-bottom: 30px;
                padding-left: 50px;
                padding-right: 50px;
            }
            .second_heading {
                text-align: center;
                font-size: 20px;
                color: silver;
                margin-bottom: 20px;
                padding: 20px 0;
                font-family: 'Segoe UI', sans-serif;
            }
            .third_heading{
                text-align: center;
                font-size: 25px;
                font-weight: bold;
                color: silver;
                margin-bottom: 20px;
                padding: 20px 0;
                font-family: 'Orbitron', sans-serif;
            }
            .chat-message {
                padding: 1.5rem;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
                display: flex;
                flex-direction: column;
                max-width: 90%;
                word-wrap: break-word;
                overflow-wrap: break-word;
                line-height: 1.6;
            }
            .user-message, .assistant-message {
                max-height: 300px;
                overflow-y: auto;
                white-space: pre-wrap;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            }
            .user-message {
                background-color: #202124;
                border-left: 5px solid #2575fc;
                margin-left: 20%;
                margin-right: 2%;
            }
            .assistant-message {
                background-color: #202124;
                border-left: 5px solid #6a11cb;
                margin-left: 2%;
                margin-right: 20%;
            }
            .message-content {
                display: flex;
                flex-direction: column;
                gap: 10px;
                font-size: 16px;
                color: #e0e0e0;
                line-height: 1.8;
            }
            .message-header {
                font-weight: bold;
                margin-bottom: 0.5rem;
            }
            .message-time {
                color: #888;
                font-size: 0.8rem;
                margin-left: auto;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    if "current_tab" not in st.session_state:
        st.session_state["current_tab"] = "Home"
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Home", "Talkee.Ai", "Interview", "Narration", "Listening", "presentation"]
    )

    with tab1:
        st.session_state["current_tab"] = "Home"
        home_page_render()
    with tab2:
        st.session_state["current_tab"] = "Talkee.Ai"
        render_main_section()
    with tab3:
        st.session_state["current_tab"] = "Interview"
        render_interview_section()
    with tab4:
        st.session_state["current_tab"] = "Narration"
        storytelling_with_feedback()
    with tab5:
        st.session_state["current_tab"] = "Listening"
        render_listening_section()
    with tab6:
        st.session_state["current_tab"] = "Presentation"
        render_presentation_section()


def home_page_render():
    """
    Render the home page content for the TALKIEE.AI application.

    - The application title and header.
    - A brief description of the app's purpose and functionality.
    - Information about real-time voice analysis features.
    - Details on HR interview simulations and listening exercises.
    - Emphasis on personalized feedback to improve communication skills.

    """
    st.markdown(
        """
        <div class="app-container">
            <div class="app-header">
                <h1 class="main-title">TALKIEE.AI</h1>
                <div class="new-chat-button">
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="intro-paragraph">
            <strong>TALKIEE.AI</strong> is an innovative verbal communication coach designed to help individuals enhance their
            speaking skills through immersive, real-time feedback. Whether you're preparing for
            job interviews, refining your presentation delivery, or practicing
            storytelling, TALKIEE.AI provides an interactive platform for self-improvement.
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <div class="intro-paragraph">
            With real-time voice analysis, the app evaluates your pitch, pace, and fluency,
            offering actionable insights to enhance your speech clarity and confidence.
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <div class="intro-paragraph">
            The HR interview simulations enable you to practice with realistic voice-based assessments,
            while the narration and listening exercises help sharpen your comprehension and delivery.
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <div class="intro-paragraph">
            By providing personalized feedback and voice synthesis, TALKIEE.AI empowers you to communicate with
            precision, confidence, and impact.
        </div>
        """,
        unsafe_allow_html=True
    )


def render_main_section():
    """
    Render the main TALKIEE.AI section with chat functionality and voice interaction.
    
    - **App Title and Header:** Displays the app name in a styled format.
    - **Chat History and Progress Tracking:**
        - Loads and displays previous chat history.
        - Tracks and displays the user's average review score.
    - **User Interaction Options:**
        - **Text Input:** Allows the user to type a message.
        - **Voice Input:** Enables real-time speech-to-text with feedback on pitch and pace.
    - **Voice Analysis and Feedback:**
        - Provides audio feedback with pitch and pace evaluation.
        - Generates audio responses using text-to-speech.
    - **History Display:** 
        - Renders past user and assistant messages in a chat format.

    The function handles real-time feedback, audio synthesis, and chat history persistence.
    """
    
    if "current_tab" not in st.session_state:
        st.session_state["current_tab"] = "Main"

    if st.session_state["current_tab"] != "Main":
        st.session_state["chat_history"] = []    
        st.session_state["current_tab"] = "Main" 
        
    st.markdown(
        """
        <h1 class="main-title">TALKIEE.AI</h1>
        """,
        unsafe_allow_html=True
    )

    chat_history = load_chat_history()
    progress = track_progress(chat_history)

    review_score = progress["average_review_score"]
    imporvement_rate = progress["improvement_score"]
    latest_point = progress["latest_point"]
    percentage_score = (review_score / 10) * 100

    # Layout with columns
    one, two = st.columns([6, 1])

    with two:
        with st.sidebar:
            st.markdown(
                """
                <div class="third_heading">
                    Pace Tracker
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown(
                f"""
                <div class="metric-box" title="Average communication score based on recent sessions.">
                    <div class="metric-label"> AceScore </div>
                    <div class="metric-value">{percentage_score:.1f}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown(
                f"""
                <div class="metric-box"  title="Rate of improvement compared to previous avg scores.">
                    <div class="metric-label"> BoostFactor</div>
                    <div class="metric-value">{imporvement_rate:.1f}%</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown(
                f"""
                <div class="metric-box" title="The score from your most recent session.">
                    <div class="metric-label">LastStrike</div>
                    <div class="metric-value">{latest_point} pts</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
    st.markdown(
        """
        <div style="text-align: center; font-size: 20px; color:silver;  margin: 20px 0;">
            Talkiee.ai is designed to help you track and improve your communication skills, whether through writing or speaking.
            With Talkiee.ai, you can send messages and record your voice to receive feedback and enhance your abilities.
        </div>
        """,
        unsafe_allow_html=True
    )

    user_input = st.text_area("sent you message", placeholder="enter your message",label_visibility="hidden")

    col1, col2 = st.columns([6, 1])
    with col1:
        if st.button("Record"):
            with st.empty():
                lottie_spinner()
                spoken_text, audio_file = speech_to_text()

                if spoken_text and audio_file:
                    pitch, pace = analyze_audio(audio_file)
                    st.write(spoken_text)
                    feedback = get_voice_feedback(spoken_text, pitch, pace)
                    audio_file = text_to_speech(feedback)
                    st.audio(audio_file, format="audio/mp3")
                    os.remove(audio_file)
                    save_chat_history_json(user_input, spoken_text, feedback, pitch, pace)
                else:
                    st.write("")

    with col2:
        if st.button("Send"):
            if user_input:
                feedback = get_text_feedback(user_input, st.session_state["chat_history"])
                audio_file = text_to_speech(feedback)
                st.audio(audio_file, format="audio/mp3")
                if audio_file and os.path.exists(audio_file):
                    os.remove(audio_file)
                save_chat_history_json(user_input, "", feedback, pitch=0, pace=0)
            else:
                st.write("")

    for i in range(0, len(st.session_state["chat_history"]), 2):
        if i < len(st.session_state["chat_history"]):
            user_msg = st.session_state["chat_history"][i].replace("User: ", "")
            st.markdown(
                f"""
                <div class="chat-message user-message">
                    <div class="message-header">You</div>
                    <div class="message-content">{user_msg}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        if i + 1 < len(st.session_state["chat_history"]):
            assistant_msg = st.session_state["chat_history"][i + 1].replace("Assistant: ", "")
            st.markdown(
                f"""
                <div class="chat-message assistant-message">
                    <div class="message-header">Assistant</div>
                    <div class="message-content">{assistant_msg}</div>
                </div>
                """,
                unsafe_allow_html=True
            )


def render_interview_section():
    """
    Render the HR Interview section with voice-based questions and real-time feedback.

    - **Session State Initialization:**
        - Ensures the `chat_history` and `current_question` states are initialized.
    - **HR Question Display:**
        - Displays a randomly generated HR interview question from the `get_hr_question()` function.
        - Uses text-to-speech (TTS) to play the question audio.
    - **User Interaction:**
        - **Record Answer:** Allows the user to record their answer via speech.
        - **Speech Analysis:** Analyzes the spoken audio for pitch, pace, and fluency.
        - **Feedback Generation:** 
            - Provides textual feedback on the user's answer with actionable insights.
            - Plays the feedback audio using TTS.
        - **Next Button:** Loads a new HR question for the next round.
    - **Chat Display:** 
        - Renders both the user's answer and the assistant's feedback in a styled chat format.

    The function handles voice synthesis, audio analysis, and chat history persistence.
    """
    if "current_tab" not in st.session_state:
        st.session_state["current_tab"] = "Interview"
        
    if st.session_state["current_tab"] != "Interview":
        st.session_state["chat_history"] = []
        st.session_state["current_question"] = get_hr_question()
        st.session_state["current_tab"] = "Interview"
        
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    if "current_question" not in st.session_state:
        st.session_state["current_question"] = get_hr_question()

    st.markdown("<h1 class='main-title'>HR Interview Session</h1>", unsafe_allow_html=True)

    hr_question = st.session_state["current_question"]
    st.markdown(
        f"""
        <div class="chat-message assistant-message">
            <div class="message-header">Interviewer</div>
            <div class="message-content">{hr_question}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    question_audio = text_to_speech(hr_question)
    st.audio(question_audio, format="audio/mp3")
    if question_audio:
        os.remove(question_audio)

    col1, col2, col3 = st.columns([4, 4, 2])
    with col1:
        if st.button("Record Answer"):
            with st.empty():
                lottie_spinner()
                spoken_text, audio_file = speech_to_text()

                if spoken_text and audio_file:
                    pitch, pace = analyze_audio(audio_file)
                    st.markdown(
                        f"""
                        <div class="chat-message user-message">
                            <div class="message-header">You</div>
                            <div class="message-content">{spoken_text}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    feedback = get_interview_feedback(spoken_text, pitch, pace, st.session_state["chat_history"])
                    st.markdown("<h2>✅ Feedback Result:</h2>", unsafe_allow_html=True)
                    st.markdown(
                        f"""
                        <div class="chat-message assistant-message">
                            <div class="message-header">Feedback</div>
                            <div class="message-content">{feedback}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    feedback_audio = text_to_speech(feedback)
                    st.audio(feedback_audio, format="audio/mp3")
                    os.remove(feedback_audio)
                else:
                    st.write("recoginzation failed")

    with col3:
        if st.button("Next"):
            st.session_state["current_question"] = get_hr_question()


def storytelling_with_feedback():
    """
    Render the storytelling section with voice recording and real-time feedback.

    - **Introduction and Instructions:**
        - Displays a heading and descriptive text explaining the purpose of the storytelling task.
        - Provides guidance on enhancing creative and communication skills through short narratives.
    - **User Interaction:**
        - **Start Recording:** Enables users to record their story through speech input.
        - **Speech Analysis:** 
            - Analyzes the spoken audio for pitch and pace.
            - Displays the transcribed story.
        - **Feedback Generation:** 
            - Provides detailed feedback on the user's storytelling performance.
            - Includes insights on flow, vocabulary, and emotional impact.
        - **Audio Playback:** 
            - Generates text-to-speech (TTS) audio feedback.
            - Plays the feedback and deletes the temporary audio file.
    - **Chat Display:** 
        - Renders both the user's story and the assistant's feedback in a styled chat format.

    The function handles voice synthesis, audio analysis, and feedback presentation.
    """

    if "current_tab" not in st.session_state:
        st.session_state["current_tab"] = "Storytelling"
    elif st.session_state["current_tab"] != "Storytelling":
        st.session_state["story_feedback"] = ""
        st.session_state["current_tab"] = "Storytelling"
        
    st.markdown(
        """
        <div class='main-title'>
            Tell Your Story
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <div class="second_heading">
            The Storytelling Task in this app is designed to help you refine your creative and communication skills
            by crafting short narratives. Whether you're a writer, presenter, or someone looking to enhance your expressive
            abilities, this task offers a structured way to practice and improve.
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <div class="second_heading">
            In this task, you will narrate a short story to practice and enhance your storytelling abilities.
            The goal is to focus on flow, vocabulary, and emotional impact. After sharing your story, you will
            receive detailed feedback.let start....
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 4, 1])
    with col3:
        if st.button("Start Recording"):
            with st.empty():
                lottie_spinner()
                spoken_text, audio_file = speech_to_text()

                if spoken_text and audio_file:
                    pitch, pace = analyze_audio(audio_file)
                    with col2:
                        st.markdown(
                            f"""
                            <div class="chat-message user-message">
                                <div class="message-header">You</div>
                                <div class="message-content">{spoken_text}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        feedback = get_storytelling_feedback(spoken_text, pitch, pace, st.session_state["chat_history"])
                        st.markdown("<h2>✅ Feedback Result:</h2>", unsafe_allow_html=True)
                        st.markdown(
                            f"""
                            <div class="chat-message assistant-message">
                                <div class="message-header">Feedback</div>
                                <div class="message-content">{feedback}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        feedback_audio = text_to_speech(feedback)
                        st.audio(feedback_audio, format="audio/mp3")
                        os.remove(feedback_audio)
                else:
                    st.write("")


def render_listening_section():
    """
    Render the Active Listening and Paraphrasing section with passage playback and feedback.

    - **Passage Generation and Playback:**
        - Generates a random passage using `generate_passage()`.
        - Converts the passage to speech using text-to-speech (TTS).
        - Plays the audio passage for the user to listen.
    - **User Interaction:**
        - **Text Area Input:** Allows the user to type their paraphrased summary.
        - **Feedback Generation:**
            - Compares the user's summary against the original passage.
            - Provides detailed feedback on accuracy, comprehension, and expression.
            - Generates TTS audio feedback and plays it.
    - **Error Handling:**
        - Displays a message prompting the user to enter a summary before requesting feedback.
    - **Temporary Audio File Management:**
        - Removes the temporary audio files after playback to avoid clutter.

    The function handles text-to-speech synthesis, audio playback, feedback generation, 
    and user interaction.
    """
    if "current_tab" not in st.session_state:
        st.session_state["current_tab"] = "Listening"
    elif st.session_state["current_tab"] != "Listening":
        st.session_state["current_tab"] = "Listening"
        
    st.markdown("<h1 class='main-title'>Active Listening & Paraphrasing</h1>", unsafe_allow_html=True)

    passage = generate_passage()
    audio_file = text_to_speech(passage)
    st.audio(audio_file, format="audio/mp3")
    time.sleep(1)
    if audio_file:
        os.remove(audio_file)

    st.markdown(
        """
        <div style="text-align: center; font-size: 20px; color:silver; font-weight: bold; margin: 20px 0;">
            Listen carefully and paraphrase the passage in your own words.
        </div>
        """,
        unsafe_allow_html=True
    )

    user_summary = st.text_area("your summary", placeholder="Type your summary here...",label_visibility="hidden")
    col1, col2, col3 = st.columns([1, 4, 1])

    with col3:
        if st.button("Get Feedback"):
            if user_summary.strip():
                feedback = get_summary_feedback(passage, user_summary)
                with col2:
                    st.markdown("<h2>Feedback:</h2>", unsafe_allow_html=True)
                    st.markdown(
                        f"""
                        <div class="chat-message assistant-message">
                            <div class="message-header">Feedback</div>
                            <div class="message-content">{feedback}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    feedback_audio = text_to_speech(feedback)
                    st.audio(feedback_audio, format="audio/mp3")
                    os.remove(feedback_audio)
            else:
                st.write("Please enter a summary before requesting feedback.")


def render_presentation_section():
    """
    Render the Presentation Assessment section with file upload and feedback.

    - **Introduction and Instructions:**
        - Displays a heading and descriptive text explaining the purpose of the presentation assessment.
        - Provides guidance on improving voice delivery and content quality.
    - **File Upload:**
        - Allows users to upload PDF, DOCX, MP3, or WAV files.
        - Supports both text-based and audio-based presentations.
    - **Text File Handling:**
        - Extracts and displays content from PDF or DOCX files.
        - Generates detailed feedback on the presentation content.
        - Provides text-to-speech (TTS) audio feedback.
    - **Audio File Handling:**
        - Saves the uploaded audio file temporarily.
        - Transcribes the audio into text.
        - Analyzes the audio for pitch and pace.
        - Generates detailed feedback on the voice presentation.
        - Provides TTS audio feedback.
    - **Temporary File Management:**
        - Removes temporary audio and feedback files after processing.
    - **Error Handling:**
        - Displays messages for unsupported file formats or empty content.

    The function handles text and audio processing, TTS synthesis, and real-time feedback generation.
    """
    if "current_tab" not in st.session_state:
        st.session_state["current_tab"] = "Presentation"
    elif st.session_state["current_tab"] != "Presentation":
        st.session_state["current_tab"] = "Presentation"

    st.markdown("<h1 class='main-title'>Presentation Assessment</h1>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="second_heading">
            The Presentation Analyzeris designed to help you refine your presentation skills
            by providing comprehensive feedback on both your voice delivery and content quality.
            Whether you're preparing for business presentations, academic speeches, or public speaking,
            the Presentation Analyzer offers personalized feedback to help you communicate with precision,
            confidence, and impact.
        </div>
        """,
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader("Upload PDF, DOCX, or Audio (flac/WAV)", type=["pdf", "docx", "mp3", "wav","flac", "aiff", "m4a"])

    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1].lower()

        if file_extension in ["pdf", "docx"]:
            presentation_text = extract_text_from_file(uploaded_file, file_extension)
            if presentation_text:
                # st.markdown("<h2>Uploaded Presentation Content:</h2>", unsafe_allow_html=True)
                # st.write(presentation_text)
                feedback = get_presentation_feedback(presentation_text, pitch=0, pace=0)
                st.markdown("<h2>✅ Presentation Feedback:</h2>", unsafe_allow_html=True)
                st.markdown(
                    f"""
                    <div class="chat-message assistant-message">
                        <div class="message-header">Feedback</div>
                        <div class="message-content">{feedback}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                feedback_audio = text_to_speech(feedback)
                st.audio(feedback_audio, format="audio/mp3")
                os.remove(feedback_audio)

        elif file_extension in [ "wav", "flac", "aiff"]:
            audio_path = f"temp_audio.{file_extension}"
            with open(audio_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            try:
                spoken_text, pitch, pace = analyze_uploaded_audio(audio_path)
                if spoken_text:
                    st.markdown("<h2>Transcribed Presentation:</h2>", unsafe_allow_html=True)
                    st.write(spoken_text)
                    feedback = get_presentation_feedback(spoken_text, pitch, pace)
                    st.markdown("<h2>✅ Presentation Feedback:</h2>", unsafe_allow_html=True)
                    st.markdown(
                        f"""
                        <div class="chat-message assistant-message">
                            <div class="message-header">Feedback</div>
                            <div class="message-content">{feedback}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    feedback_audio = text_to_speech(feedback)
                    st.audio(feedback_audio, format="audio/mp3")
                    os.remove(feedback_audio)
                os.remove(audio_path)
            except ValueError as e:
                st.error(f"Error processing audio: {e}")
            
        else:
            st.error(
            f"Unsupported audio format: `{file_extension}`. Please upload mp3, WAV, FLAC, or AIFF audio files."
            )

if __name__ == "__main__":
    main()