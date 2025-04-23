import google.generativeai as genai
import gradio as gr
import time
import os

# Set up Gemini - replace with your actual API key
genai.configure(api_key="####")

def text_to_3d(prompt):
    if not prompt.strip():
        return "Please provide a description first."
    
    try:
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
    except Exception as e:
        return f"Error generating script: {str(e)}"

def process_input(audio, text_input):
    # If audio input is provided, transcribe it
    if audio is not None:
        try:
            import whisper  # We'll use whisper for speech-to-text
            model = whisper.load_model("base")
            result = model.transcribe(audio)
            design_prompt = result["text"]
        except Exception as e:
            return f"Error transcribing audio: {str(e)}", "", ""
    else:
        design_prompt = text_input
    
    if not design_prompt:
        return "No input received", "", ""
    
    blender_script = text_to_3d(design_prompt)
    
    # Save the script
    timestamp = int(time.time())
    filename = f"design_{timestamp}.py"
    with open(filename, "w") as f:
        f.write(blender_script)
    
    return design_prompt, blender_script, filename

with gr.Blocks(title="Voice to 3D Model Generator") as demo:
    gr.Markdown("# 🎤 Voice to 3D Model Generator")
    gr.Markdown("Describe your 3D model and get a Blender Python script!")
    
    with gr.Row():
        with gr.Column():
            audio_input = gr.Audio(type="filepath", label="Speak your design (click to record)")
            text_input = gr.Textbox(label="Or type your description here", 
                                  placeholder="A round table with 4 legs...")
            submit_btn = gr.Button("Generate Blender Script", variant="primary")
            
        with gr.Column():
            output_prompt = gr.Textbox(label="Your input")
            output_script = gr.Code(label="Generated Blender Script", 
                                  language="python")
            download = gr.File(label="Download Script")

    submit_btn.click(
        fn=process_input,
        inputs=[audio_input, text_input],
        outputs=[output_prompt, output_script, download]
    )

if __name__ == "__main__":
    demo.launch()
