import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials

# === ページ設定（スマホライクなCenteredレイアウトに変更） ===
st.set_page_config(page_title="FW Compass", page_icon="🧭", layout="centered")

# ==========================================
# 🎨 カスタムCSS（iPhoneアプリ風のスタイリッシュなUI）
# ==========================================
st.markdown("""
<style>
    /* iOS風の背景色とフォント */
    .stApp {
        background-color: #F2F2F7;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    /* iOS風の白カードデザイン */
    .ios-card {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    }
    /* メトリック（数値）部分のテキストスタイル */
    .metric-label { font-size: 13px; color: #8E8E93; margin-bottom: 4px; font-weight: 600; }
    .metric-value { font-size: 24px; font-weight: 700; margin-bottom: 4px; }
    .sub-metric { font-size: 12px; color: #8E8E93; line-height: 1.5; }
    /* バッジ（達成年齢表示） */
    .goal-badge {
        background-color: #FFF4E5;
        color: #FF9500;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 16px;
    }
    /* ボタンの角丸 */
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
# 💾 データベース（スプレッドシート）連携機能
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

# 40歳〜52歳の特別支出データ（100万以上はFPアドバイスで自動警告されます）
future_data = {
    40: {'income': 1006, 'extra': 0},
    41: {'income': 1014, 'extra': 0},
    42: {'income': 1022, 'extra': 0},
    43: {'income': 1030, 'extra': 0},
    44: {'income': 1038, 'extra': 200}, # 修繕150万 + 高校準備50万
    45: {'income': 1056, 'extra': 8},   
    46: {'income': 1065, 'extra': 8},
    47: {'income': 1074, 'extra': 8},
    48: {'income': 1046, 'extra': 128}, # 専門学校等
    49: {'income': 1056, 'extra': 112}, 
    50: {'income': 1042, 'extra': -38},
    51: {'income': 1050, 'extra': -38},
    52: {'income': 1050, 'extra': -38}
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
        st.session_state.inc_husband_m = 43.0
        st.session_state.inc_husband_b = 130.0
        st.session_state.inc_wife_m = 16.0
        st.session_state.inc_wife_b = 60.0
        st.session_state.exp_food = 14.8
        st.session_state.exp_util = 1.5
        st.session_state.exp_tele = 1.1
        st.session_state.exp_car = 6.0
        st.session_state.exp_edu = 5.4
        st.session_state.exp_ins = 0.7
        st.session_state.exp_wife = 1.9
        st.session_state.exp_free = 17.3
        st.session_state.invest_amount = 60.0
    st.session_state.data_loaded = True

# --- 保存用の即時コールバック関数（連続更新バグ防止策） ---
def trigger_save():
    data_to_save = {
        "actual_cash": st.session_state.actual_cash,
        "actual_nisa": st.session_state.actual_nisa,
        "inc_h_m": st.session_state.inc_husband_m,
        "inc_h_b": st.session_state.inc_husband_b,
        "inc_w_m": st.session_state.inc_wife_m,
        "inc_w_b": st.session_state.inc_wife_b,
        "exp_food": st.session_state.exp_food,
        "exp_util": st.session_state.exp_util,
        "exp_tele": st.session_state.exp_tele,
        "exp_car": st.session_state.exp_car,
        "exp_edu": st.session_state.exp_edu,
        "exp_ins": st.session_state.exp_ins,
        "exp_wife": st.session_state.exp_wife,
        "exp_free": st.session_state.exp_free,
        "invest_amount": st.session_state.invest_amount
    }
    save_data(data_to_save)

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

# 計算処理
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
    if total >= 4000:
        goal_age = "39歳"
        is_goal_reached = True
        
    records.append({
        "年齢": "39歳(現)", "家族年齢": "35/10/6/2", "収入(万)": int(898 + income_diff), 
        "支出(万)": 0, "総資産(万)": total
    })
    
    for age in range(40, 53):
        data = future_data[age]
        current_living = current_living * 1.02 
        total_expense = current_living + loan_annual + data['extra']
        current_income = data['income'] + income_diff 
        
        sim_cash = sim_cash + current_income - total_expense - invest
        sim_nisa
