"""
LLM Connector
"""
from typing import NamedTuple

# LangChain Libraries.
#from langchain_openai import OpenAI # LangChain OpenAI Adapter
from langchain.chains import LLMChain        # LangChain Library
from langchain.prompts import PromptTemplate # LangChain Library
from langchain_community.llms import HuggingFaceTextGenInference

# Some prompt templates.

LLAMA_PROMPT_TEMPLATE = """
<s>[INST] <<SYS>>
{sys}
<</SYS>>
 
{user} [/INST]
"""

SAMPLE_SYS_PROMPT = """
You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe.  Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.

If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.

Answer the question in Markdown format for readability, use bullet points if possible.
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

class LlmModelConfig(NamedTuple):
    provider: str
    endpoint: str
    @classmethod
    def new_llm_config(cls, model_provider: str, model_endpoint: str):
        return cls(provider=model_provider.lower(), 
                   endpoint=model_endpoint)

#
def llm_stream_result(prompt: str, llm_model: LlmModelConfig, llm_parameter: LlmGenerationParameters) -> str:
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
    return llm.stream(prompt)

def craft_prompt(user_input):
    prompt = PromptTemplate(
        input_variables=["sys", "user"],
        template=LLAMA_PROMPT_TEMPLATE,  # TODO: Ability to switch prompt templates.
        )
    # Prompt crafting.
    user_prompt = prompt.partial(sys=SAMPLE_SYS_PROMPT)  # TODO: User defined system prompt.
    prompt = user_prompt.format(user=user_input) 
    return prompt