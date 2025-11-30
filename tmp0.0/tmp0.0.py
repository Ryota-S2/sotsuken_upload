import json
from json import loads
import re
import random
import os
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI
import csv

# ===== CSV の絶対パスを自動取得 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "Book1.csv")

# ===== 解説CSV読み込み関数（nullバイト対応・ヘッダーなし対応）=====
def load_explanations_from_csv(file_or_bytes):
    # file_or_bytes が bytes の場合（st.file_uploader）
    if isinstance(file_or_bytes, bytes):
        try:
            return file_or_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_or_bytes.decode("cp932")  # ← SHIFT-JIS の別名

    # ファイルパスの場合
    with open(file_or_bytes, "rb") as f:
        content = f.read()
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return content.decode("cp932")

# ===== OpenAI API キーの読み込み =====
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# ===== 説明文の読み込みとセッション保持 =====
if "explanations" not in st.session_state:
    if not os.path.exists(CSV_PATH):
        st.error(f"CSV ファイルが見つかりません: {CSV_PATH}")
    st.session_state.explanations = load_explanations_from_csv(CSV_PATH)

explanations = st.session_state.explanations

# ===== クイズの出題処理 =====
if "question_data" not in st.session_state or st.session_state.get("next_question", False):
    QuestionNum = random.randint(0, len(explanations) - 1)
    SelectedQuestion = explanations[QuestionNum]

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": "あなたはクイズの出題者です.以下の文から四択問題を作成してください。本文内容に基づいた問題にしてください。出力はJSON形式で返してください。"
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
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
        temperature=0.0
    )

    # ===== GPTの応答からJSON抽出 =====
    output_text = response.choices[0].message.content
    match = re.search(r"\{.*\}", output_text, re.DOTALL)

    if match:
        try:
            json_str = match.group()
            data = loads(json_str)
            st.session_state.question_data = data
            st.session_state.explanation = SelectedQuestion
            st.session_state.next_question = False
        except Exception as e:
            st.error(f"JSON読み込み失敗: {e}")
    else:
        st.error("JSON形式の出力が見つかりませんでした。")

# ===== UI表示 =====
st.title("兵庫学検定試験対策ツール Temperature=0.0")
st.write("以下の問題に答えてください：")
st.write(st.session_state.question_data['Question'])

choices = [
    f"1. {st.session_state.question_data['Choice1']}",
    f"2. {st.session_state.question_data['Choice2']}",
    f"3. {st.session_state.question_data['Choice3']}",
    f"4. {st.session_state.question_data['Choice4']}"
]

selected = st.radio("選択肢：", choices)

if st.button("解答"):
    selected_index = choices.index(selected) + 1
    if selected_index == st.session_state.question_data["CorrectAnswer"]:
        st.success("正解！")
    else:
        st.error("不正解…")
        st.info(f"解説：{st.session_state.explanation}")

if st.button("次の問題へ"):
    st.session_state.next_question = True
    st.rerun()
