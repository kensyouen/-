import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
import feedparser
import urllib.parse

# === ページ設定 ===
st.set_page_config(page_title="FW Compass", page_icon="🧭", layout="centered")

# ==========================================
# 🎨 カスタムCSS（iPhoneアプリ風デザイン）
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #F2F2F7; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    .ios-card { background-color: #FFFFFF; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.04); }
    .metric-label { font-size: 13px; color: #8E8E93; margin-bottom: 4px; font-weight: 600; }
    .metric-value { font-size: 24px; font-weight: 700; margin-bottom: 4px; }
    .sub-metric { font-size: 12px; color: #8E8E93; line-height: 1.5; }
    .goal-badge { background-color: #FFF4E5; color: #FF9500; padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 700; display: inline-block; margin-bottom: 16px; }
    .stButton>button { border-radius: 12px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 🔒 パスワード認証機能
# ==========================================
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if not st.session_state.password_correct:
        st.markdown('<div class="ios-card" style="text-align:center;"><h2>🧭 FW Compass</h2><p style="color:#8E8E93; font-size:14px;">ご家庭専用のプライベートツールです</p></div>', unsafe_allow_html=True)
        pwd = st.text_input("パスワード", type="password", placeholder="パスワードを入力", label_visibility="collapsed")
        expected_password = st.secrets.get("APP_PASSWORD", "secret123") 
        if st.button("ログイン", type="primary", use_container_width=True):
            if pwd == expected_password:
                st.session_state.password_correct = True
                st.rerun() 
            else:
                st.error("❌ パスワードが間違っています。")
        return False
    return True

if not check_password():
    st.stop()


# ==========================================
# 🤖 Gemini AI & ニュース取得機能（政策＆家計連動）
# ==========================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.warning("⚠️ Gemini APIキーが設定されていません。AI機能を使う場合はSecretsに `GEMINI_API_KEY` を登録してください。")

@st.cache_data(ttl=3600)
def get_latest_economic_news():
    """Google Newsから家計・政策・経済に関連する最新ニュースを取得"""
    # 検索キーワードを政策や家計に直結するものに強化
    query = "日本経済 OR 円安 OR 増税 OR 減税 OR 給付金 OR 子育て支援 OR 教育無償化 OR 関税"
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ja&gl=JP&ceid=JP:ja"
    
    feed = feedparser.parse(url)
    # 関連性の高い最新7件を抽出
    news_titles = [entry.title for entry in feed.entries[:7]]
    return "\n".join(news_titles)

def generate_ai_fp_advice(actual_cash, actual_nisa, diff_total, inc_total, expenses):
    news_text = get_latest_economic_news()
    
    prompt = f"""
    あなたはトップクラスの専属ファイナンシャルプランナーです。
    以下の「クライアントの家計データ」と「最新の経済・政策ニュース」を掛け合わせ、生活防衛と資産形成の最適解をマークダウン形式で提案してください。

    【クライアントの家計データ】
    - 現在の現金: {actual_cash}万円
    - 現在のNISA: {actual_nisa}万円
    - 予定総資産との乖離: {diff_total}万円
    - 世帯年収: {inc_total}万円
    - 月間支出: 食費 {expenses['food']}万, 光熱費 {expenses['util']}万, 通信費 {expenses['tele']}万, 車 {expenses['car']}万, 教育 {expenses['edu']}万, 妻小遣い {expenses['wife']}万, バッファ(使途不明) {expenses['free']}万
    - NISA年間積立額: {expenses['invest']}万円

    【最新の経済・政策ニュース】
    {news_text}

    【出力構成（必ず以下の4点を含める）】
    1. 📰 **政策・経済トレンドと家計への影響**：ニュースにある税制、給付金、為替、教育支援などのトレンドが、このご家庭の生活費や教育費にどう影響するか具体的に解説してください。
    2. 🛡️ **生活防衛と投資戦略**：インフレや政策を踏まえ、現金の守り方とNISA増額などの攻め方を提案してください。
    3. 👏 **家計の強みと弱点の分析**：優秀な支出項目（光熱費や通信費など）を褒めつつ、弱点（食費など）に対する具体的な改善策を提案してください（バッファ枠の活用も含む）。
    4. 🔥 **総括エール**：最後にクライアントを励ます言葉を添えてください。
    """
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text


# ==========================================
# 💾 スプレッドシート連携機能
# ==========================================
@st.cache_resource
def get_gsheet_client():
    key_dict = json.loads(st.secrets["GCP_KEY"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(key_dict, scopes=scopes)
    return gspread.authorize(creds)

def load_data():
    try:
        client = get_gsheet_client()
        sheet = client.open_by_url(st.secrets["SHEET_URL"]).sheet1
        records = sheet.get_all_records()
        if records: return records[0] 
    except Exception:
        pass
    return None

def save_data(data_dict):
    try:
        client = get_gsheet_client()
        sheet = client.open_by_url(st.secrets["SHEET_URL"]).sheet1
        headers = list(data_dict.keys())
        values = list(data_dict.values())
        sheet.clear()
        sheet.update(values=[headers, values], range_name='A1')
    except Exception as e:
        st.error(f"保存失敗: {e}")


# ==========================================
# 📊 シミュレーション設定・初期化
# ==========================================
ORIGINAL_GOAL_AGE = "47歳"
TOLERANCE_MAN = 50 

future_data = {
    40: {'income': 1006, 'extra': 0}, 41: {'income': 1014, 'extra': 0},
    42: {'income': 1022, 'extra': 0}, 43: {'income': 1030, 'extra': 0},
    44: {'income': 1038, 'extra': 200}, 45: {'income': 1056, 'extra': 8},   
    46: {'income': 1065, 'extra': 8}, 47: {'income': 1074, 'extra': 8},
    48: {'income': 1046, 'extra': 128}, 49: {'income': 1056, 'extra': 112}, 
    50: {'income': 1042, 'extra': -38}, 51: {'income': 1050, 'extra': -38}, 52: {'income': 1050, 'extra': -38}
}

if "data_loaded" not in st.session_state:
    saved_data = load_data()
    if saved_data:
        st.session_state.actual_cash = saved_data.get("actual_cash", 1880.0)
        st.session_state.actual_nisa = saved_data.get("actual_nisa", 370.0)
        st.session_state.inc_husband_m = saved_data.get("inc_h_m", 43.0)
        st.session_state.inc_husband_b = saved_data.get("inc_h_b", 130.0)
        st.session_state.inc_wife_m = saved_data.get("inc_w_m", 16.0)
        st.session_state.inc_wife_b = saved_data.get("inc_w_b", 60.0)
        st.session_state.exp_food = saved_data.get("exp_food", 14.8)
        st.session_state.exp_util = saved_data.get("exp_util", 1.5)
        st.session_state.exp_tele = saved_data.get("exp_tele", 1.1)
        st.session_state.exp_car = saved_data.get("exp_car", 6.0)
        st.session_state.exp_edu = saved_data.get("exp_edu", 5.4)
        st.session_state.exp_ins = saved_data.get("exp_ins", 0.7)
        st.session_state.exp_wife = saved_data.get("exp_wife", 1.9)
        st.session_state.exp_free = saved_data.get("exp_free", 17.3)
        st.session_state.invest_amount = saved_data.get("invest_amount", 60.0)
    else:
        st.session_state.actual_cash = 1880.0
        st.session_state.actual_nisa = 370.0
        st.session_state.inc_husband_m, st.session_state.inc_husband_b = 43.0, 130.0
        st.session_state.inc_wife_m, st.session_state.inc_wife_b = 16.0, 60.0
        st.session_state.exp_food, st.session_state.exp_util, st.session_state.exp_tele = 14.8, 1.5, 1.1
        st.session_state.exp_car, st.session_state.exp_edu, st.session_state.exp_ins = 6.0, 5.4, 0.7
        st.session_state.exp_wife, st.session_state.exp_free = 1.9, 17.3
        st.session_state.invest_amount = 60.0
    st.session_state.data_loaded = True

def trigger_save():
    save_data({
        "actual_cash": st.session_state.actual_cash, "actual_nisa": st.session_state.actual_nisa,
        "inc_h_m": st.session_state.inc_husband_m, "inc_h_b": st.session_state.inc_husband_b,
        "inc_w_m": st.session_state.inc_wife_m, "inc_w_b": st.session_state.inc_wife_b,
        "exp_food": st.session_state.exp_food, "exp_util": st.session_state.exp_util,
        "exp_tele": st.session_state.exp_tele, "exp_car": st.session_state.exp_car,
        "exp_edu": st.session_state.exp_edu, "exp_ins": st.session_state.exp_ins,
        "exp_wife": st.session_state.exp_wife, "exp_free": st.session_state.exp_free,
        "invest_amount": st.session_state.invest_amount
    })

def save_home_assets():
    st.session_state.actual_cash = st.session_state.input_cash
    st.session_state.actual_nisa = st.session_state.input_nisa
    trigger_save()

def save_plan_settings():
    st.session_state.inc_husband_m = st.session_state.input_inc_h_m
    st.session_state.inc_husband_b = st.session_state.input_inc_h_b
    st.session_state.inc_wife_m = st.session_state.input_inc_w_m
    st.session_state.inc_wife_b = st.session_state.input_inc_w_b
    st.session_state.exp_food = st.session_state.input_exp_food
    st.session_state.exp_util = st.session_state.input_exp_util
    st.session_state.exp_tele = st.session_state.input_exp_tele
    st.session_state.exp_car = st.session_state.input_exp_car
    st.session_state.exp_edu = st.session_state.input_exp_edu
    st.session_state.exp_ins = st.session_state.input_exp_ins
    st.session_state.exp_wife = st.session_state.input_exp_wife
    st.session_state.exp_free = st.session_state.input_exp_free
    st.session_state.invest_amount = st.session_state.input_invest
    trigger_save()

new_total_inc = (st.session_state.inc_husband_m * 12 + st.session_state.inc_husband_b) + (st.session_state.inc_wife_m * 12 + st.session_state.inc_wife_b)
income_diff = new_total_inc - 898
monthly_exp = st.session_state.exp_food + st.session_state.exp_util + st.session_state.exp_tele + st.session_state.exp_car + st.session_state.exp_edu + st.session_state.exp_ins + st.session_state.exp_wife + st.session_state.exp_free
living_cost_annual = monthly_exp * 12

def run_simulation():
    sim_cash = st.session_state.actual_cash
    sim_nisa = st.session_state.actual_nisa
    current_living = living_cost_annual
    invest = st.session_state.invest_amount
    loan_annual = 183 
    is_goal_reached = False
    goal_age = "未達成(50歳以降)"
    records = []
    
    total = int(sim_cash + sim_nisa)
    if total >= 4000: goal_age = "39歳"; is_goal_reached = True
        
    records.append({"年齢": "39歳(現)", "家族年齢": "35/10/6/2", "収入(万)": int(898 + income_diff), "支出(万)": 0, "総資産(万)": total})
    
    for age in range(40, 53):
        data = future_data[age]
        current_living = current_living * 1.02 
        total_expense = current_living + loan_annual + data['extra']
        current_income = data['income'] + income_diff 
        
        sim_cash = sim_cash + current_income - total_expense - invest
        sim_nisa = (sim_nisa * 1.05) + invest
        total = int(sim_cash + sim_nisa)
        
        if total >= 4000 and not is_goal_reached: goal_age = f"{age}歳"; is_goal_reached = True
            
        records.append({"年齢": f"{age}歳", "家族年齢": f"{age-4}/{age-29}/{age-33}/{age-37}", "収入(万)": int(current_income), "支出(万)": int(total_expense), "総資産(万)": total})
        
    return goal_age, pd.DataFrame(records)

goal_age_result, df_plan = run_simulation()


# ==========================================
# 📱 UI描画
# ==========================================
st.markdown("<h3 style='text-align:center; color:#1C1C1E; margin-bottom:20px;'>🧭 FW Compass</h3>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["📊 ダッシュボード", "⚙️ 詳細設定"])

with tab1:
    badge_text = f"🎯 当初目標：{ORIGINAL_GOAL_AGE} ➔ 最新予測：{goal_age_result}" if goal_age_result != ORIGINAL_GOAL_AGE else f"🎯 当初目標：{ORIGINAL_GOAL_AGE} (予定通り!)"
    target_cash, target_nisa = 1880, 370
    target_total = target_cash + target_nisa
    actual_total = st.session_state.actual_cash + st.session_state.actual_nisa
    actual_color = "#007AFF" if actual_total >= target_total - TOLERANCE_MAN else "#FF3B30"
    
    html_card = f"""
    <div class="ios-card" style="text-align:center;">
        <div class="goal-badge">{badge_text}</div>
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="width:45%;">
                <div class="metric-label">予定総資産 (現時点)</div>
                <div class="metric-value" style="color:#1C1C1E;">{target_total:,} <span style="font-size:14px;">万円</span></div>
                <div class="sub-metric">現金: {target_cash:,}万<br>投資: {target_nisa:,}万</div>
            </div>
            <div style="font-size:18px; font-weight:700; color:#D1D1D6;">VS</div>
            <div style="width:45%;">
                <div class="metric-label">実際の総資産</div>
                <div class="metric-value" style="color:{actual_color};">{int(actual_total):,} <span style="font-size:14px;">万円</span></div>
                <div class="sub-metric">現金: {int(st.session_state.actual_cash):,}万<br>投資: {int(st.session_state.actual_nisa):,}万</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html_card, unsafe_allow_html=True)

    st.markdown("<div class='ios-card'>", unsafe_allow_html=True)
    st.markdown("##### 🔄 現在の資産を更新")
    col_input1, col_input2 = st.columns(2)
    with col_input1: st.number_input("💰 現金・預金（万円）", value=float(st.session_state.actual_cash), key="input_cash", step=10.0)
    with col_input2: st.number_input("📈 NISA残高（万円）", value=float(st.session_state.actual_nisa), key="input_nisa", step=10.0)
    st.button("クラウドに保存して再計算", on_click=save_home_assets, type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    diff_total = actual_total - target_total
    
    if diff_total < -TOLERANCE_MAN:
        st.error(f"⚠️ 予定を {abs(int(diff_total)):,} 万円 下回っています。")
        
        # 🤖 AIアドバイス生成ボタン
        if st.button("✨ 専属AI-FPにアドバイスを求める", type="primary"):
            if "GEMINI_API_KEY" not in st.secrets:
                st.error("Secretsに GEMINI_API_KEY が設定されていません！")
            else:
                with st.spinner("最新の政策・経済ニュースと家計データを分析しています..."):
                    try:
                        expenses_data = {
                            'food': st.session_state.exp_food, 'util': st.session_state.exp_util,
                            'tele': st.session_state.exp_tele, 'car': st.session_state.exp_car,
                            'edu': st.session_state.exp_edu, 'wife': st.session_state.exp_wife,
                            'free': st.session_state.exp_free, 'invest': st.session_state.invest_amount
                        }
                        ai_advice = generate_ai_fp_advice(
                            st.session_state.actual_cash, st.session_state.actual_nisa, 
                            diff_total, int(new_total_inc), expenses_data
                        )
                        st.success("分析が完了しました！")
                        st.markdown("<div class='ios-card' style='background-color:#F8FAFC; border-left:4px solid #3498db;'>", unsafe_allow_html=True)
                        st.markdown(ai_advice)
                        st.markdown("</div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"AIの呼び出しに失敗しました。エラー詳細: {e}")
                    
        # 今後の高額スポット支出アラート（固定表示）
        alerts = [f"- **{age}歳の年** に特別支出 **約{data['extra']}万円**" for age, data in future_data.items() if data['extra'] >= 100]
        if alerts:
            st.warning("⚠️ **【重要】数年以内の高額支出アラート**\n" + "\n".join(alerts))


with tab2:
    st.markdown("<div class='ios-card'>", unsafe_allow_html=True)
    st.markdown("### ⚙️ 家計のパラメータ設定")
    st.caption(f"現在のベース：世帯年収 {int(new_total_inc)}万円 ／ 生活費 {int(living_cost_annual)}万円(年) ／ NISA積立 {int(st.session_state.invest_amount)}万円(年)")
    
    with st.expander("📝 収入・支出を細かく編集する", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.number_input("夫 月収", value=float(st.session_state.inc_husband_m), key="input_inc_h_m", step=1.0)
            st.number_input("夫 ボーナス", value=float(st.session_state.inc_husband_b), key="input_inc_h_b", step=5.0)
        with c2:
            st.number_input("妻 月収", value=float(st.session_state.inc_wife_m), key="input_inc_w_m", step=1.0)
            st.number_input("妻 ボーナス", value=float(st.session_state.inc_wife_b), key="input_inc_w_b", step=5.0)
            
        c3, c4 = st.columns(2)
        with c3:
            st.number_input("食費・日用品", value=float(st.session_state.exp_food), key="input_exp_food", step=1.0)
            st.number_input("水道・光熱費", value=float(st.session_state.exp_util), key="input_exp_util", step=0.1)
            st.number_input("通信費", value=float(st.session_state.exp_tele), key="input_exp_tele", step=0.1)
            st.number_input("車関連(保険・積立)", value=float(st.session_state.exp_car), key="input_exp_car", step=1.0)
        with c4:
            st.number_input("教育費(塾・学童)", value=float(st.session_state.exp_edu), key="input_exp_edu", step=1.0)
            st.number_input("保険料", value=float(st.session_state.exp_ins), key="input_exp_ins", step=0.1)
            st.number_input("妻お小遣い", value=float(st.session_state.exp_wife), key="input_exp_wife", step=0.1)
            st.number_input("使途不明金", value=float(st.session_state.exp_free), key="input_exp_free", step=1.0)
            
        st.number_input("NISA年間積立額", value=float(st.session_state.invest_amount), key="input_invest", step=5.0)
        st.button("設定を保存して再計算", on_click=save_plan_settings, type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### 📋 11年間ロードマップ（データ一覧）")
    st.dataframe(df_plan, use_container_width=True, hide_index=True)
