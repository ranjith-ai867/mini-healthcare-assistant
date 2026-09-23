"""
app.py
------
Main entry point for the Mini Healthcare Assistant. Defines the Gradio
interface and connects the three agents (Greeting, CGM + Meal Planner,
Interrupt/Q&A).
"""

import gradio as gr

from agents import CGMMealPlannerAgent, GreetingAgent, InterruptAgent
from data import ensure_dataset, load_users
from llm import LLMClient

# ==========================================
# 1. INITIALIZE DATA AND AGENTS
# ==========================================

DATA_PATH = "data/synthetic_users.csv"

ensure_dataset(DATA_PATH)          # Generate the synthetic dataset if missing
users = load_users(DATA_PATH)      # Load synthetic users

llm = LLMClient()                  # Uses HF_TOKEN if set, else falls back gracefully

greeting_agent = GreetingAgent(users)
meal_planner_agent = CGMMealPlannerAgent(llm)
interrupt_agent = InterruptAgent(llm)


# ==========================================
# 2. GREETING AGENT FUNCTION
# ==========================================

def greet_user(user_id):
    result = greeting_agent.run(user_id)
    if not result["ok"]:
        return result["message"], None
    return result["message"], result["user"]


# ==========================================
# 3. CGM + MEAL PLANNER AGENT FUNCTION
# ==========================================

def generate_meal_plan(user, glucose):
    if user is None:
        return "Please find a valid User ID first."

    if glucose is None:
        return "Please enter your CGM reading."

    try:
        glucose = int(glucose)
    except (ValueError, TypeError):
        return "Please enter a valid whole-number CGM reading."

    result = meal_planner_agent.run(user, glucose)
    return result["message"]


# ==========================================
# 4. INTERRUPT AGENT FUNCTION
# ==========================================

def answer_question(question, user):
    if not question or not question.strip():
        return "Please enter a question."
    return interrupt_agent.run(question.strip(), user)


# ==========================================
# 5. BUILD GRADIO USER INTERFACE
# ==========================================

with gr.Blocks(title="Mini Healthcare Assistant") as demo:

    gr.Markdown(
        """
        # 🩺 Mini Healthcare Assistant

        A small multi-agent demo using synthetic user profiles and an
        LLM-driven, CGM-aware meal planner.

        **Important:** Educational prototype only — synthetic data,
        no medical diagnosis or treatment advice.
        """
    )

    # ---- User Identification ----
    gr.Markdown("## 1. User Identification")

    with gr.Row():
        user_id = gr.Textbox(label="Enter User ID", placeholder="Example: U001")
        find_user_button = gr.Button("Find User", variant="primary")

    greeting_output = gr.Markdown()
    user_state = gr.State(None)  # holds the selected user profile

    find_user_button.click(
        fn=greet_user,
        inputs=[user_id],
        outputs=[greeting_output, user_state],
    )

    # ---- CGM + Meal Planner ----
    gr.Markdown("## 2. CGM Reading and Meal Planner")

    glucose_input = gr.Number(label="Enter CGM Reading (mg/dL)", value=None, precision=0)
    generate_button = gr.Button("Generate Today's Meal Plan", variant="primary")
    meal_plan_output = gr.Markdown()

    generate_button.click(
        fn=generate_meal_plan,
        inputs=[user_state, glucose_input],
        outputs=[meal_plan_output],
    )

    # ---- Interrupt Agent (Q&A) ----
    gr.Markdown("## 3. Ask a General Question")

    question_input = gr.Textbox(label="Your Question", placeholder="Ask an unrelated question here...")
    ask_button = gr.Button("Ask Question")
    answer_output = gr.Markdown()

    ask_button.click(
        fn=answer_question,
        inputs=[question_input, user_state],
        outputs=[answer_output],
    )

    # ---- Footer ----
    gr.Markdown(
        """
        ---
        **Data:** Synthetic profiles only (generated with Faker).

        **Agents:** Greeting Agent · CGM + Meal Planner Agent · Interrupt Agent

        **Safety:** The 80–300 mg/dL range is an assignment requirement, not a
        personalized clinical target. Always follow guidance from a qualified
        healthcare professional.
        """
    )


if __name__ == "__main__":
    demo.launch()
