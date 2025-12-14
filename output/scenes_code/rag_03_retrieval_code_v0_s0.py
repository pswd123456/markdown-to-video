from manim import *

class rag_03_retrieval(Scene):
    def construct(self):
        # Set background color
        self.camera.background_color = BLACK

        # 1. Title
        title = Text("Hybrid Search & Reranking Pipeline", font="Noto Sans CJK SC", font_size=36, color=WHITE)
        title.to_edge(UP, buff=1.0)
        self.play(Write(title))
        self.wait(0.5)

        # 2. Define Nodes with consistent styling
        node_style = {"width": 2.8, "height": 1.0, "stroke_width": 2}
        text_style = {"font": "Noto Sans CJK SC", "font_size": 24}

        # Node 1: Vector Icon (Top-Left)
        vector_rect = Rectangle(color=BLUE, **node_style).move_to([-4.0, 2.0, 0])
        vector_label = Text("Dense Vector", **text_style, color=BLUE).move_to(vector_rect.get_center())
        vector_group = VGroup(vector_rect, vector_label)

        # Node 2: BM25 Bubble (Top-Right)
        bm25_rect = Rectangle(color=ORANGE, **node_style).move_to([4.0, 2.0, 0])
        bm25_label = Text("Sparse BM25", **text_style, color=ORANGE).move_to(bm25_rect.get_center())
        bm25_group = VGroup(bm25_rect, bm25_label)

        # Node 3: RRF Bar (Bottom-Right)
        rrf_rect = Rectangle(color=GOLD, **node_style).move_to([4.0, -2.0, 0])
        rrf_label = Text("RRF Fusion", **text_style, color=GOLD).move_to(rrf_rect.get_center())
        rrf_group = VGroup(rrf_rect, rrf_label)

        # Node 4: TEI Model (Bottom-Left)
        tei_rect = Rectangle(color=TEAL, **node_style).move_to([-4.0, -2.0, 0])
        tei_label = Text("TEI Reranker", **text_style, color=TEAL).move_to(tei_rect.get_center())
        tei_group = VGroup(tei_rect, tei_label)

        # Final Output: 高精度结果 (Below TEI)
        result_rect = Rectangle(color=PURPLE, width=2.8, height=1.0, stroke_width=3, fill_opacity=0.2, fill_color=PURPLE).move_to([-4.0, -3.0, 0])
        result_label = Text("高精度结果", font="Noto Sans CJK SC", font_size=24, color=PURPLE).move_to(result_rect.get_center())
        result_group = VGroup(result_rect, result_label)

        # Elasticsearch Background Motif (Center, behind flow)
        es_circle = Circle(radius=1.8, color=GREY, stroke_width=1.5, fill_opacity=0.05, fill_color=GREY).move_to(ORIGIN)
        es_text = Text("Elasticsearch", font="Noto Sans CJK SC", font_size=28, color=GREY).move_to(ORIGIN)
        es_group = VGroup(es_circle, es_text)
        es_group.set_z_index(-1)  # Ensure it's in the background

        # 3. Create Arrows (only horizontal/vertical segments)
        # Arrow 1: Vector → BM25 (Top row, left to right)
        arrow1 = Arrow(
            start=vector_rect.get_right(),
            end=bm25_rect.get_left(),
            buff=0.1,
            color=WHITE,
            stroke_width=3,
            max_tip_length_to_length_ratio=0.1
        )

        # Arrow 2: BM25 → RRF (Right column, top to bottom)
        arrow2 = Arrow(
            start=bm25_rect.get_bottom(),
            end=rrf_rect.get_top(),
            buff=0.1,
            color=WHITE,
            stroke_width=3,
            max_tip_length_to_length_ratio=0.1
        )

        # Arrow 3: RRF → TEI (Bottom row, right to left)
        arrow3 = Arrow(
            start=rrf_rect.get_left(),
            end=tei_rect.get_right(),
            buff=0.1,
            color=WHITE,
            stroke_width=3,
            max_tip_length_to_length_ratio=0.1
        )

        # Arrow 4: TEI → Result (Left column, top to bottom)
        arrow4 = Arrow(
            start=tei_rect.get_bottom(),
            end=result_rect.get_top(),
            buff=0.1,
            color=WHITE,
            stroke_width=3,
            max_tip_length_to_length_ratio=0.1
        )

        # 4. Animation Sequence (Total ~11.38s)
        # Show Elasticsearch background
        self.play(FadeIn(es_group, run_time=0.8))
        self.wait(0.2)

        # Show input nodes
        self.play(FadeIn(vector_group, shift=DOWN, run_time=0.9))
        self.play(FadeIn(bm25_group, shift=DOWN, run_time=0.9))
        self.wait(0.3)

        # Connect Vector → BM25
        self.play(GrowArrow(arrow1, run_time=0.7))
        self.wait(0.3)

        # Show RRF and connect BM25 → RRF
        self.play(FadeIn(rrf_group, shift=UP, run_time=0.9))
        self.play(GrowArrow(arrow2, run_time=0.7))
        self.wait(0.3)

        # Show TEI and connect RRF → TEI
        self.play(FadeIn(tei_group, shift=RIGHT, run_time=0.9))
        self.play(GrowArrow(arrow3, run_time=0.7))
        self.wait(0.3)

        # Show final result and connect TEI → Result
        self.play(FadeIn(result_group, shift=UP, run_time=0.9))
        self.play(GrowArrow(arrow4, run_time=0.7))
        self.wait(0.8)

        # Total timing check: 
        # 0.8+0.2 + 0.9+0.9+0.3 + 0.7+0.3 + 0.9+0.7+0.3 + 0.9+0.7+0.8 ≈ 11.3s