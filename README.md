# Mini Healthcare Assistant

A small multi-agent healthcare assistant built for a Generative AI / Agentic AI Engineer take-home assignment.

The application demonstrates:

* Synthetic healthcare user data
* A Greeting Agent
* A CGM-aware Meal Planner Agent
* An Interrupt / Q&A Agent
* Hugging Face Inference API integration
* Gradio-based user interface
* Rule-based fallback handling when the LLM is unavailable

> **Educational prototype only.** All user data is synthetic. This application does not provide medical diagnosis or treatment.

## Features

### 1. Greeting Agent

The Greeting Agent accepts a synthetic User ID such as `U001` and retrieves the corresponding user profile.

It displays:

* First and last name
* City
* Dietary preference
* Medical condition

Invalid User IDs are handled with a clear message asking the user to try again.

### 2. CGM + Meal Planner Agent

The CGM Meal Planner accepts a current glucose reading in mg/dL.

It classifies the reading using the assignment's demonstration range:

* Below 80 mg/dL → Low
* 80–300 mg/dL → In range
* Above 300 mg/dL → High

The agent then uses the LLM to generate a same-day three-meal plan while considering:

* Current glucose reading
* Dietary preference
* Medical condition
* Breakfast, lunch, and dinner
* Basic safety guidance

A rule-based fallback is available if the LLM cannot be reached.

### 3. Interrupt Agent

The Interrupt Agent allows the user to ask a general free-text question without leaving the main workflow.

The question is sent to the LLM and the answer is returned to the user. After answering, the application directs the user back to the main CGM and meal-planning flow.

## Technology Stack

* **Python**
* **Gradio**
* **Pandas**
* **Hugging Face Inference API**
* **Hugging Face Hub**
* **python-dotenv**

## Project Structure

```text
mini-healthcare-assistant/
│
├── app.py
├── agents.py
├── llm.py
├── data.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── data/
│   └── synthetic_users.csv
│
└── tests/
    └── test_agents.py
```

## Running Locally

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd mini-healthcare-assistant
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Hugging Face

Create a `.env` file in the project root:

```text
HF_TOKEN=your_hugging_face_token
LLM_MODEL=openai/gpt-oss-120b
HF_PROVIDER=auto
```

The Hugging Face token must never be committed to GitHub.

The `.gitignore` file excludes `.env` from Git.

### 5. Run the application

```bash
python app.py
```

Gradio will display a local URL in the terminal. Open that URL in your browser.

## Running Tests

Run:

```bash
pytest
```

The tests cover the core agent behavior, including fallback behavior when the LLM is unavailable.

## Hugging Face Spaces Deployment

The application is designed to run as a **Hugging Face Space using the Gradio SDK**.

### Deployment steps

1. Create a new Hugging Face Space.
2. Select **Gradio** as the SDK.
3. Upload or push the project files.
4. Make sure `requirements.txt` is included.
5. Add the Hugging Face token under:

```text
Settings → Variables and secrets
```

Add:

```text
HF_TOKEN
```

as a **Secret**.

Add the model configuration as a Space variable if required:

```text
LLM_MODEL = openai/gpt-oss-120b
HF_PROVIDER = auto
```

The Space automatically installs the dependencies and launches `app.py`.

## GitHub Repository

**Repository:**
`YOUR_GITHUB_REPOSITORY_URL`

## Live Demo

**Hugging Face Space:**
`YOUR_HUGGINGFACE_SPACE_URL`

## Design Decisions

### Dataset

The application uses a synthetic dataset containing 20 users with IDs from `U001` to `U020`.

The dataset is generated using Faker and is intended only for demonstration purposes.

### LLM

The application uses the Hugging Face Inference API rather than hosting a local language model.

This keeps the project lightweight and makes it easier to deploy to Hugging Face Spaces.

The LLM integration is isolated inside `llm.py`, while the individual agents use the shared LLM client.

### Agent Architecture

The project uses simple Python classes instead of a heavyweight agent framework.

The three agents have clearly separated responsibilities:

```text
User
 │
 ▼
Gradio UI
 │
 ├──► GreetingAgent
 │
 ├──► CGMMealPlannerAgent ──► Hugging Face LLM
 │
 └──► InterruptAgent ────────► Hugging Face LLM
```

This approach keeps the implementation simple and easy to understand within the scope of the assignment.

### State Management

The selected user profile is stored using Gradio `gr.State`.

This allows the selected user to be passed between the different interactions in the same session without relying on global user state.

### Error Handling

The application includes fallback behavior when the LLM is unavailable.

This allows the core application flow to continue instead of completely failing when an external inference request cannot be completed.

## What I Would Add With More Time

### Mood Tracker Agent

Add a daily mood and energy tracker and optionally use the information when generating meal recommendations.

### Food Intake Agent

Allow users to record meals they actually consumed and compare their food intake with the suggested meal plan.

### Persistent Storage

Replace the CSV-based approach with SQLite or another database to store:

* User profiles
* CGM readings
* Meal plans
* Food intake
* Historical activity

### CGM Trend Analysis

Instead of using only one glucose reading, analyze historical readings to identify trends such as:

* Increasing glucose
* Decreasing glucose
* Repeated high readings
* Repeated low readings

### RAG-Based Healthcare Knowledge

Add a retrieval-augmented generation layer using trusted healthcare documentation so that general health questions can be answered using a controlled knowledge base.

### Docker

Add a `Dockerfile` and container configuration for reproducible deployment outside Hugging Face Spaces.

### Authentication

Add user authentication and stronger input validation if the application were expanded beyond an educational demonstration.

### Richer UI

Improve the Gradio interface with:

* CGM charts
* Historical trends
* Meal cards
* Daily summaries
* Better navigation
* Agent status indicators

## Safety Disclaimer

This application is an educational prototype using synthetic data.

It is **not a medical diagnostic or treatment system**.

The 80–300 mg/dL range used by the application is an assignment/demo requirement and should not be interpreted as an individualized clinical target.

Users should follow guidance from qualified healthcare professionals for personal medical decisions.
