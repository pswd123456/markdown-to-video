**Layout Plan**

- **Title**: "PDF to Semantic Chunks via Docling"  
  - **Region**: Top edge, centered  
  - **Relation**: Fixed with `to_edge(UP, buff=1.0)`, within SAFE ZONE Y ≤ 3.0

- **Node 1 (Start)**: PDF Icon  
  - **Region**: Top-Left (Start) → Approx. **[-4.0, 2.0]**  
  - **Relation**: First step in process; labeled “Complex PDF”

- **Node 2**: Tree Structure (Hierarchical Diagram)  
  - **Region**: Top-Right (Step 2) → Approx. **[4.0, 2.0]**  
  - **Relation**: Connected to Node 1 with a **straight rightward arrow**

- **Node 3**: Semantic Chunks (Group of colored rectangles, each labeled “语义切片”)  
  - **Region**: Bottom-Right (Step 3) → Approx. **[4.0, -2.0]**  
  - **Relation**: Connected to Node 2 with a **straight downward arrow**

- **Node 4**: Docling Logo  
  - **Region**: Bottom-Left (Step 4) → Approx. **[-4.0, -2.0]**  
  - **Relation**: Connected to Node 3 with a **straight leftward arrow**; optionally, a final arrow back to center or fade-out to imply output

> **All elements strictly within SAFE ZONE**: X ∈ [-6.0, 6.0], Y ∈ [-3.0, 3.0]  
> **Spacing**: ≥0.5 unit buffer between all nodes and arrows  
> **Style**: Rectangular bounding boxes for each node (even icons/logos placed inside clean rectangles), straight-line orthogonal arrows only  
> **Background**: Pure black