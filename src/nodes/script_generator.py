from state import ShortsState
from langchain_openai import ChatOpenAI
import os
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

class ScriptOutput(BaseModel):
    script: str
    caption: str

llm = ChatOpenAI(
    model="qwen/qwen3.6-plus:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_KEY")
)

llm_struct_output = llm.with_structured_output(ScriptOutput)

def script_generator(state: ShortsState) -> dict:
    topic = state['topic']
    genre = state['genre']
    previous_script = state.get('previous_script', '')
    review = state.get('review', '')

    prompt = f"""
            You are an educational YouTube Shorts scriptwriter for Indian school students (Class 6-12).

            Write a clear, engaging script that explains a concept in 45-60 seconds.

            TOPIC: {topic}
            GENRE: {genre}

            RULES:
            - Word count: 100-130 words
            - Tone: warm, curious teacher talking to a student
            - Flow: natural continuous sentences, no fragments
            - Structure: Hook → Explain simply → Build to surprising truth → Mind-blowing conclusion
            - First line must hook immediately — reuse or rephrase the topic
            - No "Did you know", no broken dramatic pauses
            - Speak directly to viewer using "you"
            - Never repeat phrasing from: {previous_script}

            GENRE STYLE:
            - science: explain the mechanism behind the phenomenon
            - geography: connect place/event to something student can visualize
            - fun_facts: reveal the surprising truth hiding behind everyday things
            """

    if review:
        prompt += f"""

            Apply this feedback strictly:
            {review}
        """

    # ALWAYS enforce JSON
    prompt += """
        STRICT OUTPUT FORMAT:

        Return ONLY valid JSON.
        No explanation. No extra text.

        {
        "script": "text",
        "caption": "short caption"
        }
        """

    # SAFE CALL
    try:
        resp = llm_struct_output.invoke(prompt)
        script = resp.script
        caption = resp.caption

    except Exception as e:
        print(f"⚠️ Structured output failed: {e}")

        try:
            raw = llm.invoke(prompt)
            content = raw.content if hasattr(raw, "content") else str(raw)

            print("RAW RESPONSE:", content)

            # naive fallback
            script = content[:300]
            caption = "Watch this 👀"

        except Exception as e2:
            print(f"❌ LLM completely failed: {e2}")
            script = "Something surprising is happening... and you need to see this."
            caption = "Wait for it 👀"

    print(f"Script - {script}\n")
    print(f"Caption - {caption}\n")

    return {
        'previous_script': state.get('script', ''),
        'script': script,
        'caption': caption,
        'review': ''
    }