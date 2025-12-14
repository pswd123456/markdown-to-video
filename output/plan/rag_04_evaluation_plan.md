**Layout Plan**

- **Title**: Positioned at Top Edge (`to_edge(UP, buff=1.0)`), centered horizontally within SAFE ZONE.

- **Node 1 – Langfuse Trace (Top-Right / Step 1)**  
  - **Region**: Top-Right quadrant: approx. `[X=+4.5, Y=+2.5]`  
  - **Content**: Rectangle labeled “Langfuse Trace” with embedded flowchart (mini TL→TR→BR→BL trace inside, scaled to fit).  
  - **Note**: This is the *first* step in the clockwise process path per Flowchart Rules.

- **Node 2 – Ragas Dashboard (Bottom-Right / Step 2)**  
  - **Region**: Bottom-Right quadrant: approx. `[X=+4.5, Y=-2.5]`  
  - **Content**: Rectangle labeled “Ragas Dashboard”, showing metrics (Faithfulness, Answer Relevancy, etc.).  
  - **Relation**: Connected to Node 1 with a **straight vertical arrow pointing DOWN**.

- **Node 3 – Test Set Generator (Bottom-Left / Step 3)**  
  - **Region**: Bottom-Left quadrant: approx. `[X=-4.5, Y=-2.5]`  
  - **Content**: Rectangle labeled “Test Set Generator”, icon combo: gear + document.  
  - **Relation**: Connected to Node 2 with a **straight horizontal arrow pointing LEFT**.

- **Loop Closure (Back to Start)**  
  - **Connection**: From Node 3 (Bottom-Left) back to Node 1 (Top-Right) **is not allowed** under straight-line Flowchart Rules.  
  - **Resolution**: Insert **Node 4 – Implicit Feedback/Trigger (Top-Left / Step 4)** to complete the 4-node cycle:  
    - **Region**: Top-Left quadrant: approx. `[X=-4.5, Y=+2.5]`  
    - **Content**: Small rectangle labeled “Feedback Loop” or left minimal (transparent logic node).  
    - **Relations**:  
      - Connected from Node 3 via **straight vertical arrow UP**.  
      - Connected to Node 1 via **straight horizontal arrow RIGHT**.  

- **Loop Arrow Interpretation**: The full **clockwise rectangular loop** (Top-Left → Top-Right → Bottom-Right → Bottom-Left → Top-Left) is formed using **only straight arrows**, satisfying the Flowchart & Process Rules.

- **All Nodes**: Confined within SAFE ZONE (`|X| ≤ 6.0`, `|Y| ≤ 3.0`), with ≥0.5 unit buffer between elements and edges.  
- **Background**: Pure BLACK.