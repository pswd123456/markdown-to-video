**Layout Plan**

- **Title Text ("RAG Practice")**:  
  - **Region**: Top Edge (Centered)  
  - **Position**: `to_edge(UP, buff=1.0)` → Y ≈ 3.0  
  - **Style**: Glowing white text, centered at X=0  

- **Subtitle Text ("全栈工程实践项目")**:  
  - **Region**: Upper-Center (Below Title)  
  - **Position**: Directly below title with `buff=0.6` → Y ≈ 2.2  
  - **Style**: Smaller, non-glowing white text, centered at X=0  

- **Step 1 – "理论" (Theory)**:  
  - **Region**: Top-Left (Start of flow)  
  - **Position**: X = -4.5, Y = 1.0  
  - **Shape**: Rectangle (box) with white border, black fill, white text  
  - **Relation**: —  

- **Step 2 – "生产级代码" (Production Code)**:  
  - **Region**: Top-Right (Step 2)  
  - **Position**: X = +4.5, Y = 1.0  
  - **Shape**: Rectangle (box), styled identically to Step 1  
  - **Relation**: Connected to Step 1 with a **straight horizontal arrow** pointing Right  

- **Arrow Connectors**:  
  - **Type**: Straight-line arrows (→)  
  - **Path**: From center-right edge of "理论" box to center-left edge of "生产级代码" box  
  - **Y-level**: Horizontal at Y = 1.0  

- **Code Background**:  
  - **Region**: Full canvas background  
  - **Style**: Animated dark background with subtle flowing code glyphs  
  - **Constraint**: Must not interfere with readability; all text/boxes remain legible against it  

> ✅ All critical elements are within SAFE ZONE (X ∈ [−6.0, 6.0], Y ∈ [−3.0, 3.0]).  
> ✅ Flow follows TL → TR path per Flowchart Rules.  
> ✅ Buffers ≥ 0.5 units maintained between title, subtitle, and top boxes.  
> ✅ Background is BLACK with dynamic code—compliant.