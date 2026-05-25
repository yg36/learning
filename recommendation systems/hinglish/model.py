# from transformers import (
#     AutoTokenizer,
#     AutoModelForSeq2SeqLM
# )

# MODEL_NAME = "google/flan-t5-base"


# # Load tokenizer
# tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


# # Load model
# model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)


# def generate_response(prompt):

#     # Convert text into tokens
#     inputs = tokenizer(
#         prompt,
#         return_tensors="pt",
#         truncation=True
#     )

#     # Generate response
#     outputs = model.generate(
#         **inputs,
#         max_new_tokens=50
#     )

#     # Convert tokens back to text
#     response = tokenizer.decode(
#         outputs[0],
#         skip_special_tokens=True
#     )

#     return response


# from transformers import pipeline


# # Simple multilingual text generation model
# chat_model = pipeline(
#     "text2text-generation",
#     model="google/flan-t5-base"
# )



# def generate_response(prompt):
#     result = chat_model(
#         prompt,
#         max_length=100,
#         do_sample=True
#     )

#     return result[0]["generated_text"]



from transformers import pipeline

MODEL_NAME = "microsoft/phi-2"


chat_model = pipeline(
    "text-generation",
    model=MODEL_NAME
)


def generate_response(prompt):

    result = chat_model(
        prompt,
        max_new_tokens=20,
        temperature=0.3,
        do_sample=True,
        top_p=0.8,
        repetition_penalty=1.5,
        return_full_text=True
    )

    response = result[0]["generated_text"]

    return response.strip()