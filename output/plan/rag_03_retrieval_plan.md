**Layout Plan**

- **Title**: "Hybrid Search & Reranking Pipeline"  
  - **Region**: Top edge, centered  
  - **Relation**: `to_edge(UP, buff=1.0)`, within SAFE ZONE Y ≤ 3.0

- **Node 1 (Start)**: **Vector Icon** (Blue)  
  - **Region**: Top-Left (Start) → **X = -4.0, Y = 2.0**  
  - **Relation**: Rectangle labeled “Dense Vector”; will connect rightward

- **Node 2**: **BM25 Bubble** (Orange)  
  - **Region**: Top-Right (Step 2) → **X = 4.0, Y = 2.0**  
  - **Relation**: Rectangle labeled “Sparse BM25”; connected to Node 1 via **horizontal straight arrow** (left-to-right)

- **Node 3**: **Elasticsearch Core**  
  - **Region**: Center → **X = 0.0, Y = 0.0**  
  - **Relation**: Large central rectangle labeled “Elasticsearch”; receives **two vertical downward arrows** from Node 1 and Node 2 (straight lines from [-4.0, 2.0] → [0, 0] and [4.0, 2.0] → [0, 0] are *not allowed* per Flowchart Rules).  
    → **Correction per Flowchart Rules**: Must follow **TL → TR → BR → BL** path with only horizontal/vertical straight arrows.  
    → **Revised Structure**:  
      - After Node 2 (Top-Right), next node must be **Bottom-Right**.

- **Node 3 (Corrected)**: **RRF Bar**  
  - **Region**: Bottom-Right → **X = 4.0, Y = -2.0**  
  - **Relation**: Rectangle labeled “RRF Fusion”; connected **vertically down** from Node 2 ([4.0, 2.0] → [4.0, -2.0]) with straight arrow

- **Node 4**: **TEI Model**  
  - **Region**: Bottom-Left → **X = -4.0, Y = -2.0**  
  - **Relation**: Rectangle labeled “TEI Reranker”; connected **horizontally left** from Node 3 ([4.0, -2.0] → [-4.0, -2.0]) with straight arrow

- **Final Output**: **“高精度结果”**  
  - **Region**: Below Node 4, but within SAFE ZONE → **X = -4.0, Y = -3.0**  
  - **Relation**: Rectangle labeled “高精度结果” (highlighted); connected **vertically down** from Node 4 ([-4.0, -2.0] → [-4.0, -3.0])

- **Elasticsearch Integration Note**:  
  To comply with flowchart rules, the **fusion in Elasticsearch is abstracted as the transition from Node 1 + Node 2 into the RRF step**. The central Elasticsearch icon is **not a process node** but a **background visual motif** placed at center [0,0] **behind** the flow, *not* as a connected box. It serves as contextual decoration only—**no arrows connect to/from it**, preserving the strict rectangular flow.

- **All Coordinates**: Confirmed within SAFE ZONE (X ∈ [-6,6], Y ∈ [-3,3])  
- **Buffer Compliance**: ≥0.5 units between all elements  
- **Background**: BLACK