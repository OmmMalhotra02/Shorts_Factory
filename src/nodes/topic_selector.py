from ..state import ShortsState
import sqlite3
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()

DB_PATH = Path(__file__).parent.parent.parent / "db" / "topics.db"
llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash-lite')

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
        Return a clean numbered list only. No headers, no explanations, no extra text.
        1. Topic here
        2. Topic here
        """
    resp = llm.invoke(prompt).content
    lines = resp.strip().split('\n')
    topics = []
    for line in lines:
        line = line.strip()
        if line:
            # remove numbering like "1. " or "1) "
            if line[0].isdigit():
                line = line.split('.', 1)[-1].strip()
                line = line.split(')', 1)[-1].strip()
            topics.append(line)
    return topics

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