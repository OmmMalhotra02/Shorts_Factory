import json
from state import ShortsState
from langchain_openai import ChatOpenAI
import os

llm = ChatOpenAI(
    model="nvidia/nemotron-3-super-120b-a12b:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_KEY")
)

def scene_planner(state: ShortsState) -> dict:
    script = state["script"]

    prompt = f"""
        Break this script into animation scenes.

        RULES:
        - Each sentence = one scene
        - Keep order EXACTLY same
        - No merging or skipping

        For each scene return:
        - text: exact sentence
        - visual: very specific animation idea (what appears, how it moves)

        SCRIPT:
        {script}

        Return ONLY valid JSON:
        [
        {{
            "text": "...",
            "visual": "..."
        }}
        ]
    """

    response = llm.invoke(prompt).content.strip()

    # Clean JSON if needed
    if response.startswith("```"):
        response = response.split("```")[1]
        if response.startswith("json"):
            response = response[4:]

    try:
        scene_plan = json.loads(response)
    except Exception as e:
        print("Scene planner JSON error:", e)
        print(response)
        raise

    print("\nGenerated Scene Plan:")
    for i, s in enumerate(scene_plan):
        print(f"{i+1}. {s['text']} -> {s['visual']}")

    return {"scene_plan": scene_plan}