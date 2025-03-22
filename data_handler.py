import json
import os
import datetime
import streamlit as st

# JSON file path
HISTORY_FILE = "data/chat_history.json"

#  Ensure the data folder exists
os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)


# Save Chat History to JSON
def save_chat_history_json(user_input, spoken_text, feedback, pitch, pace):
    """
    Save chat history and metrics to a JSON file.

    Args:
        user_input (str): User's text input.
        spoken_text (str): Transcribed speech input.
        feedback (str): Feedback text.
        pitch (float): Pitch metric.
        pace (float): Pace metric.
    """

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get review score based on feedback
    review_score = convert_feedback_to_score(feedback)

    # Create a new chat entry
    chat_entry = {
        "timestamp": timestamp,
        "user_input": user_input if user_input else "",
        "spoken_text": spoken_text if spoken_text else "",
        "feedback": feedback,
        "pitch": pitch,
        "pace": pace,
        "review_score": review_score
    }

    # Load existing JSON data or create new list
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            chat_history = json.load(f)
    else:
        chat_history = []

    # Append the new entry
    chat_history.append(chat_entry)

    # Save back to the JSON file
    with open(HISTORY_FILE, "w") as f:
        json.dump(chat_history, f, indent=4)

    st.write("")



# Helper Function: Convert Feedback to Score
def convert_feedback_to_score(feedback):
    """
    Convert text feedback to a numerical score for ML processing.

    Args:
        feedback (str): User feedback text.

    Returns:
        int: Numerical score between 1 and 10.
    """
    
    # Sentiment word mapping
    positive_words = ["good", "great", "excellent", "perfect", 
                      "better", "improved", "positive", "nice"
    ]
    
    negative_words = ["bad", "poor", "worse", "difficult", 
                      "problem", "issue", "negative", "terrible"
    ]

    feedback = feedback.lower()
    score = 5  # Neutral baseline score (1-10)

    # Sentiment scoring logic
    for word in positive_words:
        if word in feedback:
            score += 1

    for word in negative_words:
        if word in feedback:
            score -= 1

    # Ensure the score is between 1 and 10
    return min(max(score, 1), 10)

def load_chat_history():
    """
    Load chat history from the JSON file.

    Returns:
        list: List of chat history entries.
    """
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            chat_history = json.load(f)
        return chat_history
    else:
        return []  

def track_progress(chat_history):
    """
    Track average review score and last pitch & pace improvement.
    
    Args:
        chat_history (list): List of chat entries.
    
    Returns:
        dict: Contains average review score, last pitch, and pace improvement.
    """
    if not chat_history:
        return {
            "average_review_score": 0,
            "last_pitch_improvement": 0,
            "last_pace_improvement": 0
        }

    # ✅ Calculate average review score
    total_sessions = len(chat_history)
    total_score = sum(entry["review_score"] for entry in chat_history)
    average_review_score = total_score / total_sessions

    # ✅ Calculate last pitch and pace improvement
    if len(chat_history) > 1:
        latest_entry = chat_history[-1]
        previous_entry = chat_history[-2]

        last_pitch_improvement = latest_entry["pitch"] - previous_entry["pitch"]
        last_pace_improvement = latest_entry["pace"] - previous_entry["pace"]
    else:
        # If only one session, no improvement comparison
        last_pitch_improvement = 0
        last_pace_improvement = 0

    return {
        "average_review_score": average_review_score,
        "last_pitch_improvement": last_pitch_improvement,
        "last_pace_improvement": last_pace_improvement
    }