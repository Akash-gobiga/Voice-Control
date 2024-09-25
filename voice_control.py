import speech_recognition as sr
import firebase_admin
from firebase_admin import credentials, db
import pyttsx3
import sys

# Initialize Firebase
cred = credentials.Certificate('D:\\College\\serviceAccountKey.json')  # Replace with your Firebase service account key path
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://iwms-v2-default-rtdb.firebaseio.com/'  # Replace with your database URL
})

# Initialize the recognizer
recognizer = sr.Recognizer()

# Initialize the text-to-speech engine
tts_engine = pyttsx3.init()

# Set the speech rate (words per minute)
tts_engine.setProperty('rate', 150)  # Adjust this value as needed

# Optionally, print the current rate for reference
current_rate = tts_engine.getProperty('rate')
print(f"Current speech rate set to: {current_rate} wpm")

# Fetch and store the initial states of the lights dynamically from Firebase
def get_initial_states():
    ref = db.reference('/Automation')
    return ref.get()  # This will return a dictionary with all the lights and their states

# Dynamically map lights to human-readable labels like "light one", "light two", "light three"
def map_lights_to_labels(light_states):
    mapped_lights = {}
    for idx, light in enumerate(light_states, start=1):
        label = f"light {idx}"
        mapped_lights[label] = light
    return mapped_lights

# Update the LED state in Firebase
def update_led_state(led, state):
    ref = db.reference(f'Automation/{led}')
    ref.set(state)
    print(f"Set {led} to {state}")

# Text-to-speech function
def speak(message):
    tts_engine.say(message)
    tts_engine.runAndWait()

# Listen for commands using speech recognition
def listen_for_commands():
    with sr.Microphone() as source:
        print("Listening for commands... (Say 'stop' to exit)")
        recognizer.adjust_for_ambient_noise(source)  # Adjust for background noise
        audio = recognizer.listen(source, timeout=10)  # Increase timeout to 10 seconds

        try:
            command = recognizer.recognize_google(audio)
            command = preprocess_command(command)
            print(f"You said: {command}")
            process_command(command)
        except sr.UnknownValueError:
            print("Sorry, I did not understand the audio.")
        except sr.RequestError:
            print("Could not request results; check your network connection.")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

# Pre-process the command to handle variations
def preprocess_command(command):
    command = command.lower()
    command = " ".join(dict.fromkeys(command.split()))  # Remove duplicate words

    # Standardizing common phrases
    command = command.replace("turn on", "on")
    command = command.replace("turn off", "off")
    command = command.replace("switch on", "on")
    command = command.replace("switch off", "off")

    # Handling variations in light names
    command = command.replace("light one", "light 1")
    command = command.replace("light two", "light 2")
    command = command.replace("light three", "light 3")

    return command.strip()  # Ensure no extra spaces

# Process the voice command and dynamically toggle the corresponding LED state
def process_command(command):
    global mapped_lights, light_states  # Use the global mapped lights and light states

    print(f"Processing command: {command}")  # Debugging line

    if command in ["stop", "exit", "quit"]:  # Check for stop commands early
        print("Stopping the program...")
        speak("Stopping the program...")
        sys.exit()

    for label, light in mapped_lights.items():  # Iterate through mapped labels
        if label in command:  # Check if the command contains the mapped light label
            if "on" in command:
                current_state = light_states[light]
                if current_state == 0:
                    update_led_state(light, 1)
                    light_states[light] = 1  # Update local state
                    message = f"{label} is now ON."  # Simplified message
                    print(message)
                    speak(message)  # Speak the action
                else:
                    message = f"{label} is already ON."  # Simplified message
                    print(message)
                    speak(message)  # Speak the status
            elif "off" in command:
                current_state = light_states[light]
                if current_state == 1:
                    update_led_state(light, 0)
                    light_states[light] = 0  # Update local state
                    message = f"{label} is now OFF."  # Simplified message
                    print(message)
                    speak(message)  # Speak the action
                else:
                    message = f"{label} is already OFF."  # Simplified message
                    print(message)
                    speak(message)  # Speak the status
            break
    else:
        print("Command did not match any known lights.")  # Inform if command was unrecognized
        speak("Command did not match any known lights.")

if __name__ == "__main__":
    # Fetch initial states from Firebase
    light_states = get_initial_states()  # Get all the lights and their initial states
    print(f"Initial light states: {light_states}")

    # Dynamically map lights to labels like "light one", "light two", etc.
    mapped_lights = map_lights_to_labels(light_states)
    print(f"Mapped lights: {mapped_lights}")

    try:
        # Continuously listen for commands
        while True:
            listen_for_commands()

    except KeyboardInterrupt:
        # Gracefully stop the program if the user presses Ctrl+C
        print("\nProgram stopped by user.")
        sys.exit()
