import google.generativeai as genai 
import gradio as gr
import time
import os
import subprocess

# Set up Gemini API Key
genai.configure(api_key="AIzaSyANd4ewoF49WipY4_nOM3cnzUmEa_zmWxE")  # Replace with your actual Gemini key

# --- FLAT CONCEPT CATALOG ---
concept_catalog = {
    "Chair": {"parts": ["Seat", "Backrest", "Legs"], "default_materials": {"Seat": "red", "Backrest": "black", "Legs": "gray"}},
    "Table": {"parts": ["Top", "Legs"], "default_materials": {"Top": "lightbrown", "Legs": "darkbrown"}},
    "Bed": {"parts": ["Frame", "Mattress", "Pillows"], "default_materials": {"Frame": "wood", "Mattress": "white", "Pillows": "blue"}},
    "Bookshelf": {"parts": ["Sides", "Shelves", "Back Panel"], "default_materials": {"Sides": "brown", "Shelves": "white", "Back Panel": "gray"}},
    "Sofa": {"parts": ["Base", "Cushions", "Armrests"], "default_materials": {"Base": "darkgray", "Cushions": "blue", "Armrests": "black"}},
    "Car": {"parts": ["Body", "Wheels", "Windows"], "default_materials": {"Body": "blue", "Wheels": "black", "Windows": "transparent"}},
    "Bicycle": {"parts": ["Frame", "Wheels", "Handlebar", "Seat"], "default_materials": {"Frame": "blue", "Wheels": "black", "Handlebar": "gray", "Seat": "red"}},
    "Tree": {"parts": ["Trunk", "Leaves"], "default_materials": {"Trunk": "brown", "Leaves": "green"}},
    "Windmill": {"parts": ["Tower", "Blades", "Base"], "default_materials": {"Tower": "white", "Blades": "lightgray", "Base": "stone"}},
    "House": {"parts": ["Walls", "Roof", "Door"], "default_materials": {"Walls": "white", "Roof": "brown", "Door": "yellow"}},
    "Bridge": {"parts": ["Pillars", "Roadbed", "Supports"], "default_materials": {"Pillars": "concrete", "Roadbed": "gray", "Supports": "metal"}}
}

# --- Generate Prompt from Catalog Entry ---
def generate_prompt_from_concept(concept):
    if concept not in concept_catalog:
        return ""
    parts = concept_catalog[concept]["parts"]
    materials = concept_catalog[concept]["default_materials"]
    lines = [f"Create a {concept.lower()} using the following parts:"]
    for part in parts:
        color = materials.get(part, "any color")
        lines.append(f"- {part} colored {color}")
    lines.append("Use primitive shapes and name each part logically.")
    return "\n".join(lines)

# --- Expand Prompt with Gemini ---
def expand_concept(raw_prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        guide = (
            "Expand the following design prompt into a detailed 3D modeling breakdown.\n"
            "- For each part, identify the primitive shape to use.\n"
            "- Assign realistic dimensions in centimeters.\n"
            "- Retain and reflect any colors explicitly mentioned in the original prompt.\n"
            "- Do not add colors that are not mentioned unless clearly logical.\n"
            "- Format the output clearly. DO NOT include Blender code."
        )
        result = model.generate_content(f"{guide}\n\nOriginal: {raw_prompt}")
        return result.text.strip()
    except Exception:
        return raw_prompt

# --- Generate Blender Python Script ---
def text_to_3d(prompt):
    import re
    prompt = expand_concept(prompt)
    if not prompt.strip():
        return "Please provide a description first."

    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        system_instruction = """
        You are a Blender 4.4 Python scripting expert.
        Output valid Blender Python scripts using bpy.
        - Start by clearing the scene.
        - Use primitives (cube, cylinder, sphere).
        - Name each object.
        - For each object:
            - Create a new material.
            - Assign it to the object.
            - Set `mat.diffuse_color = "colorname"` using the part's color mentioned in the description.
        - Add a camera and a light.
        - No extra commentary or markdown.
        """

        response = model.generate_content(system_instruction + f"\n{prompt}\n\nColors in the description must appear in the material setup exactly as specified.")
        code = response.text.strip()

        if code.startswith("```python"):
            code = code.split("```python", 1)[-1].strip()
        if code.endswith("```"):
            code = code.rsplit("```", 1)[0].strip()

        # --- Color enforcement ---
        COLOR_MAP = {
            "red": (1.0, 0.0, 0.0, 1.0),
            "blue": (0.0, 0.0, 1.0, 1.0),
            "green": (0.0, 1.0, 0.0, 1.0),
            "yellow": (1.0, 1.0, 0.0, 1.0),
            "gray": (0.5, 0.5, 0.5, 1.0),
            "black": (0.0, 0.0, 0.0, 1.0),
            "white": (1.0, 1.0, 1.0, 1.0),
            "brown": (0.6, 0.3, 0.1, 1.0),
            "orange": (1.0, 0.5, 0.0, 1.0),
            "purple": (0.5, 0.0, 0.5, 1.0),
            "pink": (1.0, 0.75, 0.8, 1.0),
            "lightblue": (0.68, 0.85, 0.9, 1.0),
            "darkblue": (0.0, 0.0, 0.55, 1.0),
            "lightgray": (0.8, 0.8, 0.8, 1.0),
            "darkgray": (0.2, 0.2, 0.2, 1.0),
            "skyblue": (0.53, 0.81, 0.92, 1.0),
            "turquoise": (0.25, 0.88, 0.82, 1.0),
            "gold": (1.0, 0.84, 0.0, 1.0),
            "silver": (0.75, 0.75, 0.75, 1.0),
            "transparent": (1.0, 1.0, 1.0, 0.1)
        }

        def replace_diffuse(match):
            color_name = match.group(1).lower()
            rgba = COLOR_MAP.get(color_name, (1.0, 1.0, 1.0, 1.0))
            return f"mat.diffuse_color = {rgba}"

        # Replace color references with enforced values
        code = re.sub(r"mat\.diffuse_color\s*=\s*[\"'](\w+)[\"']", replace_diffuse, code)

        return code

    except Exception as e:
        return f"Error generating script: {str(e)}"


# --- Process Input: Text, Voice, or Concept ---
def process_input(audio, text_input, concept_prompt):
    design_prompt = text_input or concept_prompt
    if audio is not None:
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(audio)
            design_prompt = result["text"]
        except Exception as e:
            return f"Error transcribing audio: {str(e)}", "", ""
    if not design_prompt:
        return "No input received", "", ""
    blender_script = text_to_3d(design_prompt)
    timestamp = int(time.time())
    filename = f"design_{timestamp}.py"
    with open(filename, "w") as f:
        f.write(blender_script)
    return design_prompt, blender_script, filename

# --- Open Script in Blender ---
def open_in_blender(file_path):
    try:
        subprocess.Popen(["blender", "--python", file_path])
    except Exception as e:
        print("Blender launch failed:", e)

# --- Gradio UI ---
with gr.Blocks(title="🗣️🧊 PromptCAD") as demo:
    gr.Markdown("# 🤖 PromptCAD : A Multimodal AI-Powered Generator for Blender Python-Based 3D Modeling")
    gr.Markdown("Describe your 3D idea with text or voice, or pick a concept and run in Blender!")

    with gr.Row():
        audio_input = gr.Audio(type="filepath", label="🎙️ Voice Input")
        text_input = gr.Textbox(label="📝 Text Prompt", placeholder="e.g. a chair with four legs...")
        concept_dropdown = gr.Dropdown(label="🪄 Choose a Concept", choices=sorted(concept_catalog.keys()), interactive=True)
        concept_prompt_preview = gr.Textbox(label="📋 Prompt from Concept", lines=3)
        output_prompt = gr.Textbox(label="🔍 Final Used Prompt")

    concept_dropdown.change(fn=generate_prompt_from_concept, inputs=concept_dropdown, outputs=concept_prompt_preview)

    generate_button = gr.Button("🚀 Generate Blender Code")
    open_button = gr.Button(" 🧊 Open in Blender")

    with gr.Row():
        output_script = gr.Code(label="🧾 Blender Python Script", language="python")
        download = gr.File(label="💾 Download Script")

    generate_button.click(fn=process_input, inputs=[audio_input, text_input, concept_prompt_preview], outputs=[output_prompt, output_script, download])
    open_button.click(fn=open_in_blender, inputs=[download], outputs=[])

demo.launch(share=True, inbrowser=True)
