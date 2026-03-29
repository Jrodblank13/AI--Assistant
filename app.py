import os
import requests
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# MEMORY (ChatGPT-style conversation)
conversation = [
    {
        "role": "system",
        "content": "You are ChatGPT. Be helpful, smart, and conversational."
    }
]

# 🌐 Simple web search (DuckDuckGo)
def search_web(query):
    try:
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json"}
        res = requests.get(url, params=params)
        data = res.json()
        return data.get("AbstractText", "")
    except:
        return ""

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"]

    web_info = search_web(user_message)

    if web_info:
        conversation.append({
            "role": "system",
            "content": f"Use this context if relevant: {web_info}"
        })

    conversation.append({"role": "user", "content": user_message})

    def generate():
        full_response = ""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation,
            stream=True
        )

        for chunk in response:
            if chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_response += token
                yield token

        conversation.append({
            "role": "assistant",
            "content": full_response
        })

    return Response(stream_with_context(generate()), mimetype="text/plain")


if __name__ == "__main__":
    app.run(debug=True)