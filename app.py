from dotenv import load_dotenv
import os
import streamlit as st
from audiorecorder import audiorecorder
from langchain_openai import ChatOpenAI
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnableConfig
from langchain_community.tools.pubmed.tool import PubmedQueryRun
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import create_structured_chat_agent
from langchain.agents import AgentExecutor
from langchain import hub
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from speech_detection import speech_from_mic
from text_to_speech import speech_synthesis_with_language
from pydub import AudioSegment
import deepl
import uuid
import csv

load_dotenv()
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

@tool
def translate(input: str, target_lang: str) -> str:
    '''
    This tool translates the input text to the target language.
    Language codes are case-insensitive strings according to ISO 639-1, for example 'DE', 'FR', 'JA''.
    Use "EN-US" for English and "ZH" for Chinese.
    REMEMBER THE TRANSLATION IS NOT PERFECT, SO USE IT AS A GUIDE AND NOT AS A FINAL TRANSLATION. MODIFY THE TRANSLATION AS NEEDED FOR CLARITY AND ACCURACY.
    '''
    if target_lang == "EN":
        target_lang = "EN-US"
    if target_lang == "ZH-CN":
        target_lang = "ZH"
    try:
        translator = deepl.Translator(DEEPL_API_KEY)
    except Exception as e:
        return f"Failed to initialize the translator: {e}"
    
    result = translator.translate_text(input, target_lang = target_lang)
    return result.text

language_code = {}

# read from laguage_code.csv
with open('language_code.csv', mode='r') as infile:
    reader = csv.reader(infile)
    for row in reader:
        language_code[row[1]] = row[0]

# create a set of language full names
language_full_names = set(language_code.keys())

st.set_page_config(page_title="MedMax", page_icon="💊")
st.title("MedMax")

patient_language = st.selectbox(
    'What language does the patient speak?',
    language_full_names
)

doctor_language = st.selectbox(
    'What language does the doctor speak?',
    language_full_names
)

speaker = st.selectbox(
        'Who is speaking?',
        ('Patient', 'Doctor')
    )

recipient = st.selectbox(
    'Who are you talking to?',
    ('Patient', 'Doctor', 'AI')
)

input_code = language_code[patient_language]

if speaker == "Patient":
    input_code = language_code[patient_language]
elif speaker == "Doctor":
    input_code = language_code[doctor_language]

msgs = StreamlitChatMessageHistory()
memory = ConversationBufferMemory(
    chat_memory=msgs, return_messages=True, memory_key="chat_history", output_key="output"
)

audio = []
if len(msgs.messages) == 0:
    msgs.clear()
    msgs.add_ai_message("How can I help you?")
    st.session_state.steps = {}

avatars = {"human": "🗿", "ai": "💊"}

for idx, msg in enumerate(msgs.messages):
    with st.chat_message(avatars[msg.type]):
        # Render intermediate steps if any were saved
        for step in st.session_state.steps.get(str(idx), []):
            if step[0].tool == "_Exception":
                continue
            with st.status(f"**{step[0].tool}**: {step[0].tool_input}", state="complete"):
                st.write(step[0].log)
                st.write(step[1])
        st.write(msg.content)

if prompt := st.chat_input() or speech_from_mic(input_code, audiorecorder(start_prompt="Start recording", stop_prompt="Stop recording", pause_prompt="")):
    st.chat_message("🗿").write(prompt)

    speech_synthesis_with_language("./input.wav", input_code, prompt)

    audio_file = open('./input.wav', 'rb')
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/wav')

    llm = ChatOpenAI(model_name = "gpt-4", streaming = True, temperature = 0)
    tools = [TavilySearchResults(), PubmedQueryRun(), translate]

    prompt_temp = hub.pull("kenwu/react-json-translator")
    chat_agent = create_structured_chat_agent(llm, tools, prompt_temp)
    executor = AgentExecutor(
        agent=chat_agent,
        tools=tools,
        max_iterations=7,
        memory=memory,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
    )

    with st.chat_message("💊"):
        st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
        cfg = RunnableConfig()
        cfg["callbacks"] = [st_cb]

        if speaker == "Patient":
            if recipient == "Doctor":
                prompt = "I am the patient. Help me communicate with the doctor about my inquiry by translating my message to {}. My message is: {}".format(doctor_language, prompt)
            elif recipient == "AI":
                prompt = "Use tools to resolve my inquiry and answer in {} ".format(patient_language) + "and my message is: " + prompt
        elif speaker == "Doctor":
            if recipient == "Patient":
                prompt = "I am the doctor. Help me communicate with the patient about my message by translating it to the {}. My message is: {} in {}.".format(patient_language, prompt, doctor_language)
            elif recipient == "AI":
                prompt = "Use tools to resolve my inquiry and answer in {} ".format(doctor_language) + "and my message is: " + prompt

        response = executor.invoke({"input": prompt}, cfg)

        st.write(response["output"])
        st.session_state.steps[str(len(msgs.messages) - 1)] = response["intermediate_steps"]

        if recipient == "Doctor":
            output_code = language_code[doctor_language]
        elif recipient == "Patient":
            output_code = language_code[patient_language]
        elif recipient == "AI":
            output_code = input_code

        speech_synthesis_with_language("./output.wav", output_code, response["output"])

    audio_file = open('./output.wav', 'rb')
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/wav')