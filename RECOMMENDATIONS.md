# 🧠 Smart Recommendation System - DBIT Alumni Hub

This module implements a professional, rule-based recommendation engine for the DBIT Alumni Hub. It suggests relevant connections to Students and Alumni based on profile similarity and academic/professional data.

---

## 🎯 Features

- **Cross-Role Suggestions**: Automatically recommends Alumni to Students and Students to Alumni.
- **Top 5 Priority**: Only displays the top 5 most relevant users to ensure a clean user interface.
- **Rule-Based Scoring**: Uses a weighted scoring system to rank potential connections.
- **Smart Filtering**: Automatically excludes:
    - The logged-in user themselves.
    - Users who are already connected.
    - Users with pending outgoing or incoming connection requests.

---

## ⚙️ Recommendation Logic (Scoring Engine)

The system calculates a "Compatibility Score" for potential candidates based on the following weights:

| Criterion | Score | Logic |
| :--- | :--- | :--- |
| **Branch Match** | **+5** | Both users belong to the same academic department. |
| **Skill Overlap** | **+5** | Points awarded **per matching skill** between profiles. |
| **Domain Match** | **+3** | Users share the same professional domain (e.g., "Web Development"). |
| **City Match** | **+2** | Both users are located in the same city. |

---

## 📁 System Architecture (Modular)

Following Flask best practices, the system is split into multiple modules for maintainability:

- **`models/recommendation.py`**: Contains the core `get_recommended_users` logic and scoring algorithm.
- **`routes/recommendation_routes.py`**: Defines the `Blueprint` and API endpoint (`/recommendations`) for fetching data asynchronously.
- **`templates/student/dashboard.html`**: Frontend JINJA template displaying the "Recommended for You" section for students.
- **`templates/alumni/dashboard.html`**: Frontend JINJA template displaying "Students You May Know" for alumni.

---

## 🛠️ Data Infrastructure

The recommendation engine relies on the following fields in the `Users` table:
- `branch`
- `passing_year`
- `current_domain`
- `skills` (Comma-separated values)
- `interests` (Comma-separated values)
- `city`
- `company`

---

## 🚀 Future Scope & AI Potential

While currently rule-based for performance and transparency, the system is designed to scale into:

1.  **AI-based Recommendations**: Implementing Vector Embeddings (using Sentence Transformers) to calculate cosine similarity between bios and interests.
2.  **Collaborative Filtering**: Suggesting connections based on "Alumni who connected with User X also connected with User Y".
3.  **Job & Opportunity Match**: Extending the logic to suggest Job postings based on a student's skills and interest scores.
4.  **Mentor Pairing**: Advanced mentor-mentee matching based on career trajectory overlap and qualification levels.

---

**Developed by**: Expert Flask Developer Team
**Status**: ✅ Active & Integrated
**Version**: 1.0.0
