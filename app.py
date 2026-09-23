import gradio as gr

from data import ensure_dataset, load_users
from agents import (
    GreetingAgent,
    CGMMealPlannerAgent,
    InterruptAgent
)
from llm import LLMClient


# ==========================================
# 1. INITIALIZE DATA AND AGENTS
# ==========================================

DATA_PATH = "data/synthetic_users.csv"

# Generate the synthetic dataset if it doesn't exist
ensure_dataset(DATA_PATH)

# Load synthetic users
users = load_users(DATA_PATH)

# Initialize the LLM client
llm = LLMClient()

# Initialize the three agents
greeting_agent = GreetingAgent(users)
meal_planner_agent = CGMMealPlannerAgent(llm)
interrupt_agent = InterruptAgent(llm)


# ==========================================
# 2. GREETING AGENT FUNCTION
# ==========================================

def greet_user(user_id):

    result = greeting_agent.run(user_id)

    if not result["ok"]:
        return (
            result["message"],
            None
        )

    return (
        result["message"],
        result["user"]
    )


# ==========================================
# 3. CGM + MEAL PLANNER AGENT FUNCTION
# ==========================================

def generate_meal_plan(user, glucose):

    if user is None:
        return "Please enter a valid User ID first."

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

    result = interrupt_agent.run(
        question.strip(),
        user
    )

    return result


# ==========================================
# 5. BUILD GRADIO USER INTERFACE
# ==========================================

with gr.Blocks(title="Mini Healthcare Assistant") as demo:

    gr.Markdown(
        """
        # Mini Healthcare Assistant

        A simple multi-agent healthcare demonstration using
        synthetic user profiles and an LLM.

        **Important:** This is an educational prototype.
        It does not provide medical diagnosis or treatment.
        """
    )

    # --------------------------------------
    # USER IDENTIFICATION
    # --------------------------------------

    gr.Markdown("## 1. User Identification")

    with gr.Row():

        user_id = gr.Textbox(
            label="Enter User ID",
            placeholder="Example: U001"
        )

        find_user_button = gr.Button(
            "Find User",
            variant="primary"
        )

    greeting_output = gr.Markdown()

    # Stores the selected user profile between interactions
    user_state = gr.State(None)

    find_user_button.click(
        fn=greet_user,
        inputs=[user_id],
        outputs=[greeting_output, user_state]
    )

    # --------------------------------------
    # CGM + MEAL PLANNER
    # --------------------------------------

    gr.Markdown("## 2. CGM Reading and Meal Planner")

    glucose_input = gr.Number(
        label="Enter CGM Reading (mg/dL)",
        value=None,
        precision=0
    )

    generate_button = gr.Button(
        "Generate Today's Meal Plan",
        variant="primary"
    )

    meal_plan_output = gr.Markdown()

    generate_button.click(
        fn=generate_meal_plan,
        inputs=[user_state, glucose_input],
        outputs=[meal_plan_output]
    )

    # --------------------------------------
    # INTERRUPT AGENT
    # --------------------------------------

    gr.Markdown("## 3. Ask a General Question")

    question_input = gr.Textbox(
        label="Your Question",
        placeholder="Ask an unrelated question here..."
    )

    ask_button = gr.Button("Ask Question")

    answer_output = gr.Markdown()

    ask_button.click(
        fn=answer_question,
        inputs=[question_input, user_state],
        outputs=[answer_output]
    )

    # --------------------------------------
    # FOOTER
    # --------------------------------------

    gr.Markdown(
        """
        ---
        **Data:** Synthetic profiles only.

        **Agents:** Greeting Agent, CGM + Meal Planner Agent,
        and Interrupt Agent.

        **Safety:** The CGM range is an assignment requirement,
        not a personalized clinical target. Always follow
        guidance from a qualified healthcare professional.
        """
    )


# ==========================================
# 6. LAUNCH APPLICATION
# ==========================================
if __name__ == "__main__":
    print("APP STARTING", flush=True)

    import os

    port = int(os.environ.get("PORT", 10000))

    demo.launch(
        server_name="0.0.0.0",
        server_port=port
    )