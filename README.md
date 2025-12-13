# Markdown to Video (Auto Manim Video Generator)

An automated system that transforms structured JSON scripts into animated videos using [Manim](https://www.manim.community/) and LLMs. This project leverages a self-correcting pipeline powered by [LangGraph](https://langchain-ai.github.io/langgraph/) to generate, lint, and refine animation code.

## 🚀 Key Features

*   **Script-to-Video**: Converts a JSON-based storyboard into a full video.
*   **Automated Code Generation**: Uses LLMs to generate Manim Python code from natural language scene descriptions.
*   **Self-Correcting Pipeline**: A robust workflow that includes:
    *   **Code Generation**: Creates initial animation code.
    *   **Linter**: Static analysis to catch syntax and import errors early.
    *   **Renderer**: Executes the code to generate video segments.
    *   **Critic**: (Optional) Analyzes the output for visual quality and provides feedback for regeneration.
*   **Text-to-Speech (TTS)**: Automatically generates audio narration for each scene.
*   **Video Assembly**: Stitches together individual scenes and audio into a final `full_movie.mp4`.

## 🛠️ Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management.

```bash
# Install dependencies
poetry install
```

*Note: You will also need system dependencies for Manim (FFmpeg, LaTeX/TeX Live, etc.) installed on your machine.*

## 📖 Usage

Run the main script with a path to your storyboard JSON file:

```bash
poetry run python src/main.py path/to/your/script.json
```

### Input Format

The input file should be a JSON object containing a list of scenes.

**Example `script.json`:**

```json
{
  "title": "My Explanation Video",
  "scenes": [
    {
      "scene_id": "01_intro",
      "description": "Show a large blue circle appearing in the center of the screen. Then display the text 'Hello World' above it.",
      "duration": 5.0,
      "elements": ["Blue Circle", "Text"],
      "audio_script": "Welcome to this demonstration. We start with a simple circle."
    },
    {
      "scene_id": "02_process",
      "description": "The circle transforms into a square and moves to the left.",
      "duration": 4.0,
      "elements": ["Square", "Transformation"],
      "audio_script": "Next, the shape changes form and moves aside."
    }
  ]
}
```

## 🏗️ Architecture

The system operates on a scene-by-scene basis:

1.  **Loader**: Parses the input JSON.
2.  **TTS Engine**: Generates audio for all scenes.
3.  **Graph Pipeline**: For each scene:
    *   Generates code based on `description` and `elements`.
    *   Validates code (Linter).
    *   Renders the scene (Manim).
    *   Retries automatically on failure.
4.  **Assembler**: Combines video segments and audio tracks.

## 📂 Project Structure

*   `src/main.py`: Entry point.
*   `src/components/`: Core logic (Assembler, TTS, Renderer, Linter, Critic).
*   `src/core/`: Data models and Graph definition.
*   `src/llm/`: LLM client configuration.
