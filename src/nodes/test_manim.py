from manim import *

class TestScene(Scene):
    def construct(self):
        text = Text("Why is the sky blue?", color=BLUE)
        self.play(Write(text))
        self.wait(2)