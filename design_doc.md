# UI/UX Redesign Plan for Laptop Recommender System

## 1. Overview
The goal is to enhance the user experience of the Laptop Recommender System by replacing all native `<select>` elements with interactive, card-style options, expanding the multi-step wizard, and redesigning the results screen. The existing stack (HTML/CSS/JS with Flask backend) will be preserved.

## 2. Multi-Step Wizard Architecture

The wizard will be expanded from 4 steps to 7 steps to gather richer signals while keeping each screen simple and focused.

### Step 1: Primary Use Case
- **Question:** What will you use it for?
- **UI:** 4 large card-style options (General, Work, Gaming, Creation) with icons and descriptions.
- **Interaction:** Single selection. Auto-advance on click.

### Step 2: Budget Range
- **Question:** What is your maximum budget?
- **UI:** Interactive slider with a live-updating number display.
- **Interaction:** Slider drag. "Continue" button to advance.

### Step 3: Screen Size Preference
- **Question:** What screen size do you prefer?
- **UI:** 3 clickable chips/cards (13-14" Portable, 15-16" Standard, 17"+ Large).
- **Interaction:** Single selection. Auto-advance on click.

### Step 4: Portability Importance
- **Question:** How important is portability?
- **UI:** 3 clickable cards (Ultra Light, Balanced, Desktop Replacement).
- **Interaction:** Single selection. Auto-advance on click.

### Step 5: Performance Need
- **Question:** How much power do you need?
- **UI:** 3 clickable cards (Entry Level, Balanced, Powerhouse).
- **Interaction:** Single selection. Auto-advance on click.

### Step 6: OS Preference (New - UI Only)
- **Question:** Do you have an OS preference?
- **UI:** 3 clickable cards (Windows, macOS, No Preference).
- **Interaction:** Single selection. Auto-advance on click.
- *Note: This will be mapped to the "Brand" preference in the backend (macOS -> Apple, Windows -> Any non-Apple).*

### Step 7: Brand Preferences (Expanded)
- **Question:** Any specific brand preferences?
- **UI:** Multi-select chips for brands (Apple, ASUS, Lenovo, HP, Dell, Acer, MSI, Razer, Any).
- **Interaction:** Multi-selection. "Generate Recommendations" button to submit.

## 3. Component System

### Card Selectors
- **Structure:** `<label class="option-card"><input type="radio" class="hidden"><div class="card-content">...</div></label>`
- **Styling:** Border highlights, background color changes, and subtle scaling on hover/selection.

### Budget Slider
- **Structure:** `<input type="range" class="budget-slider">` with a dynamic `<output>` element.
- **Styling:** Custom track and thumb styling to match the primary theme color.

### Progress Bar
- **Structure:** `<div class="progress-bar"><div class="progress" style="width: X%"></div></div>`
- **Styling:** Smooth width transitions.

## 4. Results Screen Redesign

### Match Cards
- **Layout:** Grid layout for multiple recommendations.
- **Content:** Laptop image, brand, model, key specs (CPU, GPU, RAM, Storage, Screen).
- **New Elements:**
  - **Match Score:** A visual indicator (e.g., "95% Match") calculated based on the synthetic rating logic (if possible to extract, otherwise a simulated score based on rank).
  - **Why Picked:** The existing `reasoning` field displayed prominently.
  - **Compare Button:** A button to open a modal or side-by-side view (optional enhancement).

### Loading State
- **UI:** A full-screen or section-level overlay with a spinner and animated text ("Analyzing the market...", "Finding your best match...").

## 5. Implementation Steps
1. **HTML:** Update `index.html` to include the new steps and UI elements.
2. **CSS:** Add styles for the slider, chips, new card layouts, and loading animations in `style.css`.
3. **JS:** Update `main.js` to handle the expanded step logic, slider updates, multi-select chips, and the new results rendering.
4. **Backend:** Ensure the payload sent to `/api/recommend` matches the expected schema, mapping new UI inputs (like OS preference) to existing backend fields (like Brand).
