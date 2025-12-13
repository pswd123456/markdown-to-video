
from manim import *

class TestCircle(Scene):
    def construct(self):
        c = Circle(color=RED)
        t = Text("Docker Test").next_to(c, UP)
        self.add(c, t)
        self.wait(1)
