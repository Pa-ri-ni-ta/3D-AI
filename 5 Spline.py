import speech_recognition as sr
import google.generativeai as genai
import webbrowser

# Set up voice recognition
def hear_me():
    r = sr.Recognizer()
    with sr.Microphone() as mic:
        print("🎤 Speak your design (e.g., 'A red chair'):")
        audio = r.listen(mic)
    try:
        text = r.recognize_google(audio)
        print(f"✅ You said: {text}")
        return text
    except:
        print("❌ Didn't catch that. Try again!")
        return ""

# Connect to AI (PASTE YOUR API KEY BELOW)
genai.configure(api_key="####")  # ← Get this from https://aistudio.google.com/app/apikey

def make_3d_model(idea):
    model = genai.GenerativeModel('gemini-1.5-pro-latest')  # ← Fixed model name
    response = model.generate_content(
        f"Create Spline 3D code (JSON format) for: {idea}. "
        "Only output raw JSON code between ``` markers."
    )
    return response.text.split('```')[1]  # Extract the code

# Main program
print("🌟 Voice-to-3D Magic Starter 🌟")
while True:
    idea = hear_me()
    if idea:
        print("🛠️ Creating your 3D model...")
        spline_code = make_3d_model(idea)
        
        # Save to file
        with open("my_design.json", "w") as f:
            f.write(spline_code)
            
        # Open Spline
        webbrowser.open("https://spline.design")
        print("👉 Go to Spline → Click 'Import' → Upload 'my_design.json'")
    input("Press Enter to try again...")