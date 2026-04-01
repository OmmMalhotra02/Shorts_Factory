from ..state import ShortsState
import sqlite3
from typing import List
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from pathlib import Path
import os
load_dotenv()

DB_PATH = Path(__file__).parent.parent.parent / "db" / "topics.db"
llm = ChatOpenAI(
    model="qwen/qwen3-next-80b-a3b-instruct:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

class TopicResponse(BaseModel):
    topics: List[str]

def generate_topics(genre: str, existing_topics: List[str]) -> List[str]:
    """
    Call LLM to generate high-quality, viral-ready topics
    """

    prompt = f"""
        You are a viral YouTube Shorts content strategist specializing in {genre}.

        Generate exactly 20 topic ideas that will perform well as 30-45 second short videos.

        CRITERIA FOR EACH TOPIC:
        - Leads with a surprising, counterintuitive, or little-known fact
        - Has strong visual potential (landscapes, space imagery, human expressions)
        - Creates an immediate "I never knew that" reaction
        - Specific, not generic — name places, dates, numbers where possible

        BAD EXAMPLE: "Interesting facts about oceans"
        GOOD EXAMPLE: "The Pacific Ocean is wider than the Moon is from Earth"

        AVOID repeating these existing topics:
        {existing_topics[:100]}

        OUTPUT FORMAT:
        Generate a list of topics.
        Return the result as valid JSON in this format:
        {
            "topics": ["topic 1", "topic 2", "topic 3"]
        }
        """
    llm_struct_op = llm.with_structured_output(TopicResponse)
    resp = llm_struct_op.invoke(prompt)
    
    return resp.topics

def ensure_topice_pool(genre: str, cursor):

    cursor.execute(
        """
        SELECT COUNT(*) FROM topics WHERE genre=? 
        AND is_used=0
        """,(genre,)
    )
    unused_count = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*) FROM topics WHERE genre=?
        """,(genre,)
    )
    total_count = cursor.fetchone()[0]

    if total_count==0 or unused_count <=3:
        cursor.execute(
            """
            SELECT topic FROM topics WHERE genre=?
            """,(genre,)
        )
        existing = [row[0] for row in cursor.fetchall()]

        new_topics = generate_topics(genre, existing)
        cursor.executemany(
            """
            INSERT OR IGNORE INTO topics (genre, topic)
            VALUES (?, ?)
            """,
            [(genre, t) for t in new_topics]
        )

def topic_selector(state: ShortsState) -> dict:
    genre = state['genre']

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    ensure_topice_pool(genre, cursor)

    cursor.execute(
        """
        SELECT id, topic FROM topics 
        WHERE genre=? AND is_used=0 
        ORDER BY created_at ASC LIMIT 1
        """,(genre,)
    )
    row = cursor.fetchone()
    if row is None:
        conn.close()
        raise Exception(f"No topics available for genre: {genre}")
    
    topic_id, topic = row

    cursor.execute(
        """
        UPDATE topics SET is_used=1 WHERE id=?
        """,(topic_id,)
    )

    conn.commit()
    conn.close()
    return {"topic": topic}