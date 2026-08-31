import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials

# === ページ設定（プロ仕様のデザインに変更） ===
st.set_page_config(page_title="Family Wealth Compass", page_icon="🧭", layout="wide")

# カスタムCSS（高級感のあるネイビーとゴールド基調）
st.markdown("""
<style>
    /* メトリック（数字）のデザイン */
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    /* 警告や成功メッセージのデザイン */
    .stAlert { border-radius: 8px; }
    /* タブの文字色 */
    .stTabs [data-baseweb="tab-list"] button { font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 🔒 パスワード認証機能
# ==========================================
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if not st.session_state.password_correct:
        st.info("🔒 Private Tool - 認証が必要です")
        pwd = st.text_input("パスワードを入力してください", type="password")
        expected_password = st.secrets.get("APP_PASSWORD", "secret123") 
        if st.button("ログイン"):
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
    """Secretsの鍵を使ってスプレッドシートに接続する"""
    key_dict = json.loads(st.secrets["GCP_KEY"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(key_dict, scopes=scopes)
    return gspread.authorize(creds)

def load_data():
    """スプレッドシートからデータを読み込む"""
    try:
        client = get_gsheet_client()
        sheet = client.open_by_url(st.secrets["SHEET_URL"]).sheet1
        records = sheet.get_all_records()
        if records:
            return records[0] # 1行目のデータを辞書として返す
    except Exception as e:
        st.warning(f"データの読み込みに失敗しました（初回は無視してOKです）: {e}")
    return None

def save_data(data_dict):
    """スプレッドシートにデータを保存する"""
    try:
        client = get_gsheet_client()
        sheet = client.open_by_url(st.secrets["SHEET_URL"]).sheet1
        headers = list(data_dict.keys())
        values = list(data_dict.values())
        sheet.clear()
        # スプレッドシートの1行目に項目名、2行目に数値を書き込む
        sheet.update(values=[headers, values], range_name='A1')
    except Exception as e:
        st.error(f"データの保存に失敗しました: {e}")


# ==========================================
# 📊 シミュレーション設定
# ==========================================
ORIGINAL_GOAL_AGE = "47歳"

future_data = {
    40: {'income': 1006, 'extra': 0},
    41: {'income': 1014, 'extra': 0},
    42: {'income': 1022, 'extra': 0},
    43: {'income': 1030, 'extra': 0},
    44: {'income': 1038, 'extra': 200},
    45: {'income': 1056, 'extra': 8},   
    46: {'income': 1065, 'extra': 8},
    47: {'income': 1074, 'extra': 8},
    48: {'income': 1046, 'extra': 128},
    49: {'income': 1056, 'extra': 112}, 
    50: {'income': 1042, 'extra': -38},
    51: {'income': 1050, 'extra': -38},
    52: {'income': 1050, 'extra': -38}
}

# --- データの初期化（ロード） ---
if "data_loaded" not in st.session_state:
    saved_data = load_data()
    if saved_data:
        # スプレッドシートのデータがあれば反映
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
        # 初回起動時のデフォルト値
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

# --- 毎回の計算 ---
# 現在の設定値から年収と生活費を計算
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
        "年齢": "39歳(現)", 
        "家族年齢": "35/10/6/2",
        "収入(万)": int(898 + income_diff), 
        "支出(万)": 0, 
        "現金(万)": int(sim_cash),
        "NISA(万)": int(sim_nisa),
        "総資産(万)": total
    })
    
    for age in range(40, 53):
        data = future_data[age]
        current_living = current_living * 1.02 
        total_expense = current_living + loan_annual + data['extra']
        current_income = data['income'] + income_diff 
        
        sim_cash = sim_cash + current_income - total_expense - invest
        sim_nisa = (sim_nisa * 1.05) + invest
        total = int(sim_cash + sim_nisa)
        
        if total >= 4000 and not is_goal_reached:
            goal_age = f"{age}歳"
            is_goal_reached = True
            
        records.append({
            "年齢": f"{age}歳", 
            "家族年齢": f"{age-4}/{age-29}/{age-33}/{age-37}",
            "収入(万)": int(current_income), 
            "支出(万)": int(total_expense), 
            "現金(万)": int(sim_cash),
            "NISA(万)": int(sim_nisa),
            "総資産(万)": total
        })
        
    df = pd.DataFrame(records)
    return goal_age, df

goal_age_result, df_plan = run_simulation()

def trigger_save():
    """現在の状態をスプレッドシートに保存する"""
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


# ==========================================
# 🖥️ アプリ画面の構築
# ==========================================
st.markdown("<h2 style='color:#1E3A8A; font-weight:800;'>🧭 Family Wealth Compass</h2>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["📊 資産ダッシュボード", "⚙️ 詳細シミュレーション設定"])

with tab1:
    # --- ヘッダー部分 ---
    if goal_age_result == ORIGINAL_GOAL_AGE:
        st.success(f"**🎯 達成予測：{ORIGINAL_GOAL_AGE} （計画通りに推移しています）**")
    else:
        st.warning(f"**🎯 達成予測：{ORIGINAL_GOAL_AGE} ➔ 【 {goal_age_result} 】へ修正されました**")
    
    # --- メトリック表示 ---
    col1, col2, col3 = st.columns([1, 0.2, 1])
    with col1:
        st.metric("予定総資産 (現時点)", "2,250 万円")
    with col2:
        st.markdown("<h2 style='text-align:center; color:#B0BEC5; margin-top:10px;'>VS</h2>", unsafe_allow_html=True)
    with col3:
        actual_total = st.session_state.actual_cash + st.session_state.actual_nisa
        st.metric("現在の総資産", f"{actual_total:,.0f} 万円", delta=int(actual_total - 2250))
    
    st.divider()

    # --- グラフ表示（商業用アプリ風の視覚化） ---
    st.markdown("#### 📈 資産推移シミュレーション")
    st.caption("現金と投資(NISA)の成長推移グラフ")
    # グラフ用にデータを整形
    df_chart = df_plan[["年齢", "現金(万)", "NISA(万)"]].copy()
    df_chart.set_index("年齢", inplace=True)
    # Streamlitのネイティブ機能で積み上げ棒グラフや折れ線グラフを表示
    st.bar_chart(df_chart, color=["#3498db", "#e74c3c"])
    
    st.divider()

    # --- 入力・分析エリア ---
    st.markdown("#### 🔄 現在の資産を更新")
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        new_cash = st.number_input("💰 現金・預金（万円）", value=float(st.session_state.actual_cash), step=10.0)
    with col_input2:
        new_nisa = st.number_input("📈 NISA残高（万円）", value=float(st.session_state.actual_nisa), step=10.0)
    
    if st.button("資産を更新し、クラウドに保存する", type="primary", use_container_width=True):
        st.session_state.actual_cash = new_cash
        st.session_state.actual_nisa = new_nisa
        trigger_save() # スプレッドシートに保存
        st.rerun()

    # --- FPアドバイスエリア ---
    diff_total = (st.session_state.actual_cash + st.session_state.actual_nisa) - 2250
    TOLERANCE = 50
    
    if diff_total < -TOLERANCE:
        st.error(f"⚠️ 予定を {abs(diff_total)} 万円 下回っています。")
        with st.expander("💡 ファイナンシャルプランナーからの改善提案", expanded=True):
            st.markdown("##### 👩‍💼 資産リカバリーのためのアドバイス")
            st.markdown(f"**① 支出の見直し:** 使途不明金（月{st.session_state.exp_free}万）から投資へ資金をシフトさせましょう。")
            if st.session_state.actual_cash > 1500:
                st.markdown(f"**② 投資の増額:** 現金が{st.session_state.actual_cash}万と潤沢です。NISA積立を月10万円に増額し、複利で遅れを取り戻すことを推奨します。")
            st.markdown("**③ 高額支出アラート:** 44歳の住宅修繕、48歳以降の教育費ピークに備え、NISAは崩さず現金をキープしてください。")


with tab2:
    st.markdown("### ⚙️ 家計のパラメータ設定")
    st.info(f"💡 現在のベース：世帯年収 **{int(new_total_inc)}万円** ／ 生活費 **{int(living_cost_annual)}万円**(年) ／ NISA積立 **{int(st.session_state.invest_amount)}万円**(年)")
    
    with st.expander("📝 収入・支出の項目を細かく編集する", expanded=True):
        st.markdown("#### 👩‍💼 【収入】（手取り / 単位：万円）")
        c1, c2 = st.columns(2)
        with c1:
            new_inc_h_m = st.number_input("夫 月収", value=float(st.session_state.inc_husband_m), step=1.0)
            new_inc_h_b = st.number_input("夫 ボーナス(年)", value=float(st.session_state.inc_husband_b), step=5.0)
        with c2:
            new_inc_w_m = st.number_input("妻 月収", value=float(st.session_state.inc_wife_m), step=1.0)
            new_inc_w_b = st.number_input("妻 ボーナス(年)", value=float(st.session_state.inc_wife_b), step=5.0)
            
        st.markdown("#### 🛒 【支出】（月額 / 単位：万円）")
        c3, c4 = st.columns(2)
        with c3:
            new_exp_food = st.number_input("食費・日用品", value=float(st.session_state.exp_food), step=1.0)
            new_exp_util = st.number_input("水道・光熱費", value=float(st.session_state.exp_util), step=0.1)
            new_exp_tele = st.number_input("通信費", value=float(st.session_state.exp_tele), step=0.1)
            new_exp_car  = st.number_input("車関連(保険・積立)", value=float(st.session_state.exp_car), step=1.0)
        with c4:
            new_exp_edu  = st.number_input("教育費(塾・学童等)", value=float(st.session_state.exp_edu), step=1.0)
            new_exp_ins  = st.number_input("保険料", value=float(st.session_state.exp_ins), step=0.1)
            new_exp_wife = st.number_input("妻お小遣い", value=float(st.session_state.exp_wife), step=0.1)
            new_exp_free = st.number_input("使途不明金(バッファ)", value=float(st.session_state.exp_free), step=1.0)
            
        st.markdown("#### 📈 【投資】（年間 / 単位：万円）")
        new_invest = st.number_input("NISA年間積立額", value=float(st.session_state.invest_amount), step=5.0)

        if st.button("設定をクラウドに保存して再計算", type="primary", use_container_width=True):
            st.session_state.inc_husband_m = new_inc_h_m
            st.session_state.inc_husband_b = new_inc_h_b
            st.session_state.inc_wife_m = new_inc_w_m
            st.session_state.inc_wife_b = new_inc_w_b
            st.session_state.exp_food = new_exp_food
            st.session_state.exp_util = new_exp_util
            st.session_state.exp_tele = new_exp_tele
            st.session_state.exp_car = new_exp_car
            st.session_state.exp_edu = new_exp_edu
            st.session_state.exp_ins = new_exp_ins
            st.session_state.exp_wife = new_exp_wife
            st.session_state.exp_free = new_exp_free
            st.session_state.invest_amount = new_invest
            trigger_save() # スプレッドシートに保存
            st.rerun()

    st.divider()
    st.markdown("#### 📋 11年間ロードマップ（データ一覧）")
    st.dataframe(df_plan, use_container_width=True, hide_index=True)
