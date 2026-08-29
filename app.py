import streamlit as st
import pandas as pd

# === ページ設定 ===
st.set_page_config(page_title="Family Wealth Compass", page_icon="🧭", layout="centered")

# ==========================================
# 🔒 パスワード認証機能
# ==========================================
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        st.warning("🔒 このアプリはご家庭専用のプライベートツールです。パスワードを入力してください。")
        pwd = st.text_input("パスワード", type="password")
        
        # Streamlit Secretsからパスワードを取得（設定忘れ時の仮パスは"secret123"）
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

# --- 定数・初期設定 ---
ORIGINAL_GOAL_AGE = "47歳"
TARGET_CASH = 2474
TARGET_NISA = 804

future_data = {
    45: {'income': 1056, 'extra': 191},
    46: {'income': 1065, 'extra': 191},
    47: {'income': 1074, 'extra': 191},
    48: {'income': 1046, 'extra': 311}, 
    49: {'income': 1056, 'extra': 295},
    50: {'income': 1042, 'extra': 145},
    51: {'income': 1050, 'extra': 100},
    52: {'income': 1050, 'extra': 100}
}

if "actual_cash" not in st.session_state:
    st.session_state.actual_cash = 2474
if "actual_nisa" not in st.session_state:
    st.session_state.actual_nisa = 804
if "living_cost" not in st.session_state:
    st.session_state.living_cost = 645
if "invest_amount" not in st.session_state:
    st.session_state.invest_amount = 60
if "analyzed" not in st.session_state:
    st.session_state.analyzed = False

def run_simulation(base_cash, base_nisa, living, invest):
    sim_cash = base_cash
    sim_nisa = base_nisa
    current_living = living
    is_goal_reached = False
    goal_age = "未達成(52歳以降)"
    records = []
    
    total = int(sim_cash + sim_nisa)
    if total >= 4000:
        goal_age = "44歳"
        is_goal_reached = True
        
    records.append({"年齢": "44歳(現)", "収入(万)": "-", "支出計(万)": "-", "総資産(万)": total})
    
    for age in range(45, 53):
        data = future_data[age]
        current_living = current_living * 1.02 
        total_expense = current_living + data['extra']
        sim_cash = sim_cash + data['income'] - total_expense - invest
        sim_nisa = (sim_nisa * 1.05) + invest
        total = int(sim_cash + sim_nisa)
        
        if total >= 4000 and not is_goal_reached:
            goal_age = f"{age}歳"
            is_goal_reached = True
            
        records.append({"年齢": f"{age}歳", "収入(万)": data['income'], "支出計(万)": int(total_expense), "総資産(万)": total})
        
    df = pd.DataFrame(records)
    return goal_age, df

goal_age_result, df_plan = run_simulation(st.session_state.actual_cash, st.session_state.actual_nisa, st.session_state.living_cost, st.session_state.invest_amount)

st.title("🧭 Family Wealth Compass")
tab1, tab2 = st.tabs(["🏠 ホーム", "📊 計画・編集"])

with tab1:
    st.markdown("### 🎯 資産チェック")
    if goal_age_result == ORIGINAL_GOAL_AGE:
        st.success(f"**当初目標：{ORIGINAL_GOAL_AGE} (予定通り!)**")
    else:
        st.warning(f"**当初目標：{ORIGINAL_GOAL_AGE} ➔ 最新予測：{goal_age_result}**")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        st.metric("予定総資産", "3,278 万円")
    with col2:
        st.markdown("<h2 style='text-align:center; color:#ccc;'>VS</h2>", unsafe_allow_html=True)
    with col3:
        actual_total = st.session_state.actual_cash + st.session_state.actual_nisa
        st.metric("実際の総資産", f"{actual_total} 万円", delta=actual_total - 3278)
        
    st.caption("予定内訳: 現金 2474万 / NISA 804万")
    st.divider()

    st.markdown("##### 実際の資産を入力")
    new_cash = st.number_input("💰 現金・預金（万円）", value=st.session_state.actual_cash, step=10)
    new_nisa = st.number_input("📈 NISA残高（万円）", value=st.session_state.actual_nisa, step=10)
    
    if st.button("分析して計画を再計算する", type="primary", use_container_width=True):
        st.session_state.actual_cash = new_cash
        st.session_state.actual_nisa = new_nisa
        st.session_state.analyzed = True
        st.rerun()

    if st.session_state.analyzed:
        diff_total = (st.session_state.actual_cash + st.session_state.actual_nisa) - 3278
        st.markdown("---")
        if diff_total >= 0:
            st.success(f"**乖離： ＋{diff_total} 万円**\n\n完璧なペースです！生活レベルを維持して進んでください。")
        else:
            st.error(f"**乖離： {diff_total} 万円**")
            st.markdown("⚠️ 予定を下回っています。シミュレーションが修正されました。")
            
            with st.expander("💡 詳細な改善策：FPのアドバイスを見る", expanded=True):
                st.markdown("#### 👩‍💼 FPからの項目別・詳細改善提案")
                st.markdown("**① 項目別の支出分析**\n* **食費（月14.8万）：** 平均より高め。外食等見直しで月2〜3万の改善余地あり。\n* **光熱・通信費：** 非常に優秀です！\n* **使途不明金（月17.2万）：** 最強のバッファ。ここから月3〜5万を投資に回せば一気に改善します。")
                
                if st.session_state.actual_cash > 1500:
                    st.markdown(f"**② 資産比率とNISA増額**\n現在、現金が{st.session_state.actual_cash}万円と潤沢です。遅れを取り戻すため、使途不明金から月5万円を捻出し、**NISA積立額を月10万円に増額**することを強く推奨します。")
                
                st.markdown("**③ 【重要】今後の高額支出アラート**\n48歳の年（長女の専門学校等）に年間約300万円の特別支出が控えています。NISAは崩さず、現金のプールで受け止める準備をしましょう。")

with tab2:
    st.markdown("### 📊 ロードマップと支出設定")
    st.caption("※基本生活費は毎年2%ずつ自動上昇する設定です。")
    
    col1, col2 = st.columns(2)
    with col1:
        new_living = st.number_input("今期の基本生活費 (年間/万円)", value=st.session_state.living_cost, step=10)
    with col2:
        new_invest = st.number_input("NISA年間積立額 (万円)", value=st.session_state.invest_amount, step=5)
        
    if st.button("この設定で表を再計算する", use_container_width=True):
        st.session_state.living_cost = new_living
        st.session_state.invest_amount = new_invest
        st.rerun()
        
    st.divider()
    st.markdown(f"**🎯 シミュレーション達成予定：{goal_age_result}**")
    st.dataframe(df_plan, use_container_width=True, hide_index=True)
    st.caption("※支出計には、教育費や修繕費などの予定特別支出が加算されています。")
