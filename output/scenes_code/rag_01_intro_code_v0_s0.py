from manim import *

class rag_01_intro(Scene):
    def construct(self):
        # === 1. Animated Code Background ===
        # Create a subtle, animated background of flowing code glyphs
        code_lines = VGroup()
        for i in range(30):
            line = Text(
                "import numpy as np\n" * 2,
                font="JetBrains Mono",
                font_size=18,
                color=GREY_D
            )
            line.shift(np.array([
                np.random.uniform(-7, 7),
                np.random.uniform(-4, 4),
                0
            ]))
            code_lines.add(line)
        
        # Animate background with slow fade-in and slight drift
        self.play(
            FadeIn(code_lines, run_time=2),
            rate_func=linear
        )
        # Keep background static after appearing (no distracting motion)

        # === 2. Title Text ===
        title = Text("RAG Practice", font="Noto Sans CJK SC", font_size=56, color=WHITE)
        title.to_edge(UP, buff=1.0)
        # Add subtle glow via outer stroke (Manim doesn't have true glow, so simulate with shadow)
        title_shadow = title.copy().set_color(BLUE_E).scale(1.02).set_z_index(-1)
        title_group = VGroup(title_shadow, title)

        # === 3. Subtitle Text ===
        subtitle = Text("全栈工程实践项目", font="Noto Sans CJK SC", font_size=36, color=WHITE)
        subtitle.next_to(title, DOWN, buff=0.6)

        # === 4. Step Boxes ===
        theory_box = Rectangle(
            width=2.0,
            height=1.0,
            color=WHITE,
            fill_color=BLACK,
            fill_opacity=1.0,
            stroke_width=2
        )
        theory_text = Text("理论", font="Noto Sans CJK SC", font_size=32, color=WHITE)
        theory_group = VGroup(theory_box, theory_text)
        theory_group.move_to(np.array([-4.5, 1.0, 0]))

        code_box = Rectangle(
            width=2.4,
            height=1.0,
            color=WHITE,
            fill_color=BLACK,
            fill_opacity=1.0,
            stroke_width=2
        )
        code_text = Text("生产级代码", font="Noto Sans CJK SC", font_size=28, color=WHITE)
        code_group = VGroup(code_box, code_text)
        code_group.move_to(np.array([4.5, 1.0, 0]))

        # === 5. Arrow Connector ===
        arrow = Arrow(
            start=theory_box.get_right(),
            end=code_box.get_left(),
            color=WHITE,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.08
        )

        # === 6. Animation Sequence ===
        # Show title with emphasis
        self.play(FadeIn(title_group, shift=DOWN * 0.3, run_time=1.2))
        self.play(FadeIn(subtitle, shift=UP * 0.2, run_time=0.8))
        self.wait(0.5)

        # Reveal flow elements
        self.play(FadeIn(theory_group, run_time=0.7))
        self.play(GrowArrow(arrow), run_time=1.0)
        self.play(FadeIn(code_group, run_time=0.7))
        self.wait(2.0)

        # Total duration: ~8.18s