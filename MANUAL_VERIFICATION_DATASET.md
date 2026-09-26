# UI/UX Manual Verification Dataset

## Quick Reference for Manual Testing

Use this checklist to manually verify all UI/UX enhancements are working correctly in the live application.

---

## 1. HOME PAGE

### Visual Elements
- [ ] Four-step workflow cards visible (Prepare → Explore → Experiment → Deploy)
- [ ] Step cards have borders and clear numbering (1-4)
- [ ] Project creation form on left side
- [ ] Project list on right side
- [ ] "Create & Select" button styled in primary color (indigo)

### Content & Interaction
- [ ] Hero subtitle: "Train, compare, and deploy ML models..."
- [ ] Create project form accepts name and description
- [ ] Submitting creates project and shows success message
- [ ] Project list shows: name, description, creation date
- [ ] "Activate" button changes active state
- [ ] Active project shows "✓ Active" indicator
- [ ] Workspace Activity section shows metrics (Datasets, Experiments, Completed Runs)
- [ ] Next-step guidance appears based on state:
  - No projects: "Create one to start building"
  - No datasets: "Start by opening **Datasets**..."
  - No experiments: "Your data is ready. Open **Explore**..."
  - Has experiments: Recent experiments table shown

---

## 2. DATASETS PAGE

### Visual Elements
- [ ] Page header: "Dataset Workspace"
- [ ] Subtitle explains purpose
- [ ] Active dataset selector at top (shows current dataset)
- [ ] Three tabs: Upload CSV, Load Demo, Existing Datasets
- [ ] Dataset profile shows: name, source, creation date
- [ ] Dataset profile details expandable ("Dataset details" section)

### Upload Workflow
- [ ] Upload tab visible with file uploader
- [ ] Help text shows upload limits (reads from config: max_upload_mib, max_rows, max_columns)
- [ ] Dataset name field visible
- [ ] "Validate & Ingest Dataset" button disabled until file selected
- [ ] Validation spinner appears during processing
- [ ] Success message shows: row count, column count

### Demo Datasets
- [ ] Demo option selector works
- [ ] Seed input with default value 42
- [ ] "Load Demo into Project" button
- [ ] Demo loads without network call (offline)

### Profile Display
- [ ] Profile shows 4 metric cards: Rows, Columns, Duplicates, Memory Size
- [ ] Column schema table shows:
  - Column Name
  - Inferred Type
  - Suggested Role
  - Missing Count (with percentage)
  - Unique Values
  - Sample Values
- [ ] Quality warnings appear (if any) in expandable section

---

## 3. EXPLORE PAGE

### Visual Elements
- [ ] Page header: "Exploratory Data Analysis & Split Preparation"
- [ ] Scope header: "**Dataset:** [name] | **Rows:** [count] | **Columns:** [count]"
- [ ] Dataset selector at top (shows active dataset)

### Section 1: Modeling Protocol
- [ ] "1. Modeling Protocol Setup" heading
- [ ] Task selector: Classification vs Regression
- [ ] Target column selector (auto-detects common names like "target", "label", "species")
- [ ] Numeric Features multiselect
- [ ] Categorical Features multiselect

### Section 2: Split Configuration
- [ ] "2. Leakage-Guarded Split Configuration" heading
- [ ] Holdout Fraction selector with format: "20% Holdout (Sequestered)"
- [ ] Help text visible on hover (e.g., "20% = 150 rows withheld...")
- [ ] Cross-Validation Folds selector
- [ ] Random Split Seed input with help text
- [ ] "Prepare Verified Split & Generate Development EDA" button

### Results Display
- [ ] Scope header shows: "**Dataset:** [name] | **Task:** [Classification/Regression] | **Target:** `[column]` | **Development rows:** [count]"
- [ ] "Development Data Exploratory Analysis" heading
- [ ] Leakage warning displayed (🔒 icon + explanation)
- [ ] Target distribution chart:
  - For classification: bar chart of class frequencies
  - For regression: histogram of target values
  - Chart title includes "(N=X)" where X is development row count
- [ ] Numeric features distribution:
  - Histogram for each numeric feature
  - X-axis: feature range
  - Y-axis: frequency
- [ ] Correlation heatmap:
  - Shows numeric features correlation
  - "Numeric Correlation (Development Rows)" title
  - Values printed on heatmap
  - Non-causal disclaimer visible

---

## 4. EXPERIMENTS PAGE

### Visual Elements
- [ ] Page header: "Supervised Experiments"
- [ ] Scope section at top (if experiment exists)
- [ ] Form controls grouped by intent:
  - Dataset & Target summary
  - Feature selection
  - Preprocessing options
  - Algorithm selection
  - Run action button

### Controls
- [ ] Dataset selector
- [ ] Target display (read-only from Explore or auto-detected)
- [ ] Feature numeric/categorical display
- [ ] CV Folds selector with help text
- [ ] Random Seed input with help text
- [ ] Algorithm multiselect (Logistic Regression, Decision Tree, Random Forest, etc.)
- [ ] "Run Supervised Experiments" button (primary color)

### Results Display
- [ ] Scope header: "**Dataset:** [name] | **Task:** [type] | **Target:** `[col]` | **Metric:** [metric]"
- [ ] "Latest Training Results" section with:
  - CV Mean and CV Std for each algorithm
  - Algorithm ranks by metric
  - Selection reason explanation
- [ ] Leaderboard table with columns:
  - Algorithm
  - CV Mean (precise decimals)
  - CV Std (±value format)
  - Folds
  - Fit Duration
- [ ] CV score visualization chart
- [ ] "Finalize Holdout Evaluation" section with warning

### History
- [ ] "Experiment History" section shows all runs
- [ ] Table columns: ID, Name, Task, Status, Champion, Primary Metric, Started, Finalized

---

## 5. COMPARE PAGE

### Visual Elements
- [ ] Page header: "Experiment Comparison"
- [ ] Scope header: "**Dataset:** [name] | **Task:** [type] | **Target:** `[col]` | **Metric:** [metric]"
- [ ] Experiment multiselect (requires min 2 selections)
- [ ] "📊 Compare Selected Experiments" button

### Results Display
- [ ] "Comparison Leaderboard" heading
- [ ] Leaderboard table with:
  - Experiment name with ID
  - Champion Algorithm
  - CV Mean (6 decimals)
  - CV Std (4 decimals, ±format)
  - Trial count
  - Total fit duration
  - Start timestamp
- [ ] Horizontal bar chart:
  - X-axis: CV Mean
  - Y-axis: Experiment names
  - Sorted by CV Mean (highest first/last based on metric direction)
  - Color gradient (Viridis scale)
  - Error bars showing CV Std
  - Title: "{Metric} Comparison (Sorted by Performance)"
- [ ] Configuration Differences table showing:
  - Experiment name
  - Algorithms used
  - Random seed
  - Preprocessing settings

---

## 6. PREDICT PAGE

### Visual Elements
- [ ] Page header: "Model Prediction"
- [ ] Champion model selector
- [ ] Model info: "✅ **Model loaded** — N input features..."
- [ ] Mode selector: Single Row vs Batch CSV

### Single Row Mode
- [ ] Feature input fields dynamically generated
- [ ] Numeric fields labeled "(numeric)"
- [ ] Categorical fields labeled "(text)"
- [ ] Form submits on "Predict Single Row" button
- [ ] Results show predictions + probabilities (if classification)

### Batch Mode
- [ ] CSV file uploader
- [ ] File preview shows first 5 rows
- [ ] Success message: "Loaded X rows × Y columns"
- [ ] "Run Batch Prediction" button (requires explicit click)
- [ ] Results table includes:
  - Original features
  - Predicted values
  - Prediction probabilities (if classification)
- [ ] CSV download button labeled "⬇️ Download Predictions as CSV"

---

## 7. CLUSTERING PAGE

### Visual Elements
- [ ] Page header: "Unsupervised Clustering Lab"
- [ ] Dataset selector
- [ ] Experiment name input
- [ ] Numeric features multiselect
- [ ] K slider (2-10)
- [ ] Random seed input
- [ ] "Run K-Means" button in form

### Results Display
- [ ] Cluster sizes bar chart
- [ ] PCA scatter plot with cluster colors
- [ ] Silhouette scores bar chart
- [ ] Elbow diagnostic (inertia vs k)
- [ ] Metrics table showing:
  - K value
  - Inertia
  - Silhouette score
  - Cluster sizes

---

## 8. SIDEBAR NAVIGATION

### Visual Elements
- [ ] Brand mark: "DM" in colored box (gradient)
- [ ] Brand name: "DataMind"
- [ ] Brand copy: "Interactive machine learning workspace"
- [ ] "Current workspace" section with project selector
- [ ] Active dataset badge: "Active dataset: [name]"
- [ ] "Workflow" section showing: "Workspace → Prepare → Model → Deliver → Learn"
- [ ] Navigation radio buttons for all 9 pages
- [ ] Runtime status: green dot + "Local runtime · 127.0.0.1"

### Colors & Styling
- [ ] Primary color (indigo #4f46e5) on buttons and active states
- [ ] Border colors (#dde2ea) on cards and dividers
- [ ] Text color (#172033) readable on white
- [ ] Muted text color (#5f6b7a) for secondary info

---

## 9. RESPONSIVE LAYOUT

### Mobile (375px)
- [ ] Single column layout
- [ ] Buttons full-width
- [ ] Form inputs stack vertically
- [ ] Charts responsive
- [ ] Text readable without zoom

### Tablet (768px)
- [ ] Two-column layouts work
- [ ] Project panels side-by-side
- [ ] Charts display correctly

### Laptop (1024px–1440px)
- [ ] Three-column layouts work
- [ ] Max width enforced (1440px)
- [ ] Sidebar visible
- [ ] All interactive elements accessible

---

## 10. KEYBOARD & ACCESSIBILITY

### Keyboard Navigation
- [ ] Tab through all interactive elements in logical order
- [ ] Focus visible (3px outline) on every button, input, selectbox
- [ ] Enter/Space activates buttons
- [ ] Arrows navigate dropdowns
- [ ] All form submission works via keyboard

### Form Validation
- [ ] Required field shows error if empty
- [ ] Error message reads (role="alert" behavior)
- [ ] Input field stays focused after error
- [ ] Success message appears after valid submission

### Screen Reader
- [ ] Page title announced
- [ ] Headings announce hierarchy (H1→H2→H3)
- [ ] Form labels associated with inputs
- [ ] Buttons have descriptive text
- [ ] Charts have table alternatives below

---

## 11. COLOR & CONTRAST

### Primary Interaction
- [ ] Buttons: Indigo #4f46e5 on white = 6.5:1 contrast ✓
- [ ] Text: #172033 on white = 15:1 contrast ✓
- [ ] Muted text: #5f6b7a on white = 7.2:1 contrast ✓

### Error & Success States
- [ ] Error text: #b91c1c (red) readable
- [ ] Success icon: #15803d (green) with text label (not color alone)
- [ ] Warning: #b45309 (orange) with icon + text

---

## 12. INTERACTIVE ELEMENTS

### Buttons
- [ ] Primary buttons: Solid indigo background
- [ ] Buttons have hover state (darker color)
- [ ] Buttons have active/pressed state
- [ ] Disabled buttons appear faded
- [ ] Button text is always visible (not icon-only)

### Forms
- [ ] Labels visible above inputs
- [ ] Help text displays on hover/focus
- [ ] Multiselect shows clear selection count
- [ ] Selectbox shows current value
- [ ] Number inputs have spinner controls

### Cards
- [ ] Project cards have border
- [ ] Active project shows distinct styling
- [ ] Clickable cards have cursor-pointer
- [ ] Card hover state (subtle background change)

---

## Test Scenario Walkthrough

**Complete flow to manually verify all enhancements:**

1. **Start app** → Browser loads Home page
2. **Verify Home** → Four-step cards, project panels, guidance
3. **Create project** → Form validates, shows success
4. **Navigate to Datasets** → Load Iris demo dataset
5. **Navigate to Explore** → Select target, run split prep
6. **Verify Explore results** → Scope header, charts, table
7. **Navigate to Experiments** → Run ML training
8. **Verify Experiments results** → Scope header, leaderboard, CV chart
9. **Navigate to Compare** → Compare multiple runs
10. **Verify Compare results** → Sorted chart, error bars, table
11. **Navigate to Predict** → Make predictions
12. **Test keyboard nav** → Tab through all elements
13. **Test responsive** → Resize to 375px, 768px, 1440px
14. **Verify accessibility** → Color contrast, focus visibility

---

## Expected Results

✅ All pages render with consistent styling
✅ All interactive elements have visible focus
✅ All colors meet WCAG AA contrast (4.5:1 minimum)
✅ All text readable at 200% zoom
✅ All tables show precise numeric data
✅ All charts have meaningful titles and labels
✅ Scope headers visible on all analytical results
✅ Navigation workflow clear and consistent
✅ No layout shifts or truncation
✅ Responsive at 375px, 768px, 1024px, 1366px, 1440px

---

## Sign-Off

**Date Verified:** _________________

**Verified By:** _________________

**All Tests Passed:** ☐ Yes ☐ No

**Issues Found:** None / _________________

