"""
LLM Connector
"""
from typing import NamedTuple, List
from langchain_core.documents.base import Document

# LangChain Libraries.
#from langchain_openai import OpenAI # LangChain OpenAI Adapter
from langchain.chains import LLMChain        # LangChain Library
from langchain.prompts import PromptTemplate # LangChain Library
from langchain_community.llms import HuggingFaceTextGenInference

import time

# Text generation inference APIs.
import text_generation
import text_generation.errors

from webui_config import LlmModelConfig

# Some prompt templates.

LLAMA_PROMPT_TEMPLATE = """
<s>[INST] <<SYS>>
{sys}
<</SYS>>
{rag}
{user} [/INST]
"""

SAMPLE_SYS_PROMPT = """
You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe.  Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.

If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.

Answer the question in Markdown format for readability, use bullet points if possible.
"""

RAG_STEM = """
If there is nothing in the context relevant to the question at hand, just resuse to answer it. Don't try to make up an answer.

Anything between the following `context` html blocks is retrieved from a knowledge bank, not part of the conversation with the user. 

"""

#
class LlmGenerationParameters(NamedTuple):
    max_new_tokens: int
    top_k: int
    top_p: float
    temperature: float
    repetition_penalty: float
    @classmethod
    def new_generation_parameter(cls, max_new_tokens=1024, top_k=10, top_p=0.9, temperature=0.1, repetition_penalty=1.3):
        return cls(max_new_tokens=max_new_tokens,
                   top_k=top_k, 
                   top_p=top_p, 
                   temperature=temperature, 
                   repetition_penalty=repetition_penalty)

#
def llm_stream_result(prompt: str, llm_model: LlmModelConfig, llm_parameter: LlmGenerationParameters):
    # Check LLM service provider.
    if llm_model.provider.lower() == "huggingface":
        llm = HuggingFaceTextGenInference(
            inference_server_url=llm_model.endpoint,
            max_new_tokens=llm_parameter.max_new_tokens,
            top_k=llm_parameter.top_k,
            top_p=llm_parameter.top_p,
            temperature=llm_parameter.temperature,
            repetition_penalty=llm_parameter.repetition_penalty,
        )                
    else:
        raise NotImplemented("May implement someday lol.")
    
    # This is the broker function that handles the limit of concurrent requests.
    def streamer():
        
        while True: # Retry on overload.
            try:
                # If we get the resource, we can start streaming.
                for token in llm.stream(prompt):
                    yield token
                break
            except text_generation.errors.OverloadedError: # Overload error.
                time.sleep(5) # Wait for 5 seconds and continue.
                continue
    return streamer() # Return the generator.

def craft_prompt(user_input, rag_content: List[Document]=[]):
    prompt = PromptTemplate(
        input_variables=["sys", "user"],
        template=LLAMA_PROMPT_TEMPLATE,  # TODO: Ability to switch prompt templates.
        partial_variables={"rag": ""},
        )
    # Prompt crafting.
    user_prompt = prompt.partial(sys=SAMPLE_SYS_PROMPT)  # TODO: User defined system prompt.

    if rag_content:
        rag_documents = "\n".join([x.page_content for x in rag_content])
        rag_prompt = RAG_STEM + f"<context>\n{rag_documents}\n</context>\n"
        user_prompt = user_prompt.partial(rag=rag_prompt)
        
    prompt = user_prompt.format(user=user_input) 
    return prompt