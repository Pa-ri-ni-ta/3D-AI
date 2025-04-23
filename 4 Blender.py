import speech_recognition as sr
import google.generativeai as genai

# Set up Gemini
genai.configure(api_key="####")  # Replace with your actual API key

def voice_to_text():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Speak your design (e.g., 'A round table with 4 legs'):")
        audio = r.listen(source, timeout=10)
    try:
        text = r.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except:
        print("Sorry, I didn't catch that.")
        return ""

def text_to_3d(prompt):
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    
    response = model.generate_content(
        f"""Convert this description into a complete Blender Python script.
        The script should:
        1. Delete existing objects first
        2. Create the described 3D model using primitive shapes
        3. Name all objects appropriately
        4. Use correct Blender API syntax
        
        Description: {prompt}
        
        Output ONLY the Python code with no additional text or explanations.
        Example structure:
        import bpy
        # Clear scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        # Create objects...
        """
    )
    return response.text

if __name__ == "__main__":
    design_prompt = voice_to_text()
    if design_prompt:
        blender_script = text_to_3d(design_prompt)
        
        # Save the script
        with open("design.py", "w") as f:
            f.write(blender_script)
        
        print("\nSuccess! Generated Blender script:")
        print("----------------------------------")
        print(blender_script)
        print("----------------------------------")
        print("Saved to 'design.py'. Open this in Blender's Scripting tab and run it.")