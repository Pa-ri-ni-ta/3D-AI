import google.generativeai as genai
import gradio as gr
import time
import os
import subprocess

# Set up Gemini API Key (Recommended: use environment variable in production)
genai.configure(api_key="####")

def expand_concept(raw_prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        guide = (
            "Expand the following design prompt into an explicit 3D modeling breakdown.\n"
            "Use primitive shapes (cube, cylinder, sphere, cone, etc.) to describe each part.\n"
            "Be detailed but compact. Don't write code. Just output the revised description."
        )
        result = model.generate_content(f"{guide}\n\nOriginal: {raw_prompt}")
        return result.text.strip()
    except Exception as e:
        return raw_prompt

def text_to_3d(prompt):
    prompt = expand_concept(prompt)

    if not prompt.strip():
        return "Please provide a description first."

    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        system_instruction = """
        You are a Blender 4.4 Python scripting expert.
        You must output syntactically valid, executable Blender scripts using the `bpy` module.
        Follow these rules strictly:
        - Output ONLY the code, no comments or explanations.
        - Start by clearing the scene.
        - Use primitive shapes like cubes, cylinders, spheres.
        - Assign materials with RGB color values and alpha = 1.0.
        - Always name objects logically (e.g., TableTop, Leg1).
        - Add at least one camera and one light to the scene.
        - Set camera to point at the center of the scene.
        - Render settings are NOT required.

        Here is an example:
        import bpy
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
        cube = bpy.context.object
        cube.name = "RedCube"
        mat = bpy.data.materials.new(name="Red")
        mat.diffuse_color = (1.0, 0.0, 0.0, 1.0)
        cube.active_material = mat

        Now generate a script for this user description:
        """

        response = model.generate_content(system_instruction + f"\n{prompt}")
        code = response.text.strip()
        if code.startswith("```python"):
            code = code.split("```python", 1)[-1].strip()
        if code.endswith("```"):
            code = code.rsplit("```", 1)[0].strip()
        return code
    except Exception as e:
        return f"Error generating script: {str(e)}"

def process_input(audio, text_input):
    if audio is not None:
        try:
            import whisper
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
    timestamp = int(time.time())
    filename = f"design_{timestamp}.py"
    with open(filename, "w") as f:
        f.write(blender_script)

    return design_prompt, blender_script, filename

def open_in_blender(file_path):
    try:
        subprocess.Popen(["blender", "--python", file_path])
    except Exception as e:
        print("Blender launch failed:", e)

with gr.Blocks(title="🎨 Voice/Text to Colored Blender Script Generator") as demo:
    gr.Markdown("# 🧠 AI to Blender: Voice & Text Based 3D Script Generator")
    gr.Markdown("Generate Blender Python code using simple descriptions. Speak or type your idea — download and run it in Blender!")

    with gr.Row():
        audio_input = gr.Audio(type="filepath", label="🎙️ Audio Input")
        text_input = gr.Textbox(label="📝 Text Prompt", placeholder="Describe your 3D model...")
        output_prompt = gr.Textbox(label="🔍 Interpreted Prompt")

    generate_button = gr.Button("🚀 Generate 3D Code")
    open_button = gr.Button("🟢 Open in Blender")

    with gr.Row():
        output_script = gr.Code(label="🧾 Generated Blender Script", language="python")
        download = gr.File(label="💾 Download Script")

    generate_button.click(
        fn=process_input,
        inputs=[audio_input, text_input],
        outputs=[output_prompt, output_script, download]
    )

    open_button.click(
        fn=open_in_blender,
        inputs=[download],
        outputs=[]
    )

if __name__ == "__main__":
    demo.launch(share=True, inbrowser=True)
