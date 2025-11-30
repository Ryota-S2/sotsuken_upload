import json
from json import loads
import re
import random
import os
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI
import chardet
import pandas as pd

# ===== CSV パス =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "Book1.csv")

# ===== 文字コード自動判定して読み込む関数 =====
def load_csv_auto(path):
    with open(path, "rb") as f:
        raw = f.read()

    enc = chardet.detect(raw)["encoding"]
    df = pd.read_csv(pd.io.common.BytesIO(raw), encoding=enc, header=None)
    return df

# ===== OpenAI API =====
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

st.title("📘 CSV教材 → 四択問題生成アプリ（Temperature=0.0）")

# ===== Book1.csv を自動読み込み =====
if not os.path.exists(CSV_PATH):
    st.error(f"Book1.csv が見つかりません: {CSV_PATH}")
    st.stop()

df = load_csv_auto(CSV_PATH)

# ===== 1列目のみ使用 =====
explanations_list = df[0].dropna().astype(str).tolist()

# =====問題生成準備=====
if "question_data" not in st.session_state:
    st.session_state.next_question = True

# =====問題生成=====
if st.session_state.next_question:

    SelectedQuestion = random.choice(explanations_list)

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": "あなたはクイズの出題者です。与えられた文章から四択問題をJSON形式で作成してください。"
            },
            {"role": "user", "content": SelectedQuestion},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "QuestionData",
                "schema": {
                    "type": "object",
                    "properties": {
                        "Question": {"type": "string"},
                        "Choice1": {"type": "string"},
                        "Choice2": {"type": "string"},
                        "Choice3": {"type": "string"},
                        "Choice4": {"type": "string"},
                        "CorrectAnswer": {"type": "number"},
                    },
                    "required": ["Question", "Choice1", "Choice2", "Choice3", "Choice4", "CorrectAnswer"],
                },
                "strict": True,
            },
        },
        temperature=0.0
    )

    output_text = response.choices[0].message.content
    data = loads(output_text)

    st.session_state.question_data = data
    st.session_state.explanation = SelectedQuestion
    st.session_state.next_question = False

# ===== UI =====
q = st.session_state.question_data

st.subheader("🔍 問題")
st.write(q["Question"])

choices = [
    f"1. {q['Choice1']}",
    f"2. {q['Choice2']}",
    f"3. {q['Choice3']}",
    f"4. {q['Choice4']}"
]

selected = st.radio("選択肢：", choices)

if st.button("解答"):
    selected_index = choices.index(selected) + 1
    if selected_index == q["CorrectAnswer"]:
        st.success("🎉 正解！")
    else:
        st.error("❌ 不正解")
    st.info(f"📘 元の文章：\n{st.session_state.explanation}")

if st.button("次の問題へ"):
    st.session_state.next_question = True
    st.rerun()
