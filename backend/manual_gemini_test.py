from app.llm.gemini import classify_email


print("Starting Gemini test...")

result = classify_email(
    sender_name="John Smith",
    sender_email="john@example.com",
    subject="Interested in your AI development services",
    body="""
Hello,

We are looking for a development team to help us build an AI-powered
customer support platform.

Could you please share your pricing and availability?

We would like to schedule a call next week.

Best regards,
John
""",
)

print("Gemini call completed.")
print("Result type:", type(result))
print("Classification:")
print(result)
print("As JSON:")
print(result.model_dump_json(indent=2))
print("Test completed.")