import streamlit as st
import hashlib
import random
import math
import pandas as pd
import os
from datetime import datetime

# --- 核心逻辑类 (复用之前的逻辑并优化) ---
class PersonalLotteryTool:
    def __init__(self, user_profile):
        self.profile = user_profile
        self.seed_val = self._generate_soul_seed()

    def _generate_soul_seed(self):
        raw_data = f"{self.profile['solar']}{self.profile['lunar']}{self.profile['mbti']}{self.profile['gender']}{self.profile['place']}{self.profile['zodiac']}"
        hash_object = hashlib.sha256(raw_data.encode())
        return int(hash_object.hexdigest(), 16)

    def _combinations(self, n, k):
        if k < 0 or k > n: return 0
        return math.factorial(n) // (math.factorial(k) * math.factorial(n - k))

    def generate(self, game_type, period, r_count, b_count, is_append=False):
        # 混合 个人种子 + 期号 + 时间戳(微秒级，保证同配置多次点击不同)
        current_seed = self.seed_val + int(period) + datetime.now().microsecond
        random.seed(current_seed)

        if game_type == 'dlt':
            pool_red = list(range(1, 36))
            pool_blue = list(range(1, 13))
            red = sorted(random.sample(pool_red, r_count))
            blue = sorted(random.sample(pool_blue, b_count))
            bets = self._combinations(len(red), 5) * self._combinations(len(blue), 2)
            unit_price = 3 if is_append else 2
            
        else: # ssq
            pool_red = list(range(1, 34))
            pool_blue = list(range(1, 17))
            red = sorted(random.sample(pool_red, r_count))
            blue = sorted(random.sample(pool_blue, b_count))
            bets = self._combinations(len(red), 6) * self._combinations(len(blue), 1)
            unit_price = 2
            is_append = False # 双色球无追加

        price = bets * unit_price
        return {
            "period": period,
            "game": "大乐透" if game_type == 'dlt' else "双色球",
            "red": red,
            "blue": blue,
            "bets": bets,
            "price": price,
            "is_append": is_append,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

# --- 界面辅助函数 ---
def render_balls(reds, blues):
    """画出漂亮的球"""
    html = '<div style="display:flex; flex-wrap:wrap; gap:5px; margin-bottom:10px;">'
    for r in reds:
        html += f'<div style="width:35px; height:35px; background-color:#ff4d4f; color:white; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);">{r:02d}</div>'
    for b in blues:
        html += f'<div style="width:35px; height:35px; background-color:#1890ff; color:white; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);">{b:02d}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# --- 页面配置 ---
st.set_page_config(page_title="玄学选号助手", page_icon="🎱", layout="centered")

# --- 侧边栏：个人档案 (玄学因子) ---
with st.sidebar:
    st.header("🧬 能量校准")
    st.info("输入你的信息，生成专属随机种子")
    solar = st.date_input("阳历生日", value=datetime(1990, 1, 1))
    lunar = st.text_input("阴历生日 (例: 四月廿六)", "四月廿六")
    mbti = st.selectbox("MBTI 人格", ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP", "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"])
    gender = st.radio("性别", ["男", "女"], horizontal=True)
    place = st.text_input("出生地点", "Shanghai")
    zodiac = st.selectbox("星座", ["白羊", "金牛", "双子", "巨蟹", "狮子", "处女", "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼"])
    
    user_profile = {
        "solar": str(solar), "lunar": lunar, "mbti": mbti, 
        "gender": gender, "place": place, "zodiac": zodiac
    }

# --- 主界面 ---
st.title("🎱 灵感选号 & 追踪")

tab1, tab2 = st.tabs(["🎲 生成号码", "📜 历史与核对"])

tool = PersonalLotteryTool(user_profile)

# CSV文件路径
HISTORY_FILE = 'lottery_history.csv'

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        game_type = st.selectbox("选择彩种", ["dlt", "ssq"], format_func=lambda x: "大乐透" if x=="dlt" else "双色球")
    with col2:
        period = st.text_input("期号 (例: 25001)", value="25001")

    st.write("---")
    
    # 动态配置区域
    if game_type == 'dlt':
        st.subheader("大乐透配置 (5+2)")
        col_r, col_b = st.columns(2)
        with col_r:
            r_count = st.slider("红球数量 (复式)", 5, 18, 5)
        with col_b:
            b_count = st.slider("蓝球数量 (复式)", 2, 12, 2)
        is_append = st.checkbox("🔮 追加投注 (+1元/注)", value=True)
    else:
        st.subheader("双色球配置 (6+1)")
        col_r, col_b = st.columns(2)
        with col_r:
            r_count = st.slider("红球数量 (复式)", 6, 20, 6)
        with col_b:
            b_count = st.slider("蓝球数量 (复式)", 1, 16, 1)
        is_append = False

    # 实时价格预览
    if game_type == 'dlt':
        est_bets = tool._combinations(r_count, 5) * tool._combinations(b_count, 2)
        est_price = est_bets * (3 if is_append else 2)
    else:
        est_bets = tool._combinations(r_count, 6) * tool._combinations(b_count, 1)
        est_price = est_bets * 2
    
    st.caption(f"当前配置: {est_bets} 注 | 预计金额: ¥{est_price}")

    if st.button("✨ 启动玄学算法生成", type="primary", use_container_width=True):
        result = tool.generate(game_type, period, r_count, b_count, is_append)
        
        st.success(f"生成成功！依据: {mbti} + {zodiac} 能量场")
        render_balls(result['red'], result['blue'])
        
        st.info(f"""
        **详细清单**:
        - 💰 金额: **¥{result['price']}** ({result['bets']}注)
        - 📝 模式: {'追加' if result['is_append'] else '标准'} {'复式' if result['bets']>1 else '单式'}
        """)
        
        # 保存到历史记录
        df_new = pd.DataFrame([result])
        # 数组转字符串以便CSV保存
        df_new['red'] = df_new['red'].apply(lambda x: str(x))
        df_new['blue'] = df_new['blue'].apply(lambda x: str(x))
        
        if os.path.exists(HISTORY_FILE):
            df_new.to_csv(HISTORY_FILE, mode='a', header=False, index=False)
        else:
            df_new.to_csv(HISTORY_FILE, mode='w', header=True, index=False)
        
        st.toast("已保存到历史记录！")

with tab2:
    st.subheader("📊 投注记录 & 核对")
    
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
        # 倒序显示
        df = df.iloc[::-1]
        
        for index, row in df.iterrows():
            with st.expander(f"{row['date']} - {row['game']} (第{row['period']}期)"):
                # 还原数据格式
                reds = eval(row['red'])
                blues = eval(row['blue'])
                render_balls(reds, blues)
                st.write(f"投入: ¥{row['price']}")
                
                # 核对功能区
                st.markdown("---")
                c1, c2 = st.columns([3, 1])
                with c1:
                    win_input = st.text_input("输入开奖号码 (空格分隔, 蓝球在最后)", key=f"check_{index}")
                with c2:
                    check_btn = st.button("核对", key=f"btn_{index}")
                
                if check_btn and win_input:
                    # 简单解析逻辑
                    try:
                        nums = [int(x) for x in win_input.split()]
                        # 简单切分，大乐透后2位是蓝，双色球后1位是蓝
                        split_idx = -2 if row['game'] == '大乐透' else -1
                        real_red = set(nums[:split_idx])
                        real_blue = set(nums[split_idx:])
                        
                        hit_red = set(reds) & real_red
                        hit_blue = set(blues) & real_blue
                        
                        st.markdown(f"""
                        **🎯 核对结果**:
                        - 红球命中 ({len(hit_red)}): {list(hit_red) if hit_red else '无'}
                        - 蓝球命中 ({len(hit_blue)}): {list(hit_blue) if hit_blue else '无'}
                        """)
                        if len(hit_red) + len(hit_blue) > 3:
                            st.balloons()
                    except:
                        st.error("输入格式错误，请输入如: 05 12 20 25 30 03 10")
    else:
        st.write("暂无历史记录，快去生成第一注吧！")