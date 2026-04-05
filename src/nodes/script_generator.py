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
            You are a YouTube Shorts scriptwriter for Indian students (Class 6-12).

            TOPIC: {topic}
            GENRE: {genre}

            Write a 45-60 second script (100-140 words).

            STYLE:
            - Speak directly to "you"
            - Clear, simple, engaging
            - Like a great teacher explaining visually

            STRUCTURE:
            1. Hook (curiosity in first line)
            2. Simple explanation
            3. Build insight
            4. Surprising conclusion

            RULES:
            - No "Did you know"
            - No filler or repetition
            - No dramatic pauses
            - Must be easy to visualize

            IMPORTANT:
            Every sentence should be something that can be animated visually.

            Avoid repeating:
            {previous_script}
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