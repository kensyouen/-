import streamlit as st
import pandas as pd

# === ページ設定 ===
st.set_page_config(page_title="Family Wealth Compass", page_icon="🧭", layout="wide")

# ==========================================
# 🔒 パスワード認証機能
# ==========================================
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        st.warning("🔒 このアプリはご家庭専用のプライベートツールです。パスワードを入力してください。")
        pwd = st.text_input("パスワード", type="password")
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

# --- 定数・固定データ ---
ORIGINAL_GOAL_AGE = "47歳"

# ★【新規追加】マイナス乖離の許容範囲（単位：万円）★
# 例：50に設定すると、予定より50万円マイナスまでは「許容内（セーフ）」と判定します
TOLERANCE_MAN = 50 

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
    50: {'income': 1042, 'extra': -38}, # 長女自立等で支出減
    51: {'income': 1050, 'extra': -38},
    52: {'income': 1050, 'extra': -38}
}

# --- セッションステート初期化 ---
if "actual_cash" not in st.session_state: st.session_state.actual_cash = 1880
if "actual_nisa" not in st.session_state: st.session_state.actual_nisa = 370

if "inc_husband_m" not in st.session_state: st.session_state.inc_husband_m = 43.0
if "inc_husband_b" not in st.session_state: st.session_state.inc_husband_b = 130.0
if "inc_wife_m" not in st.session_state: st.session_state.inc_wife_m = 16.0
if "inc_wife_b" not in st.session_state: st.session_state.inc_wife_b = 60.0
if "income_diff" not in st.session_state: st.session_state.income_diff = 0.0

if "exp_food" not in st.session_state: st.session_state.exp_food = 14.8
if "exp_util" not in st.session_state: st.session_state.exp_util = 1.5
if "exp_tele" not in st.session_state: st.session_state.exp_tele = 1.1
if "exp_car" not in st.session_state: st.session_state.exp_car = 6.0
if "exp_edu" not in st.session_state: st.session_state.exp_edu = 5.4
if "exp_ins" not in st.session_state: st.session_state.exp_ins = 0.7
if "exp_wife" not in st.session_state: st.session_state.exp_wife = 1.9
if "exp_free" not in st.session_state: st.session_state.exp_free = 17.3

if "living_cost" not in st.session_state: st.session_state.living_cost = 584.4
if "invest_amount" not in st.session_state: st.session_state.invest_amount = 60.0
if "analyzed" not in st.session_state: st.session_state.analyzed = False

# --- シミュレーション関数 ---
def run_simulation(base_cash, base_nisa, living, invest, inc_diff):
    sim_cash = base_cash
    sim_nisa = base_nisa
    current_living = living
    loan_annual = 183 
    
    is_goal_reached = False
    goal_age = "未達成(50歳以降)"
    records = []
    
    total = int(sim_cash + sim_nisa)
    if total >= 4000:
        goal_age = "39歳"
        is_goal_reached = True
        
    records.append({
        "夫の年齢": "39歳(現)", 
        "家族の年齢(妻/長/次/男)": "35 / 10 / 6 / 2",
        "世帯収入(万)": int(898 + inc_diff), 
        "支出計(万)": "-", 
        "総資産(万)": total
    })
    
    for age in range(40, 53):
        data = future_data[age]
        current_living = current_living * 1.02 
        total_expense = current_living + loan_annual + data['extra']
        current_income = data['income'] + inc_diff 
        
        sim_cash = sim_cash + current_income - total_expense - invest
        sim_nisa = (sim_nisa * 1.05) + invest
        total = int(sim_cash + sim_nisa)
        
        if total >= 4000 and not is_goal_reached:
            goal_age = f"{age}歳"
            is_goal_reached = True
            
        wife = age - 4
        child1 = age - 29
        child2 = age - 33
        child3 = age - 37
            
        records.append({
            "夫の年齢": f"{age}歳", 
            "家族の年齢(妻/長/次/男)": f"{wife} / {child1} / {child2} / {child3}",
            "世帯収入(万)": int(current_income), 
            "支出計(万)": int(total_expense), 
            "総資産(万)": total
        })
        
    df = pd.DataFrame(records)
    return goal_age, df

goal_age_result, df_plan = run_simulation(
    st.session_state.actual_cash, 
    st.session_state.actual_nisa, 
    st.session_state.living_cost, 
    st.session_state.invest_amount,
    st.session_state.income_diff
)

# === UI構築 ===
st.title("🧭 Family Wealth Compass")
tab1, tab2 = st.tabs(["🏠 ホーム", "📊 計画・詳細編集"])

with tab1:
    st.markdown("### 🎯 資産チェック")
    if goal_age_result == ORIGINAL_GOAL_AGE:
        st.success(f"**当初目標：{ORIGINAL_GOAL_AGE} (予定通り!)**")
    else:
        st.warning(f"**当初目標：{ORIGINAL_GOAL_AGE} ➔ 最新予測：{goal_age_result}**")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        st.metric("予定総資産 (現時点)", "2,250 万円")
    with col2:
        st.markdown("<h2 style='text-align:center; color:#ccc;'>VS</h2>", unsafe_allow_html=True)
    with col3:
        actual_total = st.session_state.actual_cash + st.session_state.actual_nisa
        st.metric("実際の総資産", f"{actual_total} 万円", delta=actual_total - 2250)
        
    st.caption("当初の現在予定: 現金 1880万 / NISA 370万")
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
        diff_total = (st.session_state.actual_cash + st.session_state.actual_nisa) - 2250
        st.markdown("---")
        
        # ★【変更】許容範囲の判定ロジック★
        if diff_total >= -TOLERANCE_MAN:
            # 乖離がプラス、またはマイナスでも許容範囲内（-50万以内）の場合
            if diff_total >= 0:
                st.success(f"**乖離： ＋{diff_total} 万円**\n\n完璧なペースです！生活レベルを維持して進んでください。")
            else:
                # 許容範囲内のマイナスの場合のメッセージ
                st.success(f"**乖離： {diff_total} 万円**\n\nマイナスですが【許容範囲内（±{TOLERANCE_MAN}万円）】です！誤差の範囲ですので、焦らず今のペースを維持しましょう。")
        else:
            # 許容範囲を超えてマイナスになった場合のみ、警告とFPアドバイスを表示
            st.error(f"**乖離： {diff_total} 万円**")
            st.markdown(f"⚠️ 許容範囲（-{TOLERANCE_MAN}万円）を下回りました。シミュレーションが修正されました。")
            
            with st.expander("💡 詳細な改善策：FPのアドバイスを見る", expanded=True):
                st.markdown("#### 👩‍💼 FPからの項目別・詳細改善提案")
                st.markdown(f"**① 項目別の支出分析**\n* **食費（月{st.session_state.exp_food}万）：** 平均より高め。外食等見直しで月2〜3万の改善余地あり。\n* **光熱・通信費：** 非常に優秀です！\n* **使途不明金（月{st.session_state.exp_free}万）：** 最強のバッファ。ここから少し投資に回せば一気に改善します。")
                
                if st.session_state.actual_cash > 1500:
                    st.markdown(f"**② 資産比率とNISA増額**\n現在、現金が{st.session_state.actual_cash}万円と潤沢です。遅れを取り戻すため、使途不明金から月5万円を捻出し、**NISA積立額を月10万円に増額**することを強く推奨します。")
                
                st.markdown("**③ 【重要】今後の高額支出アラート**\nご主人が44歳の年に「住宅修繕費150万円」など、年間200万近い追加支出が控えています。また48歳・49歳には長女の専門学校等の教育費ピークが来ます。NISAは崩さず、現金のプールで受け止める準備をしましょう。")


with tab2:
    st.markdown("### 📊 ロードマップと詳細設定")
    
    current_inc = (st.session_state.inc_husband_m * 12 + st.session_state.inc_husband_b) + (st.session_state.inc_wife_m * 12 + st.session_state.inc_wife_b)
    st.info(f"💡 現在のベース設定：世帯年収 **{int(current_inc)}万円** ／ 基本生活費 **{int(st.session_state.living_cost)}万円**(年) ／ NISA積立 **{int(st.session_state.invest_amount)}万円**(年)")
    
    with st.expander("📝 収入・支出の項目を細かく編集する", expanded=False):
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

        if st.button("この設定でシミュレーションを再計算する", use_container_width=True):
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
            
            new_total_inc = (new_inc_h_m * 12 + new_inc_h_b) + (new_inc_w_m * 12 + new_inc_w_b)
            st.session_state.income_diff = new_total_inc - 898
            
            monthly_exp = new_exp_food + new_exp_util + new_exp_tele + new_exp_car + new_exp_edu + new_exp_ins + new_exp_wife + new_exp_free
            st.session_state.living_cost = monthly_exp * 12
            
            st.rerun()

    st.divider()
    st.markdown(f"**🎯 シミュレーション達成予定：{goal_age_result}**")
    st.dataframe(df_plan, use_container_width=True, hide_index=True)
    st.caption("※支出計には、住宅ローン(183万)＋教育費や修繕費などの予定特別支出が加算されています。")
