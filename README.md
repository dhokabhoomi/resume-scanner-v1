# Resume Analysis (Fullstack: React + FastAPI)

This project is a full-stack resume analysis tool with a React (Vite) frontend and a FastAPI backend.  
Users can upload PDF resumes, which the backend analyzes for content quality, structure, and completeness.  
The frontend displays a structured report with scores, feedback, and improvement suggestions.

---

## 🚀 Features

- **Resume PDF Upload**: Only PDF uploads supported, with validation and error handling.
- **Backend Integration**: Sends uploaded files to a FastAPI backend (`/analyze_resume`).
- **Dynamic Report Rendering**: Displays an overall score and detailed sections:
  - Basic Info
  - Professional Summary
  - Education
  - Work Experience
  - Projects
  - Skills
  - Certifications
  - Extracurriculars
- **Custom Content Renderer**: Displays nested objects/arrays in a readable format (no raw JSON).
- **Expandable Sections**: Toggle open/close for each resume section.
- **Modern UI**: Clean design using custom CSS and Vishwakarma University theme colors.

---

## 📂 Project Structure

```
ai_resume_scanner/
│
├── backend/                # FastAPI backend (resume analysis logic)
│
├── ai-resume-frontend/     # React (Vite) frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── UploadResumeForm.jsx   # File upload form
│   │   │   ├── SectionCard.jsx        # Resume section card
│   │   ├── utils/
│   │   │   └── renderContent.jsx      # Content rendering utility
│   │   ├── App.jsx                    # Main app component
│   │   └── index.css                  # Global styles
│   ├── package.json
│   ├── vite.config.js
│
├── .gitignore
├── README.md
```

---

## ⚙️ Setup & Usage

### 1. Clone the Repository

```bash
git clone https://github.com/dhokabhoomi/resume-scanner-v1.git
cd resume-scanner-v1t
```

### 2. Backend Setup (FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- Runs at `http://localhost:8000`
- Resume upload endpoint: `http://localhost:8000/analyze_resume`

### 3. Frontend Setup (React + Vite)

```bash
cd ai-resume-frontend
npm install
npm run dev
```

- Runs at `http://localhost:5173`

### 4. Upload Resume

- Open `http://localhost:5173`
- Upload a PDF resume
- View the analysis report with scores and suggestions

---

## 🧩 Components Overview

### UploadResumeForm.jsx

- Handles file input & validation (PDF only).
- Displays file name, size, and error messages.
- Uploads file to backend and shows progress.

### SectionCard.jsx

- Displays a resume section with:
  - Title
  - Quality & completeness scores
  - Suggestions
- Expandable/collapsible design.

### renderContent.jsx

- Recursively renders objects and arrays into human-readable text.
- Avoids showing raw JSON output.

### App.jsx

- Main component managing state and rendering analysis results.

---

## 🎨 Customization

- Styles can be updated in `.css` files (e.g., `UploadResumeForm.css`).
- Backend URL can be changed in `UploadResumeForm.jsx`.
- Extend `renderContent.jsx` to modify how data is displayed.

---

## 📦 Tech Stack

- **Frontend**: React (Vite), CSS
- **Backend**: Python, FastAPI
- **API**: Fetch API (native)

---

## 👩‍💻 Author

Developed by [Bhoomi](https://github.com/dhokabhoomi).

---

## 🙏 Acknowledgments

Inspired by resume analysis tools with a custom React UI for structured data visualization.
