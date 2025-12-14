from manim import *

class rag_04_evaluation(Scene):
    def construct(self):
        self.camera.background_color = BLACK

        # === Title ===
        title = Text("集成 Ragas 与 Langfuse", font="Noto Sans CJK SC", font_size=42, color=YELLOW)
        title.to_edge(UP, buff=1.0)
        self.play(Write(title))
        self.wait(0.5)

        # === Node Positions (Safe Zone Compliant) ===
        top_right = np.array([4.5, 2.5, 0])
        bottom_right = np.array([4.5, -2.5, 0])
        bottom_left = np.array([-4.5, -2.5, 0])
        top_left = np.array([-4.5, 2.5, 0])

        # === Node 1: Langfuse Trace (Top-Right) ===
        langfuse_rect = RoundedRectangle(corner_radius=0.2, width=3.0, height=1.8, color=BLUE, stroke_width=3)
        langfuse_rect.move_to(top_right)
        langfuse_label = Text("Langfuse Trace", font="Noto Sans CJK SC", font_size=28, color=WHITE)
        langfuse_label.next_to(langfuse_rect, UP, buff=0.1)

        # Mini trace inside: TL → TR → BR → BL (simplified as dots + lines)
        mini_scale = 0.4
        p1 = langfuse_rect.get_corner(UL) + RIGHT*0.3 + DOWN*0.3
        p2 = langfuse_rect.get_corner(UR) + LEFT*0.3 + DOWN*0.3
        p3 = langfuse_rect.get_corner(DR) + LEFT*0.3 + UP*0.3
        p4 = langfuse_rect.get_corner(DL) + RIGHT*0.3 + UP*0.3

        trace_dots = VGroup(*[Dot(point=p, radius=0.06, color=GOLD) for p in [p1, p2, p3, p4]])
        trace_lines = VGroup(
            Line(p1, p2, stroke_width=2, color=GOLD),
            Line(p2, p3, stroke_width=2, color=GOLD),
            Line(p3, p4, stroke_width=2, color=GOLD)
        )
        mini_trace = VGroup(trace_dots, trace_lines).scale(mini_scale).move_to(langfuse_rect.get_center())

        # === Node 2: Ragas Dashboard (Bottom-Right) ===
        ragas_rect = RoundedRectangle(corner_radius=0.2, width=3.0, height=1.8, color=GREEN, stroke_width=3)
        ragas_rect.move_to(bottom_right)
        ragas_label = Text("Ragas Dashboard", font="Noto Sans CJK SC", font_size=28, color=WHITE)
        ragas_label.next_to(ragas_rect, UP, buff=0.1)

        # Metrics list
        metrics = VGroup(
            Text("Faithfulness", font_size=20, color=WHITE),
            Text("Answer Relevancy", font_size=20, color=WHITE),
            Text("Context Recall", font_size=20, color=WHITE)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).next_to(ragas_rect, DOWN, buff=0.2)

        # === Node 3: Test Set Generator (Bottom-Left) ===
        testgen_rect = RoundedRectangle(corner_radius=0.2, width=3.0, height=1.8, color=PURPLE, stroke_width=3)
        testgen_rect.move_to(bottom_left)
        testgen_label = Text("Test Set Generator", font="Noto Sans CJK SC", font_size=28, color=WHITE)
        testgen_label.next_to(testgen_rect, UP, buff=0.1)

        # Gear + Document icon (simplified)
        gear = Circle(radius=0.3, color=WHITE).move_to(testgen_rect.get_center() + LEFT*0.5)
        doc = Rectangle(width=0.6, height=0.8, color=WHITE).move_to(testgen_rect.get_center() + RIGHT*0.5)
        doc.set_fill(WHITE, opacity=0.1)
        icons = VGroup(gear, doc)

        # === Node 4: Feedback Loop (Top-Left) ===
        feedback_rect = RoundedRectangle(corner_radius=0.15, width=2.2, height=1.2, color=GREY, stroke_width=2, fill_opacity=0.05)
        feedback_rect.move_to(top_left)
        feedback_label = Text("Feedback\nLoop", font="Noto Sans CJK SC", font_size=24, color=GREY_B)
        feedback_label.move_to(feedback_rect.get_center())

        # === Arrows (Straight, Clockwise) ===
        arrow1 = Arrow(
            start=feedback_rect.get_right(),
            end=langfuse_rect.get_left(),
            color=WHITE,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.1
        )
        arrow2 = Arrow(
            start=langfuse_rect.get_bottom(),
            end=ragas_rect.get_top(),
            color=WHITE,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.1
        )
        arrow3 = Arrow(
            start=ragas_rect.get_left(),
            end=testgen_rect.get_right(),
            color=WHITE,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.1
        )
        arrow4 = Arrow(
            start=testgen_rect.get_top(),
            end=feedback_rect.get_bottom(),
            color=WHITE,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.1
        )

        # === Assemble All Elements ===
        nodes = VGroup(
            langfuse_rect, langfuse_label, mini_trace,
            ragas_rect, ragas_label, metrics,
            testgen_rect, testgen_label, icons,
            feedback_rect, feedback_label
        )
        arrows = VGroup(arrow1, arrow2, arrow3, arrow4)

        # === Animation Sequence ===
        # Show nodes in clockwise order starting from Langfuse (Step 1)
        self.play(
            Create(langfuse_rect), Write(langfuse_label),
            FadeIn(mini_trace, scale=0.8)
        )
        self.wait(0.4)

        self.play(
            Create(ragas_rect), Write(ragas_label),
            FadeIn(metrics)
        )
        self.wait(0.4)

        self.play(
            Create(testgen_rect), Write(testgen_label),
            FadeIn(icons)
        )
        self.wait(0.4)

        self.play(
            Create(feedback_rect), Write(feedback_label)
        )
        self.wait(0.4)

        # Draw arrows to close the loop
        self.play(
            GrowArrow(arrow2),  # Langfuse → Ragas
            GrowArrow(arrow3),  # Ragas → TestGen
            GrowArrow(arrow4),  # TestGen → Feedback
            GrowArrow(arrow1)   # Feedback → Langfuse
        )
        self.wait(1.5)

        # Final highlight of the full loop
        loop_highlight = VGroup(arrows, nodes).copy()
        self.play(
            Indicate(VGroup(langfuse_rect, ragas_rect, testgen_rect, feedback_rect), color=YELLOW, scale_factor=1.03),
            run_time=1.2
        )
        self.wait(0.5)