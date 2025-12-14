**Layout Plan**

- **Title**: “参考与实践”  
  - **Region**: Top Edge (Y ≈ 3.5)  
  - **Relation**: Centered horizontally; placed with `to_edge(UP, buff=1.0)` to respect breathing room.

- **Core Concept – Developer Silhouette**:  
  - **Region**: Absolute Center [0, 0]  
  - **Relation**: Serves as visual anchor; all other modules orbit around it within SAFE ZONE.

- **Flowchart Nodes (Rectangles + Straight Arrows, Clockwise Snake Path)**:

  1. **Node 1 – RAG Diagram**  
     - **Region**: Top-Left (Start) → Approx. [-4.0, 2.0]  
     - **Relation**: Rectangle labeled “RAG 架构图”; no incoming arrow (start node).

  2. **Node 2 – Code Snippet**  
     - **Region**: Top-Right (Step 2) → Approx. [4.0, 2.0]  
     - **Relation**: Rectangle labeled “工程代码”; connected to Node 1 via **straight horizontal arrow (→)**.

  3. **Node 3 – Metrics Panel**  
     - **Region**: Bottom-Right (Step 3) → Approx. [4.0, -2.0]  
     - **Relation**: Rectangle labeled “评估指标”; connected to Node 2 via **straight vertical arrow (↓)**.

  4. **Node 4 – Checkmark (Final Symbol)**  
     - **Region**: Bottom-Left (Step 4) → Approx. [-4.0, -2.0]  
     - **Relation**: Rectangle containing a large **green checkmark icon**; connected to Node 3 via **straight horizontal arrow (←)**.  
     - **Note**: This node visually represents the culmination (“参考与实践” validated).

- **Final Focus Transition**:  
  - After layout is established, animation zooms/fades to center on **“参考与实践” title** while background behind silhouette transitions to display the green checkmark (matching Node 4’s icon), maintaining black background elsewhere.

- **Spacing & Safety**:  
  - All nodes kept within X: [-4.0, 4.0], Y: [-2.0, 2.0] → well inside SAFE ZONE [-6.0, 6.0] × [-3.0, 3.0].  
  - Minimum 0.5-unit buffer between silhouette and nearest node edges.  
  - Arrows are straight, axis-aligned, and unambiguous.  

✅ Layout complies with Flowchart Rules, Breathing Room, and Safe Zone constraints.