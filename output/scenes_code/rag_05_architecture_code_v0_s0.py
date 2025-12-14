from manim import *

class rag_05_architecture(Scene):
    def construct(self):
        # Set background color
        self.camera.background_color = BLACK

        # 1. Title
        title = Text("一键部署架构联动流程", font="Noto Sans CJK SC", font_size=42, color=YELLOW)
        title.to_edge(UP, buff=1.0)
        self.play(Write(title))
        self.wait(0.5)

        # 2. Create Nodes (Rectangles with centered text)
        def create_node(text, width=3.0, height=1.0, color=WHITE):
            rect = RoundedRectangle(corner_radius=0.2, width=width, height=height, color=color, stroke_width=2)
            label = Text(text, font="Noto Sans CJK SC", font_size=28, color=WHITE)
            label.move_to(rect.get_center())
            return VGroup(rect, label)

        docker = create_node("Docker", color=BLUE)
        redis = create_node("Redis Queue", color=RED)
        index = create_node("Parent-Child\nIndex", color=GREEN)
        auth = create_node("Auth Lock", color=PURPLE)
        fastapi = create_node("FastAPI\n(Backend)", color=TEAL)
        nextjs = create_node("Next.js\n(Frontend)", color=ORANGE)

        # 3. Position Nodes as per layout plan
        docker.move_to([-4.0, 2.0, 0])
        redis.move_to([4.0, 2.0, 0])
        index.move_to([4.0, -2.0, 0])
        auth.move_to([-4.0, -2.0, 0])
        fastapi.move_to([-2.0, -3.0, 0])
        nextjs.move_to([2.0, -3.0, 0])

        # 4. Create Arrows (only horizontal/vertical)
        arrow1 = Arrow(docker.get_right(), redis.get_left(), buff=0.1, color=WHITE)
        arrow2 = Arrow(redis.get_bottom(), index.get_top(), buff=0.1, color=WHITE)
        arrow3 = Arrow(index.get_left(), auth.get_right(), buff=0.1, color=WHITE)
        arrow4 = Arrow(auth.get_bottom(), fastapi.get_top(), buff=0.1, color=WHITE)
        arrow5 = Arrow(index.get_bottom(), nextjs.get_top(), buff=0.1, color=WHITE)

        # 5. Add all elements to scene
        nodes = VGroup(docker, redis, index, auth, fastapi, nextjs)
        arrows = VGroup(arrow1, arrow2, arrow3, arrow4, arrow5)
        self.play(
            FadeIn(nodes, lag_ratio=0.1),
            Create(arrows, lag_ratio=0.1),
            run_time=1.5
        )
        self.wait(0.5)

        # 6. Animation Sequence: Pulse Docker, then sequential highlight
        # Pulse Docker
        self.play(
            Indicate(docker, color=BLUE, scale_factor=1.1, run_time=0.8)
        )

        # Highlight path: Docker → Redis
        self.play(
            Indicate(redis, color=RED, scale_factor=1.05, run_time=0.6),
            ShowPassingFlash(arrow1.copy().set_color(YELLOW).set_stroke(width=6), time_width=0.8)
        )

        # Redis → Index
        self.play(
            Indicate(index, color=GREEN, scale_factor=1.05, run_time=0.6),
            ShowPassingFlash(arrow2.copy().set_color(YELLOW).set_stroke(width=6), time_width=0.8)
        )

        # Index → Auth
        self.play(
            Indicate(auth, color=PURPLE, scale_factor=1.05, run_time=0.6),
            ShowPassingFlash(arrow3.copy().set_color(YELLOW).set_stroke(width=6), time_width=0.8)
        )

        # Auth → FastAPI & Index → Next.js (simultaneously)
        self.play(
            Indicate(fastapi, color=TEAL, scale_factor=1.05, run_time=0.7),
            Indicate(nextjs, color=ORANGE, scale_factor=1.05, run_time=0.7),
            ShowPassingFlash(arrow4.copy().set_color(YELLOW).set_stroke(width=6), time_width=0.9),
            ShowPassingFlash(arrow5.copy().set_color(YELLOW).set_stroke(width=6), time_width=0.9)
        )

        self.wait(1.0)