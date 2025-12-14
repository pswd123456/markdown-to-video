**Layout Plan**

- **Title**: "一键部署架构联动流程"  
  - **Region**: Top edge, `to_edge(UP, buff=1.0)` → Y ≈ 3.0  
  - **Style**: Centered text within SAFE ZONE (X: [-6.0, 6.0])

> **Flowchart Path (Clockwise / Snake-like)** — All nodes as **rectangles**, connected by **straight arrows** (horizontal/vertical only), with ≥0.5 unit buffer.

- **Node 1: Docker（顶部触发器）**  
  - **Region**: Top-Left (Start) → Position: (-4.0, 2.0)  
  - **Note**: Represents the "一键部署" trigger; despite semantic top-center placement, adheres to flowchart start at TL per rules.

- **Node 2: Redis Queue**  
  - **Region**: Top-Right (Step 2) → Position: (4.0, 2.0)  
  - **Relation**: Connected to **Docker** with a **straight rightward arrow**

- **Node 3: Parent-Child Index**  
  - **Region**: Bottom-Right (Step 3) → Position: (4.0, -2.0)  
  - **Relation**: Connected to **Redis Queue** with a **straight downward arrow**

- **Node 4: Auth Lock**  
  - **Region**: Bottom-Left (Step 4) → Position: (-4.0, -2.0)  
  - **Relation**: Connected to **Parent-Child Index** with a **straight leftward arrow**

> **Bottom Dual Modules (Final Output Layer – Not in main 4-node cycle but visually grounded)**  
These are **not part of the 4-step flowchart cycle** but serve as terminal consumers; placed below Node 4 & 3 with vertical connections.

- **FastAPI (Backend)**  
  - **Region**: Bottom-Center-Left → Position: (-2.0, -3.0)  
  - **Relation**: Connected **vertically upward** to **Auth Lock** (Node 4)

- **Next.js (Frontend)**  
  - **Region**: Bottom-Center-Right → Position: (2.0, -3.0)  
  - **Relation**: Connected **vertically upward** to **Parent-Child Index** (Node 3)

> **Animation Note**: On trigger, Docker pulses → sequential highlight along arrows: Docker → Redis → Index → Auth Lock → both FastAPI & Next.js.

> **All coordinates respect SAFE ZONE**:  
> - X ∈ [-4.0, 4.0] ⊂ [-6.0, 6.0]  
> - Y ∈ [-3.0, 2.0] ⊂ [-3.0, 3.0]  
> - Minimum spacing = 2.0 units between adjacent nodes (>> 0.5 buffer)  
> - Background: BLACK