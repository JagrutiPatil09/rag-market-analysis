import gradio as gr
from main import retrieve_and_generate_response

def chatbot_interface(query):
    return retrieve_and_generate_response(query)["response"]

gr.Interface(fn=chatbot_interface, inputs="text", outputs="text").launch()
