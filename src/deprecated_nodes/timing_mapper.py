from state import ShortsState
import json

def group_words_into_sentences(words):
    sentences = []
    current = []

    for w in words:
        current.append(w)
        if w["word"].endswith((".", "?", "!")):
            sentences.append(current)
            current = []

    if current:
        sentences.append(current)

    return sentences

def sentence_to_timing(sentence):
    start = sentence[0]["start"]
    end = sentence[-1]["start"] + sentence[-1]["duration"]
    return {
        "text": " ".join([w["word"] for w in sentence]),
        "start": start,
        "duration": end - start
    }

def timing_mapper(state: ShortsState):
    with open(state["subtitle_path"], "r") as f:
        words = json.load(f)

    sentences = group_words_into_sentences(words)
    timed_sentences = [sentence_to_timing(s) for s in sentences]

    return {"timed_sentences": timed_sentences}