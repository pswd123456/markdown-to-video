from manim import *

class rag_06_conclusion(Scene):
    def construct(self):
        # === 1. Title ===
        title = Text("参考与实践", font="Noto Sans CJK SC", font_size=48, color=BLUE)
        title.to_edge(UP, buff=1.0)
        
        # === 2. Developer Silhouette (Center Anchor) ===
        silhouette_circle = Circle(radius=0.8, color=WHITE, fill_opacity=0)
        dev_label = Text("开发者", font="Noto Sans CJK SC", font_size=36, color=WHITE)
        dev_label.move_to(silhouette_circle.get_center())
        silhouette = VGroup(silhouette_circle, dev_label)
        silhouette.move_to(ORIGIN)

        # === 3. Flowchart Nodes (Rectangles) ===
        node_width, node_height = 2.4, 1.2

        # Node 1: RAG Diagram (Top-Left)
        node1 = RoundedRectangle(corner_radius=0.2, width=node_width, height=node_height, color=BLUE)
        label1 = Text("RAG 架构图", font="Noto Sans CJK SC", font_size=28, color=WHITE)
        label1.move_to(node1.get_center())
        node1_group = VGroup(node1, label1)
        node1_group.move_to([-4.0, 2.0, 0])

        # Node 2: Code Snippet (Top-Right)
        node2 = RoundedRectangle(corner_radius=0.2, width=node_width, height=node_height, color=TEAL)
        label2 = Text("工程代码", font="Noto Sans CJK SC", font_size=28, color=WHITE)
        label2.move_to(node2.get_center())
        node2_group = VGroup(node2, label2)
        node2_group.move_to([4.0, 2.0, 0])

        # Node 3: Metrics Panel (Bottom-Right)
        node3 = RoundedRectangle(corner_radius=0.2, width=node_width, height=node_height, color=PURPLE)
        label3 = Text("评估指标", font="Noto Sans CJK SC", font_size=28, color=WHITE)
        label3.move_to(node3.get_center())
        node3_group = VGroup(node3, label3)
        node3_group.move_to([4.0, -2.0, 0])

        # Node 4: Checkmark (Bottom-Left) - Use WHITE for better contrast
        node4 = RoundedRectangle(corner_radius=0.2, width=node_width, height=node_height, color=GREEN)
        checkmark = Text("✓", font="Noto Sans CJK SC", font_size=60, color=WHITE)
        checkmark.move_to(node4.get_center())
        node4_group = VGroup(node4, checkmark)
        node4_group.move_to([-4.0, -2.0, 0])

        # === 4. Arrows (Straight, Axis-Aligned) ===
        arrow1 = Arrow(
            start=node1_group.get_right(),
            end=node2_group.get_left(),
            color=WHITE,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.1
        )
        arrow2 = Arrow(
            start=node2_group.get_bottom(),
            end=node3_group.get_top(),
            color=WHITE,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.1
        )
        arrow3 = Arrow(
            start=node3_group.get_left(),
            end=node4_group.get_right(),
            color=WHITE,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.1
        )

        # === 5. Animation Sequence ===
        self.play(Write(title), run_time=0.8)
        self.wait(0.2)

        self.play(FadeIn(silhouette, scale=0.8), run_time=0.7)
        self.wait(0.3)

        self.play(FadeIn(node1_group, shift=DOWN), run_time=0.6)
        self.wait(0.2)

        self.play(GrowArrow(arrow1), run_time=0.5)
        self.play(FadeIn(node2_group, shift=DOWN), run_time=0.6)
        self.wait(0.2)

        self.play(GrowArrow(arrow2), run_time=0.5)
        self.play(FadeIn(node3_group, shift=UP), run_time=0.6)
        self.wait(0.2)

        self.play(GrowArrow(arrow3), run_time=0.5)
        self.play(FadeIn(node4_group, shift=UP), run_time=0.6)
        self.wait(0.5)

        # === 6. Final Focus Transition ===
        big_check = Text("✓", font="Noto Sans CJK SC", font_size=200, color=GREEN)
        big_check.move_to(silhouette.get_center())  # Fully opaque by default

        background_elements = VGroup(silhouette, node1_group, node2_group, node3_group, node4_group, arrow1, arrow2, arrow3)
        self.play(
            FadeOut(background_elements, run_time=1.0),
            FadeIn(big_check, run_time=1.0)
        )
        self.wait(1.0)