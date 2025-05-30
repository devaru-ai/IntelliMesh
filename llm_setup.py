import os
from transformers import BitsAndBytesConfig, AutoModelForCausalLM, AutoTokenizer, pipeline
from langchain.llms import HuggingFacePipeline

# Set API keys and model names
os.environ["HUGGINGFACE_API_KEY"] = "your_hf_key"
os.environ["SERPER_API_KEY"] = "your_serper_key"
model_name = "meta-llama/Meta-Llama-3-8B-Instruct"

# Quantization config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype="float16",
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
)

# Load model and tokenizer
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True
)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# HuggingFace pipeline
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=512,
    device_map="auto"
)

# LangChain LLM wrapper
llm = HuggingFacePipeline(pipeline=pipe)
