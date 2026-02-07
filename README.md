# Classical Music Explorer Agent

A full-stack AI application powered by **AgentField**. This project demonstrates how to build an interactive educational agent that provides classical music lectures, composer profiles, and personalized music recommendations.

## User Scenario

1.  **Topic Selection**: A user arrives at the page and selects a topic (e.g., "The Romantic Era").
2.  **Knowledge Briefing**: The `lecture` reasoner provides a comprehensive briefing on the topic, summarizing key historical and theoretical points.
3.  **Deep Dive**: The user can then "dig further" by selecting a specific **COMPOSER**. This triggers the `get_composer_info` reasoner to retrieve a detailed profile.
4.  **Concrete Examples**: Finally, the user requests music recommendations. The `recommend_music` reasoner provides specific pieces with YouTube links to listen to, offering concrete examples of the composer's style.

## Project Scope

*   **Stage 1 (Current)**: **Basic Learning Engine for Music**. Users can explore predefined topics, receive lectures, and find static or generated music recommendations.
*   **Stage 2 (Future)**: **Leverage AI for Personalized Content**. Expand the system to generate content based on user interests, mood, or other dynamic inputs (e.g., interactive quizzes, generated sheet music, or mood-based playlists).

## Features

- **Interactive Lectures**: Get AI-generated lectures on musical eras, styles, or specific topics.
- **Composer Profiles**: Deep dive into composer biographies, fetched from local data or Wikipedia.
- **Music Recommendations**: Receive curated listening suggestions with direct YouTube links.
- **Sheet Music Generation**: (Experimental) Generate ABC notation for themes.

## Architecture

- **Frontend**: React (Vite) application for the user interface.
- **Backend Agent**: A Python agent built with the `agentfield` framework.
- **Control Plane**: The AgentField server orchestrates communication between the frontend and the agent.

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **AgentField**: Installed via `pip`.

## Installation

### 1. Backend Setup

Navigate to the `my-agent` directory:

```bash
cd my-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Set up environment variables (optional for basic features, required for AI):

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY or OPENAI_API_KEY
```

### 2. Frontend Setup

Navigate to the `web` directory:

```bash
cd ../web
npm install
```

## Running the Application

You will need three terminal windows/tabs.

### Terminal 1: AgentField Server
Start the control plane:

```bash
af server
```

### Terminal 2: The Agent
Start your music agent:

```bash
cd my-agent
# Ensure venv is active
python main.py
```

### Terminal 3: The Frontend
Start the React development server:

```bash
cd web
npm run dev
```

Open your browser at `http://localhost:5173`.

## Usage

1.  **Select a Topic**: Enter a topic like "Baroque Music" or "Beethoven" to get a lecture.
2.  **Explore Composers**: Click on related composers to view their detailed profile.
3.  **Get Recommendations**: Ask for music similar to the composer to get YouTube links.