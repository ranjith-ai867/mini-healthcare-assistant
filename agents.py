
"""
agents.py
---------
The three agents required by the assignment:

1. GreetingAgent
   - Looks up a user by ID
   - Greets the user
   - Re-prompts if invalid

2. CGMMealPlannerAgent
   - Classifies CGM glucose
   - Generates a 3-meal plan using the LLM
   - Falls back to a rule-based plan if the LLM is unavailable

3. InterruptAgent
   - Answers one free-text question using the same LLM
   - Falls back to a small rule-based response if the LLM is unavailable
   - Returns the user to the main flow
"""

from llm import LLMUnavailableError


# =========================================================
# GREETING AGENT
# =========================================================

class GreetingAgent:

    def __init__(self, users_df):
        self.users_df = users_df

    def run(self, user_id: str) -> dict:

        if not user_id or not user_id.strip():
            return {
                "ok": False,
                "message": "Please enter a User ID (e.g. **U001**).",
                "user": None,
            }

        uid = user_id.strip().upper()

        match = self.users_df[
            self.users_df["user_id"] == uid
        ]

        if match.empty:
            return {
                "ok": False,
                "message": (
                    f"I couldn't find a user with ID **{uid}**. "
                    "Please check the ID and try again "
                    "(valid range: U001–U020)."
                ),
                "user": None,
            }

        user = match.iloc[0].to_dict()

        message = (
            f"👋 Hello, **{user['first_name']} {user['last_name']}**!\n\n"
            f"- City: {user['city']}\n"
            f"- Dietary preference: **{user['dietary_preference']}**\n"
            f"- Medical condition on file: **{user['medical_condition']}**\n\n"
            "Enter your current CGM reading below to get today's meal plan."
        )

        return {
            "ok": True,
            "message": message,
            "user": user,
        }


# =========================================================
# CGM MEAL PLANNER AGENT
# =========================================================

class CGMMealPlannerAgent:

    LOW = 80
    HIGH = 300

    def __init__(self, llm):
        self.llm = llm

    def run(self, user: dict, glucose: int) -> dict:

        status, note = self._classify(glucose)

        prompt = self._build_prompt(
            user,
            glucose,
            status,
        )

        try:

            plan_text = self.llm.generate(
                prompt,
                max_tokens=450,
            )

            source_note = ""

        except LLMUnavailableError as exc:

            # Print the real error for debugging
            print(f"[CGMMealPlannerAgent] LLM ERROR: {exc}")

            plan_text = self._fallback_plan(
                user,
                status,
            )

            source_note = (
                "\n\n"
                "*(LLM unavailable — showing a rule-based fallback plan.)*"
            )

        header = (
            f"**CGM reading: {glucose} mg/dL — {status}**\n"
            f"{note}\n\n"
        )

        return {
            "ok": True,
            "message": header + plan_text + source_note,
        }

    # -----------------------------------------------------
    # Glucose classification
    # -----------------------------------------------------

    def _classify(self, glucose: int):

        if glucose < self.LOW:

            return (
                "Low",
                "⚠️ Below the 80–300 mg/dL target range. "
                "The plan favors a quick, easily digestible "
                "carbohydrate source, with a reminder to "
                "recheck your glucose shortly.",
            )

        if glucose > self.HIGH:

            return (
                "High",
                "⚠️ Above the 80–300 mg/dL target range. "
                "The plan is adjusted to be lower in refined "
                "carbohydrates and added sugar.",
            )

        return (
            "In range",
            "✅ Within the 80–300 mg/dL target range.",
        )

    # -----------------------------------------------------
    # LLM prompt
    # -----------------------------------------------------

    def _build_prompt(
        self,
        user: dict,
        glucose: int,
        status: str,
    ) -> str:

        return (
            "You are a cautious nutrition assistant creating "
            "a same-day 3-meal plan (Breakfast, Lunch, Dinner) "
            "for the person below.\n\n"

            "This is an educational prototype, not medical advice. "
            "Never diagnose or prescribe medication.\n\n"

            f"Dietary preference: "
            f"{user['dietary_preference']}\n"

            f"Medical condition: "
            f"{user['medical_condition']}\n"

            f"Current CGM glucose reading: "
            f"{glucose} mg/dL ({status})\n"

            "Target range used by this prototype: 80–300 mg/dL\n\n"

            "Instructions:\n"

            "- Strictly respect the dietary preference "
            "(veg / non-veg / vegan).\n"

            "- Take the medical condition into account.\n"

            "- If glucose is High, reduce refined carbohydrates "
            "and added sugar.\n"

            "- If glucose is Low, include an appropriate "
            "fast-acting carbohydrate suggestion and advise "
            "rechecking glucose in about 15 minutes.\n"

            "- Output exactly three meals:\n"
            "  Breakfast\n"
            "  Lunch\n"
            "  Dinner\n"

            "- Keep each meal short, around 1–2 lines.\n"

            "- End with one short safety note recommending "
            "consultation with a healthcare professional.\n"
        )

    # -----------------------------------------------------
    # Rule-based fallback
    # -----------------------------------------------------

    def _fallback_plan(
        self,
        user: dict,
        status: str,
    ) -> str:

        pref = user["dietary_preference"].lower()

        protein = {
            "veg": "paneer or lentils (dal)",
            "vegan": "tofu or chickpeas",
            "non-veg": "grilled chicken or fish",
        }.get(
            pref,
            "a protein source of your choice",
        )

        main_protein = protein.split(" or ")[0]

        if status == "High":

            carb_note = (
                "kept lower in refined carbohydrates "
                "and added sugar"
            )

        elif status == "Low":

            carb_note = (
                "includes a quick-acting carbohydrate source, "
                "with a reminder to recheck glucose in "
                "about 15 minutes"
            )

        else:

            carb_note = "balanced across the day"

        return (
            f"**Breakfast:** Vegetable oats or a small bowl "
            f"of fruit with nuts, plus {main_protein}.\n\n"

            f"**Lunch:** {protein.capitalize()} with a "
            f"whole grain (brown rice or whole-wheat roti) "
            f"and a side of mixed vegetables or salad.\n\n"

            f"**Dinner:** A lighter meal — {protein} with "
            f"steamed vegetables and a small portion of "
            f"whole grains.\n\n"

            f"*This plan is {carb_note}, adjusted for "
            f"{user['medical_condition']}.*\n\n"

            "**Safety note:** This is a general, educational "
            "suggestion — please consult a doctor or dietitian "
            "for real medical or dietary decisions."
        )


# =========================================================
# INTERRUPT AGENT
# =========================================================

class InterruptAgent:

    def __init__(self, llm):
        self.llm = llm

    def run(
        self,
        question: str,
        user: dict | None = None,
    ) -> str:

        # -------------------------------------------------
        # Validate question
        # -------------------------------------------------

        if not question or not question.strip():

            return (
                "**Q:** No question provided.\n\n"
                "**A:** Please enter a question and try again."
            )

        question = question.strip()

        # -------------------------------------------------
        # Optional user context
        # -------------------------------------------------

        context = ""

        if user:

            context = (
                f"The current user is {user['first_name']}. "
                f"Their dietary preference is "
                f"{user['dietary_preference']}.\n\n"
            )

        # -------------------------------------------------
        # LLM prompt
        # -------------------------------------------------

        prompt = (
            "You are a helpful general-purpose assistant "
            "inside a healthcare demonstration application.\n\n"

            "Answer the user's question briefly and clearly "
            "in 2–4 sentences.\n\n"

            "If the question is related to health or medicine, "
            "provide general educational information only and "
            "include a short recommendation to consult a "
            "qualified healthcare professional for personal "
            "medical decisions.\n\n"

            f"{context}"

            f"User question: {question}\n\n"

            "Answer:"
        )

        # -------------------------------------------------
        # Call LLM
        # -------------------------------------------------

        try:

            answer = self.llm.generate(
                prompt,
                max_tokens=250,
            )

            source_note = ""

        except LLMUnavailableError as exc:

            # IMPORTANT:
            # Print the actual error so we can diagnose
            # InterruptAgent separately from the meal agent.
            print(
                f"[InterruptAgent] LLM ERROR: {exc}"
            )

            answer = self._fallback_answer(
                question,
                user,
            )

            source_note = (
                "\n\n"
                "*(LLM unavailable — showing a rule-based "
                "fallback answer.)*"
            )

        # -------------------------------------------------
        # Return answer
        # -------------------------------------------------

        return (
            f"**Q:** {question}\n\n"
            f"**A:** {answer}"
            f"{source_note}\n\n"
            "---\n"
            "*You're back in the main flow — continue with "
            "your CGM reading or meal plan above.*"
        )

    # =====================================================
    # FALLBACK TOPICS
    # =====================================================

    _FALLBACK_TOPICS = [

        (
            (
                "sugar",
                "sweet",
                "dessert",
                "candy",
            ),

            "In general, people managing diabetes are often "
            "advised to limit added sugar and pay attention "
            "to carbohydrate portions. The appropriate amount "
            "depends on the person's overall diet, glucose "
            "management, and treatment plan. Please consult "
            "a doctor or dietitian for personalized advice."
        ),

        (
            (
                "exercise",
                "workout",
                "walk",
                "run",
            ),

            "Light-to-moderate physical activity can support "
            "overall health and glucose management, but the "
            "appropriate type and intensity depend on the "
            "person's health and glucose levels. Consult a "
            "healthcare professional before starting a new "
            "exercise routine."
        ),

        (
            (
                "water",
                "hydration",
                "drink",
            ),

            "Staying adequately hydrated is generally "
            "important for overall health. Individual fluid "
            "needs can vary, particularly when other health "
            "conditions are present. A healthcare professional "
            "can provide personalized guidance."
        ),

        (
            (
                "sleep",
                "tired",
                "rest",
            ),

            "Consistent, adequate sleep is generally associated "
            "with better overall health and can support healthy "
            "glucose regulation. Persistent sleep problems "
            "should be discussed with a healthcare professional."
        ),
    ]

    # =====================================================
    # FALLBACK ANSWER
    # =====================================================

    def _fallback_answer(
        self,
        question: str,
        user: dict | None = None,
    ) -> str:

        q_lower = question.lower()

        for keywords, answer in self._FALLBACK_TOPICS:

            if any(
                word in q_lower
                for word in keywords
            ):

                return answer

        return (
            "I couldn't generate a live response right now. "
            "Please try the question again in a moment."
        )
