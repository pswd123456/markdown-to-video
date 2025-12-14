from manim import *

class RAG02DataScene(Scene):
    def construct(self):
        # Set background to pure black
        self.camera.background_color = BLACK

        # 1. Title
        title = Text("PDF to Semantic Chunks via Docling", font="Noto Sans CJK SC", font_size=36, color=WHITE)
        title.to_edge(UP, buff=1.0)
        self.play(Write(title), run_time=1.0)

        # 2. Node 1: PDF Icon (represented as a labeled rectangle)
        pdf_label = Text("Complex PDF", font="Noto Sans CJK SC", font_size=24, color=WHITE)
        pdf_rect = Rectangle(width=2.0, height=1.2, color=BLUE).set_fill(BLUE, opacity=0.3)
        pdf_group = VGroup(pdf_rect, pdf_label)
        pdf_group.move_to([-4.0, 2.0, 0])
        self.play(Create(pdf_rect), Write(pdf_label), run_time=1.0)

        # 3. Node 2: Tree Structure (simplified hierarchical diagram)
        # Create a simple tree: root with two children
        root = Circle(radius=0.3, color=GREEN).set_fill(GREEN, opacity=0.5)
        child1 = Circle(radius=0.25, color=GREEN).set_fill(GREEN, opacity=0.4)
        child2 = Circle(radius=0.25, color=GREEN).set_fill(GREEN, opacity=0.4)
        
        root.move_to([4.0, 2.5, 0])
        child1.move_to([3.3, 1.8, 0])
        child2.move_to([4.7, 1.8, 0])
        
        line1 = Line(root.get_bottom(), child1.get_top(), color=GREEN)
        line2 = Line(root.get_bottom(), child2.get_top(), color=GREEN)
        
        tree_label = Text("层级结构", font="Noto Sans CJK SC", font_size=24, color=WHITE)
        tree_bounding = Rectangle(width=2.4, height=2.0, color=GREEN).set_fill(GREEN, opacity=0.15)
        tree_group = VGroup(tree_bounding, root, child1, child2, line1, line2, tree_label)
        tree_group.move_to([4.0, 2.0, 0])
        tree_label.next_to(tree_bounding, DOWN, buff=0.1)
        
        self.play(
            Create(tree_bounding),
            Create(root), Create(child1), Create(child2),
            Create(line1), Create(line2),
            Write(tree_label),
            run_time=1.5
        )

        # 4. Arrow from PDF to Tree
        arrow1 = Arrow(
            start=pdf_group.get_right(),
            end=tree_group.get_left(),
            color=WHITE,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.1
        )
        self.play(GrowArrow(arrow1), run_time=1.0)

        # 5. Node 3: Semantic Chunks (group of colored rectangles)
        chunk1 = Rectangle(width=1.4, height=0.6, color=YELLOW).set_fill(YELLOW, opacity=0.4)
        chunk2 = Rectangle(width=1.4, height=0.6, color=ORANGE).set_fill(ORANGE, opacity=0.4)
        chunk3 = Rectangle(width=1.4, height=0.6, color=PURPLE).set_fill(PURPLE, opacity=0.4)
        
        chunk_label1 = Text("语义切片", font="Noto Sans CJK SC", font_size=18, color=BLACK)
        chunk_label2 = Text("语义切片", font="Noto Sans CJK SC", font_size=18, color=BLACK)
        chunk_label3 = Text("语义切片", font="Noto Sans CJK SC", font_size=18, color=BLACK)
        
        c1 = VGroup(chunk1, chunk_label1).arrange(DOWN, buff=0.05)
        c2 = VGroup(chunk2, chunk_label2).arrange(DOWN, buff=0.05)
        c3 = VGroup(chunk3, chunk_label3).arrange(DOWN, buff=0.05)
        
        chunks_vgroup = VGroup(c1, c2, c3).arrange(DOWN, buff=0.4)
        chunks_bounding = SurroundingRectangle(chunks_vgroup, color=RED, buff=0.3, corner_radius=0.1)
        chunks_bounding.set_fill(RED, opacity=0.1)
        
        chunks_group = VGroup(chunks_bounding, chunks_vgroup)
        chunks_group.move_to([4.0, -2.0, 0])
        
        self.play(
            Create(chunks_bounding),
            FadeIn(c1, shift=UP),
            FadeIn(c2, shift=UP),
            FadeIn(c3, shift=UP),
            run_time=1.2
        )

        # 6. Arrow from Tree to Semantic Chunks (downward)
        arrow2 = Arrow(
            start=tree_group.get_bottom(),
            end=chunks_group.get_top(),
            color=WHITE,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.1
        )
        self.play(GrowArrow(arrow2), run_time=1.0)

        # 7. Node 4: Docling Logo (represented as labeled rectangle)
        docling_label = Text("Docling", font="Noto Sans CJK SC", font_size=28, color=WHITE)
        docling_rect = RoundedRectangle(width=2.0, height=1.2, corner_radius=0.2, color=GOLD)
        docling_rect.set_fill(GOLD, opacity=0.2)
        docling_group = VGroup(docling_rect, docling_label)
        docling_group.move_to([-4.0, -2.0, 0])
        
        self.play(Create(docling_rect), Write(docling_label), run_time=1.0)

        # 8. Arrow from Semantic Chunks to Docling (leftward)
        arrow3 = Arrow(
            start=chunks_group.get_left(),
            end=docling_group.get_right(),
            color=WHITE,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.1
        )
        self.play(GrowArrow(arrow3), run_time=1.0)

        # Optional: Final subtle highlight on Docling to imply processing engine
        self.play(Indicate(docling_group, color=GOLD, scale_factor=1.05, run_time=1.0))

        self.wait(0.5)  # Total duration ~9.06s