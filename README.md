# adaptive-medical-voice-assistant
## project status
**Implemented:**
* Interaction layer dialogue
* Adaptive TTS rate scaling (1.0x default, 0.72x slow mode, extra reduction for sentences over 16 words)
* Scanning for holding cues eg. ("hang on", "one second", "wait").
* Adaptive threshold of silence between turns (5s baseline, can increase to 15-20s)
* Slow mode can read appointments one by one
* Explicit confirmation required from user before booking an appointment
* Sidebar with System state Information

**Simulated:**
* Speech input simulated via text
* Length of user pause simulated via slider
* GP appointment slots simulated via hardcoding 4 imaginary slots

**Planned:**
* Live microphone speech to text user input
* Integration with a real GP booking API

## Technology Stack
* Python 3 & Streamlit : Interactive web prototype UI
* Browser Web Speech API (window.speechSynthesis) : Text to speech synthesis with adjustable 'utterance.rate'
* AI assistance tools: Gemini used for code debugging

## Running and Inspecting the Work
```bash
#1. Clone the repository and enter the directory
git clone https://github.com/caitlin-parsons17/adaptive-medical-voice-assistant
cd adaptive-medical-voice-assistant

#2. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1 # On macOS/Linux: source venv/bin/activate

#3. Install dependencies and launch
pip install -r requirements.txt
python -m streamlit run app.py
```

## Development Record
* created appointment booking flow based on story board (greet -> offer_slots -> confirm_booking -> booked)
* added system state inspector to view metrics during simulation
* implemented text to speech with browser web speech API and added adaptive speech pacing
* added silence length vs baseline checks to decide when the system would act
* added holding cue parsing to extend timeout
* fixed slot day parsing across all four appointments
* added reversibility for slow mode.
* adjusted dialogue to improve user experience eg. "sorry i didn't catch that" puts the burden on the user/ replaced with "I didn't match a valid option. Currently available: {SLOTS[st.session_state.slot_index]}. " "Please say 'yes', 'no', or tap a button on screen." this provides the user with more guidance.
* ran each storyboard flow to check it worked. 

## AI assistance
Gemini was used to debug logic for parsing GP appointment slots, as well as checking README and report structure against module breif. I manually adapted my code and report based on the suggestions given. 
