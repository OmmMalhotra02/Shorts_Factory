from state import ShortsState
import sqlite3
from typing import List, Tuple
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

DB_PATH = Path(__file__).parent.parent.parent / "db" / "topics.db"

llm = ChatOpenAI(
    model="nvidia/nemotron-3-super-120b-a12b:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_KEY")
)

# ---------- MODELS ----------

class TopicResponse(BaseModel):
    topics: List[str]

class ScoredTopic(BaseModel):
    topic: str
    virality_score: int

class ScoredTopicsResponse(BaseModel):
    topics: List[ScoredTopic]

# ---------- GENERATE + SCORE ----------

def generate_topics(genre: str, existing_topics: List[str]) -> List[Tuple[str, int]]:
    
    # -------- STEP 1: Generate Topics --------
    prompt = f"""
        You are a viral YouTube Shorts strategist school students.

        Generate exactly 20 HIGHLY engaging topics for: {genre}

        Each topic MUST:
        - Be directly from NCERT/CBSE curriculum for that class
        - Create curiosity
        - Start with a surprising or counterintuitive fact
        - Be explainable in 30 to 60 seconds
        - Be visually explainable
        - Feel like "I never knew this was in my textbook"

        Avoid these:
        {existing_topics[:30]}
        """

    llm_topics = llm.with_structured_output(TopicResponse)
    resp = llm_topics.invoke(prompt)
    topics = resp.topics

    # -------- STEP 2: Score Topics --------
    score_prompt = f"""
        Rate each topic from 1 to 10 for viral potential.

        Criteria:
        - Hook strength
        - Curiosity gap
        - Shareability
        - Visual potential

        Topics:
        {topics}

        Return JSON:
        topics: [{{"topic": "...", "virality_score": 8}}]
        """

    llm_scores = llm.with_structured_output(ScoredTopicsResponse)
    scored_resp = llm_scores.invoke(score_prompt)

    scored_topics = [
        (t.topic.strip().capitalize(), t.virality_score)
        for t in scored_resp.topics
        if t.virality_score >= 7
    ]

    # fallback if all filtered out
    if not scored_topics:
        scored_topics = [(t.strip().capitalize(), 5) for t in topics]

    return scored_topics

# ---------- DB MANAGEMENT ----------

def ensure_topic_pool(genre: str, cursor):

    cursor.execute("""
        SELECT COUNT(*) FROM topics 
        WHERE genre=? AND is_used=0
    """, (genre,))
    unused_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM topics 
        WHERE genre=?
    """, (genre,))
    total_count = cursor.fetchone()[0]

    if total_count == 0 or unused_count <= 3:
        cursor.execute("""
            SELECT topic FROM topics WHERE genre=?
        """, (genre,))
        existing = [row[0] for row in cursor.fetchall()]

        new_topics = generate_topics(genre, existing)

        cursor.executemany("""
            INSERT OR IGNORE INTO topics (genre, topic, virality_score)
            VALUES (?, ?, ?)
        """, [(genre, topic, score) for topic, score in new_topics])

# ---------- MAIN NODE ----------

def topic_selector(state: ShortsState) -> dict:
    genre = state['genre']

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # updated schema
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        genre TEXT NOT NULL,
        topic TEXT NOT NULL,
        is_used INTEGER DEFAULT 0,
        virality_score INTEGER DEFAULT 0,
        published_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    ensure_topic_pool(genre, cursor)

    # pick BEST topic, not oldest
    cursor.execute("""
        SELECT id, topic FROM topics
        WHERE genre=? AND is_used=0
        ORDER BY virality_score DESC, created_at DESC
        LIMIT 1
    """, (genre,))
    
    row = cursor.fetchone()

    if row is None:
        conn.close()
        raise Exception(f"No topics available for genre: {genre}")

    topic_id, topic = row

    cursor.execute("""
        UPDATE topics SET is_used=1 WHERE id=?
    """, (topic_id,))

    conn.commit()
    conn.close()

    return {"topic": topic}