import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Adaptive Medical Voice Assistant", layout = "wide")

# initial state 
if "step" not in st.session_state:
    st.session_state.step = "greet"
    #tracks if user is in conversation mode
if "slow_mode" not in st.session_state:
    st.session_state.slow_mode = False
    # tracks if adaptive pacing is currently active
if "speech_rate" not in st.session_state:
    st.session_state.speech_rate = 1.0
    # controls TTS playback speed with 1 being baseline speed
if "timeout_threshold" not in st.session_state:
    st.session_state.timeout_threshold = 5
    # baseline silence duration in seconds
if "repeat_counter" not in st.session_state:
    st.session_state.repeat_counter = 0
    # implements repeat counter variable to track number of re-asks
if "selected_slot" not in st.session_state:
    st.session_state.selected_slot = None
    # stores string of appointment eg. sunday 22 nov at 10am
if "slot_index" not in st.session_state:
    st.session_state.slot_index = 0
    # tracks which appointment in slots list is being offered
if "system_message" not in st.session_state:
    st.session_state.system_message = (
        "Hello, I can help you book a GP appointment. " \
        "Available slots are: Tuesday at 10 AM, Wednesday at 2 PM, Thursday at 9 AM, or Friday at 2:00 PM. "
    )
if "inferred_state" not in st.session_state:
    st.session_state.inferred_state = "Normal interaction flow"
    # readable explanation of why the system did what it did

# simulated backend
SLOTS = [
    "Tuesday 24 Nov at 10:00 AM with Dr. Loskutova",
    "Wednesday 25 Nov at 2:00 PM with Dr. Hensley",
    "Thursday 26 Nov at 9:00 AM with Dr. Ofori-Atta",
    "Friday 27 Nov at 2:00 PM with Dr. Bahia"
]

HOLDING_CUES = ["hang on", "wait", "one second", "diary", "hold on", "one moment", "give me a second"] 

# Browser 
def speak_text(text: str, rate: float):
    effective_rate = round(max(0.55, rate - 0.05), 2) if len(text.split()) > 16 and rate < 1.0 else rate
    # if slow mode is active and the message is long, speaking speed drops by an extra 0.05
    # minimum speed capped at 0.55
    safe_text = text.replace('"', '\\"').replace("\n", " ")
    # removes quotation marks and line breaks to be inserted in javascript
    components.html(
        f"""
        <script>
            window.speechSynthesis.cancel();
            const msg = new SpeechSynthesisUtterance("{safe_text}");
            msg.rate = {effective_rate};
            window.speechSynthesis.speak(msg);
        </script>
        """,
        height = 0,
    )
    # invisible block in browser runs to produce audio
    # stops speaking if user clicks a button

#decision logic

def process_user_turn(user_text: str, pause_seconds: int):
    cleaned = user_text.strip().lower()

    # check for holding cue "wait" etc
    if any(cue in cleaned for cue in HOLDING_CUES):
        st.session_state.timeout_threshold = 20
        st.session_state.inferred_state = "Holding cue detected, extending timeout"
        st.session_state.system_message = "No problem, let me know when you are ready."
        return

    # Check if user asks to return to normal/faster pace (Bidirectional Pacing Control)
    if any(phrase in cleaned for phrase in ["faster", "speed up", "normal pace", "normal speed"]):
        st.session_state.slow_mode = False
        st.session_state.speech_rate = 1.0
        st.session_state.timeout_threshold = 5
        st.session_state.inferred_state = "User requested faster pace, Restored default speed (1.0x)"
        if st.session_state.step == "confirm_booking" and st.session_state.selected_slot:
            st.session_state.system_message = (
                f"Okay, returning to my normal speaking pace. Please confirm: {st.session_state.selected_slot}. Is this correct?"
            )
        else:
            st.session_state.step = "offer_slots"
            st.session_state.system_message = (
                "Okay, returning to my normal speaking pace. "
                "We have Tuesday at 10 AM, Wednesday at 2 PM, or Friday at 9 AM. Which suits you?"
            )
        return

    # check if pause exceeded baseline threshold
    if pause_seconds > st.session_state.timeout_threshold and not st.session_state.slow_mode:
        st.session_state.repeat_counter += 1
        st.session_state.step = "negotiate_pace"
        st.session_state.inferred_state = f"Pause ({pause_seconds}s) > baseline ({st.session_state.timeout_threshold}s), infer pacing too fast"
        st.session_state.system_message = ( "You took longer than usual to respond. Would you like me to speak at a slower pace and show one option at a time?")
        return

    # Handle response for pacing negotiation
    if st.session_state.step == "negotiate_pace":
        if "yes" in cleaned or "slow" in cleaned:
            # if the user confirms they need slower speech/ options one at a time
            st.session_state.slow_mode = True
            st.session_state.speech_rate = 0.72
            st.session_state.timeout_threshold = 15
            st.session_state.step = "offer_slots"
            st.session_state.inferred_state = "User confirmed slower pace, adapted mode active"
            st.session_state.system_message = (
                f"I'll slow down. Let me know if you want me to speak faster. "
                f"First option: {SLOTS[st.session_state.slot_index]}. Would you like this slot?") 
        elif "no" in cleaned and st.session_state.slow_mode and st.session_state.step in ["greet", "offer_slots"]:
            # if the user dosent confirm they need slower speed - give them a longer wait next time isntead
            st.session_state.timeout_threshold = 15
            st.session_state.step = "offer_slots"
            st.session_state.inferred_state = "False positive corrected by user ,kept default pace, extended timer"
            st.session_state.system_message = (
                "Understood. I will keep my normal pace and give you extra time. "
                "We have Tuesday at 10 AM, Wednesday at 2 PM, Thursday at 9 AM, or Friday at 2 PM."
            )
        return

    #Slot selection
    if "tuesday" in cleaned or ("yes" in cleaned and st.session_state.slow_mode and st.session_state.slot_index == 0 and st.session_state.step != "confirm_booking"):
        st.session_state.selected_slot = SLOTS[0]
        st.session_state.step = "confirm_booking"
        st.session_state.inferred_state = "Slot selected, awaiting confirmation"
        st.session_state.system_message = f"Please confirm: {SLOTS[0]}. Is this correct?"
    elif "wednesday" in cleaned or ("yes" in cleaned and st.session_state.slow_mode and st.session_state.slot_index == 1 and st.session_state.step != "confirm_booking"):
        st.session_state.selected_slot = SLOTS[1]
        st.session_state.step = "confirm_booking"
        st.session_state.inferred_state = "Slot selected, awaiting confirmation"
        st.session_state.system_message = f"Please confirm: {SLOTS[1]}. Is this correct?"
    elif "thursday" in cleaned or ("yes" in cleaned and st.session_state.slow_mode and st.session_state.slot_index == 2 and st.session_state.step != "confirm_booking"):
        st.session_state.selected_slot = SLOTS[2]
        st.session_state.step = "confirm_booking"
        st.session_state.inferred_state = "Slot selected, awaiting confirmation"
        st.session_state.system_message = f"Please confirm: {SLOTS[2]}. Is this correct?"
    elif "friday" in cleaned or ("yes" in cleaned and st.session_state.slow_mode and st.session_state.slot_index == 3 and st.session_state.step != "confirm_booking"):
        st.session_state.selected_slot = SLOTS[3]
        st.session_state.step = "confirm_booking"
        st.session_state.inferred_state = "Slot selected, awaiting confirmation"
        st.session_state.system_message = f"Please confirm: {SLOTS[3]}. Is this correct?"
    elif "no" in cleaned and st.session_state.slow_mode and st.session_state.step == "offer_slots":
        st.session_state.slot_index = (st.session_state.slot_index + 1) % len(SLOTS)
        st.session_state.system_message = f"Ok, Next option: {SLOTS[st.session_state.slot_index]}. Would you like this slot?"
    elif st.session_state.step == "confirm_booking" and ("confirm" in cleaned or "yes" in cleaned or "correct" in cleaned):
        st.session_state.step = "booked"
        st.session_state.inferred_state = "Booking verified and completed"
        st.session_state.system_message = f"Your appointment is booked for {st.session_state.selected_slot}."
    else:
        st.session_state.repeat_counter += 1
        st.session_state.inferred_state = "Unrecognised input, Offering clarification"
        st.session_state.system_message = f"I didn't match a valid option. Currently available: {SLOTS[st.session_state.slot_index]}. "
    "Please say 'yes', 'no', or tap a button on screen."
    
# UI layout
col_main, col_inspector = st.columns([2, 1])

with col_main:
    st.title("GP Appointment Voice & Screen Assistant")
    st.caption("(simulated clinic schedule)")
    # spoken and visual prompt card
    st.info(f"**Assistant Says ({st.session_state.speech_rate}x speed):**\n\n### {st.session_state.system_message}")
    speak_text(st.session_state.system_message, st.session_state.speech_rate)

    # Simulated Voice Input & Pause Simulator
    st.subheader("Simulate Spoken Input & Pause")
    with st.form("turn_form", clear_on_submit=True):
        simulated_speech = st.text_input("Simulated User Speech")
        pause_duration = st.slider("Simulated Silence / Pause Before Speaking (seconds):", 0, 20, 2)
        submitted = st.form_submit_button("Send Turn")
        if submitted:
            process_user_turn(simulated_speech, pause_duration)
            st.rerun()

    st.divider()

    # Multimodal Visual Controls
    st.subheader("Visual Options")
    if st.session_state.step == "negotiate_pace":
        c1, c2 = st.columns(2)
        if c1.button("Yes, speak slower (1 option at a time)", use_container_width=True, type="primary"):
            process_user_turn("yes slow down", 0)
            st.rerun()
        if c2.button("No, wait one second", use_container_width=True):
            process_user_turn("no", 0)
            st.rerun()

    elif st.session_state.step == "confirm_booking":
        st.warning(f"**Verify Appointment Details:** {st.session_state.selected_slot}")
        c1, c2 = st.columns(2)
        if c1.button("Confirm Booking", use_container_width=True, type="primary"):
            process_user_turn("confirm", 0)
            st.rerun()
        if c2.button("Change Slot", use_container_width=True):
            st.session_state.step = "offer_slots"
            st.session_state.system_message = "Okay, let's pick a different time. We have Tuesday at 10 AM, Wednesday at 2 PM, or Friday at 9 AM. Which suits you?"
            st.rerun()

    elif st.session_state.step == "booked":
        st.success(f"**Confirmed:** {st.session_state.selected_slot}")
        if st.button("Start New Booking Demo"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    else:
        # Show 1 slot at a time in Slow Mode, or all 3 in Default Mode
        visible_slots = [SLOTS[st.session_state.slot_index]] if st.session_state.slow_mode else SLOTS
        for slot in visible_slots:
            if st.button(f"Select: {slot}", use_container_width=True):
                process_user_turn(slot.split(" ")[0], 0)
                st.rerun()
        if st.session_state.slow_mode:
            if st.button("Hear Next Option", use_container_width=True):
                process_user_turn("no", 0)
                st.rerun()

    

with col_inspector:
    st.subheader("System State Inspector")
    st.caption("Live internal logic from flow diagram (Implemented / Simulated)")
    st.metric("Speech Rate", f"{st.session_state.speech_rate}x", "Adapted" if st.session_state.slow_mode else "Default")
    st.metric("Pause Timeout Threshold", f"{st.session_state.timeout_threshold}s")
    st.metric("Repeat Counter", st.session_state.repeat_counter)
    st.markdown(f"**Current State:** `{st.session_state.step}`")
    st.markdown(f"**System Inference:** {st.session_state.inferred_state}")
