# PRD: tiktokchef (MVP)

## 1. Executive Summary

**tiktokchef** is a web-based "Recipe Vault" that allows users to convert short-form video URLs (TikTok, Reels, Shorts) into structured, editable digital recipe cards. The goal is to eliminate the need for users to manually pause and transcribe fast-paced cooking videos.

## 2. Target User

- The "FoodTok" enthusiast who saves hundreds of videos but never cooks them because the instructions are buried in captions or fast-cut edits.
- Home cooks who prefer a structured "Metric" ingredient list over "eyeballed" American measurements.

---

## 3. Functional Requirements

### 3.1 Core Extraction Engine

- **Input:** A single text input field for the video URL.
- **Processing:** \* System fetches video metadata (description, captions, transcript).
- **LLM Integration:** Pass metadata to an LLM (e.g., GPT-4o or Gemini Pro) to identify and separate:

1. **Recipe Title**
2. **Ingredient List** (with quantities)
3. **Step-by-Step Instructions**

- **Unit Conversion:** The system must automatically detect Imperial units (lbs, oz, cups) and convert them to Metric (g, ml, kg) as the default output.

### 3.2 The Digital Recipe Card (UX)

- **Preview Mode:** Before saving, display the extracted data in a clean, readable card format.
- **Inline Editing:** Every field (Title, Ingredients, Steps) must be interactive. Users can click to fix LLM "hallucinations" or add their own notes.
- **Original Source:** A permanent link back to the original TikTok video for reference.

### 3.3 The Digital Cookbook

- **Storage:** A "Library" view showing all previously extracted recipes.
- **Search/Filter:** Users can search their cookbook by title or ingredient.
- **Scaling:** A simple toggle or input to scale the recipe (e.g., 1x, 2x, 0.5x).

---

## 4. Technical Specifications (Web App)

| Component    | Recommendation                                                        |
| ------------ | --------------------------------------------------------------------- |
| **Frontend** | React or Next.js (Tailwind CSS for the "Recipe Card" UI)              |
| **Backend**  | Node.js (Python is also a strong choice for video scraping libraries) |
| **Database** | Supabase or MongoDB (to store the "Cookbook" JSON structures)         |
| **LLM**      | OpenAI API or Google Gemini API                                       |

---

## 5. Answers to your "Future" Questions

### How would the "Share to tiktokchef" extension look?

On a phone, it would live in the native **Share Sheet**.

1. User watches a TikTok → Clicks **Share**.
2. Selects the **tiktokchef icon**.
3. A small "overlay" or "drawer" pops up showing: _"Extracting recipe..."_ 4. It shows a success checkmark and a button: _"View in Cookbook."_

### The Multi-Video Shopping List

To achieve this in the MVP-plus stage, we would create a **"Select Mode"** in your Library. Users check the boxes of 3 recipes, click **"Generate List,"** and the app sums the quantities (e.g., 200g butter from Recipe A + 100g from Recipe B = 300g total).

---

## 6. Success Metrics for MVP

- **Accuracy:** % of recipes that require zero manual editing after LLM extraction.
- **Time-to-Table:** Reduction in time spent manually writing down ingredients vs. using the app.
