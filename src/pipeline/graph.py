from langgraph.graph import StateGraph, START, END
from state import ShortsState
from nodes.assembler import assembler
from nodes.email_approval import email_approval
# from nodes.media_fetcher import media_fetcher
from nodes.visual_brain import visual_brain
from nodes.image_generator import image_generator
from nodes.motion_generator import motion_generator
from nodes.scene_aligner import scene_duration_aligner
from nodes.timing_mapper import timing_mapper
from nodes.publisher import publisher
from nodes.script_generator import script_generator
from nodes.topic_selector import topic_selector
from nodes.voice_generator import voice_generator
from .reviewer import reviewer


graph = StateGraph(ShortsState)

graph.add_node('topic_selector', topic_selector)
graph.add_node('script_generator', script_generator) #genrates both script and caption
# graph.add_node('media_fetcher', media_fetcher)
graph.add_node('visual_brain', visual_brain)
graph.add_node('image_generator', image_generator)
graph.add_node('motion_generator', motion_generator)
graph.add_node('scene_duration_aligner', scene_duration_aligner)
graph.add_node('timing_mapper', timing_mapper)
graph.add_node('voice_generator', voice_generator)
graph.add_node('assembler', assembler)
graph.add_node('email_approval', email_approval)
graph.add_node('publisher', publisher)

graph.add_edge(START, 'topic_selector')
graph.add_edge('topic_selector', 'script_generator')
graph.add_edge('script_generator', 'visual_brain')
graph.add_edge('visual_brain', 'scene_duration_aligner')
graph.add_edge('scene_duration_aligner', 'image_generator')
graph.add_edge('image_generator', 'motion_generator')
# voice comes AFTER visuals are planned
graph.add_edge('motion_generator', 'voice_generator')
graph.add_edge('voice_generator', 'timing_mapper')
graph.add_edge('timing_mapper', 'assembler')
graph.add_edge('assembler', 'email_approval')
graph.add_conditional_edges('email_approval', reviewer, {
    'no_review': 'publisher',
    'skip': END,
    'script_change': 'script_generator',
    'media_change': 'visual_brain',
    'both_change': 'script_generator'
})

graph.add_edge('publisher', END)

workflow = graph.compile()