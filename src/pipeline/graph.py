from langgraph.graph import StateGraph, START, END
from ..state import ShortsState
from ..nodes.assembler import assembler
from ..nodes.email_approval import email_approval
from ..nodes.media_fetcher import media_fetcher
from ..nodes.publisher import publisher
from ..nodes.script_generator import script_generator
from ..nodes.topic_selector import topic_selector
from ..nodes.voice_generator import voice_generator
from .reviewer import reviewer


graph = StateGraph(ShortsState)

graph.add_node('topic_selector', topic_selector)
graph.add_node('script_generator', script_generator) #genrates both script and caption
graph.add_node('media_fetcher', media_fetcher)
graph.add_node('voice_generator', voice_generator)
graph.add_node('assembler', assembler)
graph.add_node('email_approval', email_approval)
graph.add_node('publisher', publisher)

graph.add_edge(START, 'topic_selector')
graph.add_edge('topic_selector', 'script_generator')
graph.add_edge('script_generator', 'media_fetcher')
graph.add_edge('media_fetcher', 'voice_generator')
graph.add_edge('voice_generator', 'assembler')
graph.add_edge('assembler', 'email_approval')
graph.add_conditional_edges('email_approval', reviewer, {
    'no_review': 'publisher',
    'script_change': 'script_generator',
    'media_change': 'media_fetcher',
    'both_change': 'script_generator'
})

graph.add_edge('publisher', END)