# 📢 TALKEE.AI Communication Assistant

A comprehensive AI-powered platform to enhance your communication skills through real-time feedback and analysis.

## 🚀 Features

### 1. TALKEE.AI (Chat & Voice Practice)
- Engage in **text and voice conversations** powered by **xAI**
- Receive **real-time feedback** on grammar, tone, clarity, and delivery
- Supports **speech-to-text (STT)** and **text-to-speech (TTS)** conversion

### 2. Interview Practice
- AI-generated **HR interview questions** based on real-world scenarios
- Record your responses and receive **detailed feedback** on:
  - **Pitch** (tone quality)
  - **Pace** (speaking speed)
  - **Filler words** and **fluency**
- Ideal for **job interview preparation**

### 3. Storytelling Arena
- Record a story and the app analyzes your **narration skills**
- Feedback includes:
  - **Emotional impact**
  - **Storytelling flow**
  - **Clarity and articulation**

### 4. Listening Area
- Listen to **AI-generated audio** clips
- Practice **narrating back** the content
- Get feedback on:
  - **Pronunciation accuracy**
  - **Retention** and **recall**

### 5. Presentation Review
- Upload **PDF, DOC, or MP4** files
- AI extracts content and provides feedback on:
  - **Structure and clarity**
  - **Grammar and language**
  - **Tone and effectiveness**

## 🛠️ Tech Stack

### Backend
- **xAI (Grok)** → AI-powered feedback generation
- **OpenAI** → LLM API connection
- **PyPDF2** → Extract text from PDF files
- **docx** → Extract text from DOC files
- **Librosa** → Analyze audio pitch and pace
- **SpeechRecognition** → Speech-to-text recording
- **gTTS (Google Text-to-Speech)** → Convert text to speech

### Frontend
- **Streamlit** → Web app framework
- **Custom CSS** → For improved styling and UI/UX
- **Lottie Animations** → For dynamic visuals

## 📋 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/rizvanasherf/Talkiee
```

### 2. Setup Environment
```bash
cd Talkiee
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure API Keys
Create a `.env` file in the root directory:
```
XAI_API_KEY=your_xai_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 4. Launch the Application
```bash
streamlit run app.py
```

## 💡 Usage Examples

- **TALKEE.AI**: Start with a prompt like "Tell me about your hobbies"
- **Interview Practice**: Record audio responses to AI-generated interview questions
- **Storytelling Arena**: Record a narrative and receive comprehensive feedback
- **Listening Area**: Practice active listening and recall with AI-generated content
- **Presentation Review**: Upload presentation files for detailed analysis

## 🔍 Design Decisions

### API Choices
- **xAI (Grok)**: Chosen for its efficient NLP capabilities, allowing detailed feedback generation
- **OpenAI**: Used for robust LLM-based language generation and evaluation
- **Librosa**: Selected for its accuracy in analyzing pitch and pace in audio files
- **SpeechRecognition & gTTS**: Reliable libraries for speech-to-text and text-to-speech functionalities

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.