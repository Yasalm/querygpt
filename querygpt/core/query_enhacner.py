from pydantic import BaseModel
from querygpt.config.config import Config
import json
from querygpt.core import chat_completion_from_config


def enhance_user_question(user_question: str, config: Config) -> str:

    class EnhancedQuestion(BaseModel):
        original_question: str
        enhanced_question: str

    prompt = f"""
        You are a database query clarification assistant. Your job is to make ambiguous user questions clearer and more specific without making them overly complex.

        ## Your Task:
        Transform this ambiguous question into a clear, specific question that an AI SQL agent can easily understand and execute.

        **Original Question:** "{user_question}"

        ## Clarification Framework:

        ### 1. Specify the Scope
        - What exactly should be measured/counted/analyzed?
        - What specific filters or conditions?
        - **Time period (only if relevant):** When adding time constraints, make them flexible so the you can adapt based on available data

        ### 2. Define the Output
        - What format should the results be in?
        - How should results be ordered/ranked?
        - How many results are needed?

        ### 3. Clarify Ambiguous Terms
        - Replace vague terms with specific business concepts
        - Define what "top", "best", "most", "popular" means
        - Specify metrics for comparisons

        ## Examples:

        **Ambiguous:** "Show me the best customers"
        **Clarified:** "Show me the top 10 customers ranked by total spending, ordered from highest to lowest"

        **Ambiguous:** "Which staff are doing good?"
        **Clarified:** "Which staff members have the highest total sales, ordered from highest to lowest? (you should adapt time period based on available data - could be recent period, all time, or most active period in database)"

        **Ambiguous:** "Which movies are popular?"
        **Clarified:** "Which films have been rented the most times, ordered by rental count?"

        **Ambiguous:** "How are sales doing?"
        **Clarified:** "What is the total rental revenue over time? (you should determine appropriate time grouping - monthly, weekly, or quarterly - based on data range available)"

        ## Your Clarified Question:
        Make the original question specific and unambiguous. If time periods are suggested, make them adaptive so the you can adjust based on what data actually exists.

        **Clarified Question:** [Your clarification here]
        """
    messages = [
        {
            "role": "system",
            "content": "You are a data analyst expert.",
        },
        {"role": "user", "content": prompt},
    ]
    try:
        response = chat_completion_from_config(
            messages, config, response_format=EnhancedQuestion
        )
        return EnhancedQuestion(**json.loads(response.choices[0].message.content))
    except Exception as e:
        print(e) # need better logging
        return user_question



