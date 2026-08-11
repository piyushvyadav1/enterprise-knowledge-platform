from app.ai.llm_service import generate_answer


context = """
Employee Leave Policy

The current approved Employee Leave Policy states:

Casual Leave (CL): 15 Days per calendar year.
Sick Leave (SL): 10 Days.
Earned / Privilege Leave (EL): 15 Days.

The document is version 2 and approved.
"""


question = (
    "How many days of casual leave "
    "are employees entitled to?"
)


answer = generate_answer(
    question=question,
    context=context,
)


print()
print("ANSWER:")
print(answer)
print()