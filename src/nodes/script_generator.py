from ..state import ShortsState
from langchain_openai import ChatOpenAI
import os
from pydantic import BaseModel

class ScriptOutput(BaseModel):
    script: str
    caption: str

llm = ChatOpenAI(
    model="qwen/qwen3-next-80b-a3b-instruct:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

llm_struct_output = llm.with_structured_output(ScriptOutput)

def script_generator(state: ShortsState) -> dict:
    topic = state['topic']
    genre = state['genre']
    previous_script = state['previous_script']
    review = state['review']

    prompt = f"""
        You are a viral YouTube Shorts scriptwriter.

        Write a HIGH-RETENTION script for a 30-second YouTube Short.

        TOPIC: {topic}
        GENRE: {genre}

        GOAL:
        Make the viewer watch till the end.

        STRICT RULES:
        - Count your words. 80 is the hard limit. Under 70 is ideal.
        - First line MUST be a strong hook
        - Use simple, spoken language
        - No fluff, no filler
        - One idea only
        - Keep sentences short
        - Add a curiosity gap
        - Avoid repeating structure or phrasing from: {previous_script}
        - End with a line that makes viewer want to share
        - Never start with "Did you know"
        - Speak directly to viewer using "you"

        STYLE GUIDE:
        Space → make them feel small against the universe
        Earth → reveal something hiding in plain sight  
        Psychology → make them say "wait, that's literally me"

        STRUCTURE:
        Hook (1 line)
        Build curiosity
        Reveal
        Twist or final punch
        """
    
    if review:
        prompt += f"""
        
        FEEDBACK FROM REVIEWER (must be applied): 
        {review}"""

    prompt += """
            Return the output strictly as JSON with this schema:
            {
            "script": "<your script>",
            "caption": "<short caption under 10 words>"
            }
        """

    resp = llm_struct_output.invoke(prompt)
    script = resp.script
    caption = resp.caption

    return {'previous_script': state['script'], 'script': script, 'caption': caption, 'review': ''}
