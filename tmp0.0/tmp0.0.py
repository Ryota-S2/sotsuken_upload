import streamlit as st
import os
import csv

# ==========================
#  CSV パス設定
# ==========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "Book1.csv")


# ==========================
#  CSV 読み込み関数（完全版）
# ==========================
def load_explanations_from_csv(path):
    """
    - バイナリで読み込み null バイト除去
    - utf-8 / cp932 / shift_jis / latin1 の順でデコードを試す
    - csv.reader で読み込む
    - Streamlit にデバッグ情報を表示
    """
    st.write("===== CSV DEBUG START =====")

    if not os.path.exists(path):
        st.error(f"CSV not found at: {path}")
        raise FileNotFoundError(f"CSV not found: {path}")

    st.write("📁  CSV path:", path)

    # バイナリ読み込み（null byte 対策）
    with open(path, "rb") as f:
        raw = f.read().replace(b'\x00', b'')

    # エンコーディング候補
    encodings = ["utf-8", "cp932", "shift_jis", "latin1"]

    text = None
    used_encoding = None

    for enc in encodings:
        try:
            text = raw.decode(enc)
            used_encoding = enc
            break
        except Exception:
            continue

    # 最終救済（文字化け回避）
    if text is None:
        text = raw.decode("utf-8", errors="replace")
        used_encoding = "utf-8(replaced)"

    st.write("🧾  Detected encoding:", used_encoding)

    # CSV パース
    rows = list(csv.reader(text.splitlines()))
    st.write("🔢  Total rows:", len(rows))
    st.write("📝  First few rows (raw):")
    st.write(rows[:8])

    # 1列目を説明文とする
    explanations = []
    for row in rows:
        if not row:
            continue
        explanations.append(row[0])

    st.write("📚  Parsed explanations sample:", explanations[:8])
    st.write("===== CSV DEBUG END =====")

    return explanations


# ==========================
#  Streamlit UI
# ==========================
def main():
    st.title("CSV 読み込みデバッグアプリ（完全版）")

    st.write("このアプリは Book1.csv を正しく読み込めているか検証します。")

    # ==========================
    #  CSV 読み込み
    # ==========================
    try:
        explanations = load_explanations_from_csv(CSV_PATH)
        st.success("CSV を正常に読み込みました！")
    except Exception as e:
        st.error(f"CSV 読み込みエラー: {e}")
        return

    # ==========================
    #  表示
    # ==========================
    st.subheader("読み込んだデータ（先頭20件）")
    for i, ex in enumerate(explanations[:20]):
        st.write(f"{i+1}. {ex}")


if __name__ == "__main__":
    main()
