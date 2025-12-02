import streamlit as st
import hashlib
import random
import math
import pandas as pd
import os
import requests
# import json
from datetime import datetime, date
# from zhdate import ZhDate  <-- 已移除此行

# ===========================
# 🎨 CSS 魔法区 (移动端深度适配)
# ===========================
st.set_page_config(page_title="赛博玄学终端 Mobile", page_icon="🔮", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #0e1117; }
    .mobile-header {
        background: linear-gradient(45deg, #ff00cc, #3333ff, #00dbde);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: 900; font-size: 1.8em; text-align: center; margin: 10px 0 20px 0;
    }
    .cyber-card {
        background-color: #1c1f26; padding: 15px; border-radius: 12px;
        border: 1px solid #2d313a; box-shadow: 0 2px 8px rgba(0,0,0,0.2); margin-bottom: 15px;
    }
    .section-title {
        font-size: 1.1em; font-weight: bold; color: #e0e0e0; margin-bottom: 12px; display: flex; align-items: center;
    }
    .section-icon { margin-right: 8px; }
    .stButton>button[kind="primary"] {
        background: linear-gradient(90deg, #ff4d4f 0%, #f73859 100%);
        border: none; border-radius: 12px; height: 55px; font-size: 20px; font-weight: bold; width: 100%;
        box-shadow: 0 4px 15px rgba(247, 56, 89, 0.3); transition: all 0.2s ease;
    }
    .stButton>button[kind="primary"]:active { transform: scale(0.98); }
    .lottery-ball-red, .lottery-ball-blue {
        width: 34px; height: 34px; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center;
        font-weight: 900; font-size: 15px; 
    }
    .lottery-ball-red { background: radial-gradient(circle at 30% 30%, #ff6b6b, #c0392b); box-shadow: inset 0 2px 3px rgba(255,255,255,0.3); }
    .lottery-ball-blue { background: radial-gradient(circle at 30% 30%, #4facfe, #00f2fe); box-shadow: inset 0 2px 3px rgba(255,255,255,0.3); }
    .copy-btn-container { margin-top: 15px; }
    .copy-btn {
        background-color: #2b324a; color: #00dbde; border: 1px solid #3333ff; padding: 12px 0;
        border-radius: 10px; cursor: pointer; font-weight: bold; width: 100%; font-size: 16px;
        transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 8px;
    }
    .copy-btn:active { background-color: #3333ff; color: white; }
    [data-testid="stTabs"] button { flex: 1; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ===========================
# 🧠 工具函数 (保留星座计算，移除生肖计算)
# ===========================
def get_zodiac(month, day):
    zodiacs = [
        ('摩羯座 ♑', (1, 20)), ('水瓶座 ♒', (2, 19)), ('双鱼座 ♓', (3, 20)), ('白羊座 ♈', (4, 20)),
        ('金牛座 ♉', (5, 21)), ('双子座 ♊', (6, 21)), ('巨蟹座 ♋', (7, 22)), ('狮子座 ♌', (8, 23)),
        ('处女座 ♍', (9, 23)), ('天秤座 ♎', (10, 23)), ('天蝎座 ♏', (11, 22)), ('射手座 ♐', (12, 22)),
        ('摩羯座 ♑', (12, 31))
    ]
    for z_name, (end_month, end_day) in zodiacs:
        if month < end_month or (month == end_month and day <= end_day): return z_name
    return '摩羯座 ♑'

# 移除了 get_chinese_zodiac 函数

# ===========================
# 🧠 核心逻辑区 (保持不变)
# ===========================
class PersonalLotteryTool:
    def __init__(self, user_profile):
        self.profile = user_profile
        self.seed_val = self._generate_soul_seed()

    def _generate_soul_seed(self):
        # 依然使用所有因子来生成种子
        raw_data = f"{self.profile['solar']}{self.profile['lunar_str']}{self.profile['mbti']}{self.profile['place']}{self.profile['zodiac_sign']}{self.profile['chinese_zodiac']}"
        hash_object = hashlib.sha256(raw_data.encode())
        return int(hash_object.hexdigest(), 16)

    def _combinations(self, n, k):
        if k < 0 or k > n: return 0
        return math.factorial(n) // (math.factorial(k) * math.factorial(n - k))

    def generate(self, game_type, period, r_count, b_count, is_append=False):
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
            is_append = False

        price = bets * unit_price
        return {
            "period": period,
            "game": "大乐透" if game_type == 'dlt' else "双色球",
            "red": red,
            "blue": blue,
            "bets": bets,
            "price": price,
            "is_append": is_append,
            "date": datetime.now().strftime("%m-%d %H:%M")
        }

class LotteryAPI:
    def __init__(self, appkey):
        self.appkey = appkey
        self.base_url = "https://api.jisuapi.com/caipiao"
        self.game_ids = self._fetch_game_ids()

    def _fetch_game_ids(self):
        if not self.appkey: return {}
        try:
            url = f"{self.base_url}/class?appkey={self.appkey}"
            res = requests.get(url, timeout=5).json()
            if res['status'] != 0: return {}
            mapping = {}
            for item in res['result']:
                if item['name'] == '超级大乐透': mapping['大乐透'] = item['caipiaoid']
                elif item['name'] == '双色球': mapping['双色球'] = item['caipiaoid']
            return mapping
        except: return {}

    def get_draw_result(self, game_name, period):
        if not self.appkey or game_name not in self.game_ids: return None, "API key无效或彩种未识别"
        cid = self.game_ids[game_name]
        url = f"{self.base_url}/query?appkey={self.appkey}&caipiaoid={cid}&issueno={period}"
        try:
            res = requests.get(url, timeout=8).json()
            if res['status'] == 0: return res['result'], "OK"
            else: return None, res['msg']
        except Exception as e: return None, str(e)

    def get_recent_history(self, game_name, num=5):
        if not self.appkey or game_name not in self.game_ids: return []
        cid = self.game_ids[game_name]
        url = f"{self.base_url}/history?appkey={self.appkey}&caipiaoid={cid}&num={num}"
        try:
            res = requests.get(url, timeout=8).json()
            if res['status'] == 0: return res['result']['list']
        except: pass
        return []

# ===========================
# 📱 界面渲染区 (移动端布局)
# ===========================
def render_balls_fancy(reds, blues):
    html = '<div style="display:flex; flex-wrap:wrap; gap:6px; margin: 12px 0; justify-content: center;">'
    for r in reds: html += f'<div class="lottery-ball-red">{int(r):02d}</div>'
    for b in blues: html += f'<div class="lottery-ball-blue">{int(b):02d}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# --- 主界面 ---
st.markdown('<div class="mobile-header">🔮 赛博玄学终端</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["⚡️ 算号", "📜 记录", "📈 走势"])
HISTORY_FILE = 'lottery_history.csv'

# --- Tab 1: 算号首页 (修改区) ---
with tab1:
    with st.expander("⚙️ 接口设置 (AppKey)", expanded=False):
        api_key = st.text_input("输入 Key 用于核对", type="password", placeholder="在此粘贴极速数据 AppKey")
        api_tool = LotteryAPI(api_key) if api_key else None

    st.markdown('<div class="cyber-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><span class="section-icon">🧬</span>你的能量档案</div>', unsafe_allow_html=True)
    
    # --- 修改开始：手动输入区域 ---
    c1, c2 = st.columns(2)
    with c1:
        default_solar = date(1987, 10, 14)
        solar = st.date_input("阳历诞辰", value=default_solar)
        # 依旧保留星座自动计算
        zodiac_sign = get_zodiac(solar.month, solar.day)
    with c2:
        # 改为手动选择生肖
        zodiac_list = ["鼠 🐀", "牛 🐂", "虎 🐅", "兔 🐇", "龙 🐉", "蛇 🐍", "马 🐎", "羊 🐏", "猴 🐒", "鸡 🐓", "狗 🐕", "猪 🐖"]
        # 默认选兔 (对应1987)
        chinese_zodiac = st.selectbox("生肖", zodiac_list, index=3)

    # 改为手动输入农历字符串
    lunar_str = st.text_input("农历生日 (例: 八月廿二)", value="八月廿二")

    # 展示计算结果 (只展示自动计算的星座了)
    st.info(f"✨ 已校准星盘能量: {zodiac_sign}")
    # --- 修改结束 ---

    mbti_options = ["INTJ 建筑师", "INTP 逻辑学家", "ENTJ 指挥官", "ENTP 辩论家", "INFJ 提倡者", "INFP 调停者", "ENFJ 主人公", "ENFP 竞选者", "ISTJ 物流师", "ISFJ 守卫者", "ESTJ 总经理", "ESFJ 执政官", "ISTP 鉴赏家", "ISFP 探险家", "ESTP 企业家", "ESFP 表演者"]
    default_mbti_index = mbti_options.index("ENFJ 主人公")
    mbti = st.selectbox("MBTI 人格", mbti_options, index=default_mbti_index)

    place = st.text_input("出生城市 (拼音)", "Shanghai")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 构建用户画像对象 (使用手动输入的值)
    user_profile = {"solar": str(solar),"lunar_str": lunar_str,"chinese_zodiac": chinese_zodiac,"zodiac_sign": zodiac_sign,"mbti": mbti[:4],"place": place}
    tool = PersonalLotteryTool(user_profile)

    # 3. 选号参数卡片 (保持不变)
    st.markdown('<div class="cyber-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><span class="section-icon">🎯</span>目标与参数</div>', unsafe_allow_html=True)
    
    c_game, c_period = st.columns([3, 2])
    with c_game:
        game_type = st.selectbox("彩种", ["dlt", "ssq"], format_func=lambda x: "大乐透" if x=="dlt" else "双色球")
    with c_period:
        period = st.text_input("期号", value=f"25001")
    
    st.divider()

    if game_type == 'dlt':
        st.caption("复式配置 (红球5-18，蓝球2-12)")
        r_count = st.slider("🔴 红球数", 5, 18, 5, label_visibility="collapsed")
        b_count = st.slider("🔵 蓝球数", 2, 12, 2, label_visibility="collapsed")
        is_append = st.toggle("🔮 追加投注 (+50%奖金)", value=True)
        est_bets = tool._combinations(r_count, 5) * tool._combinations(b_count, 2)
        est_price = est_bets * (3 if is_append else 2)
    else:
        st.caption("复式配置 (红球6-20，蓝球1-16)")
        r_count = st.slider("🔴 红球数", 6, 20, 6, label_visibility="collapsed")
        b_count = st.slider("🔵 蓝球数", 1, 16, 1, label_visibility="collapsed")
        is_append = False
        est_bets = tool._combinations(r_count, 6) * tool._combinations(b_count, 1)
        est_price = est_bets * 2
    
    st.markdown(f"<div style='text-align:right; font-weight:bold; color:#00dbde;'>共 {est_bets} 注 | 预计 ¥{est_price}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 4. 启动按钮 (保持不变)
    if st.button("⚡️ 注入灵魂，显现号码", type="primary"):
        with st.spinner("连接宇宙能量场..."):
            res = tool.generate(game_type, period, r_count, b_count, is_append)
            
            st.markdown('<div class="cyber-card" style="border-color: #ff00cc; background: linear-gradient(135deg, #2a1a3a 0%, #1c1f26 100%);">', unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align:center; margin:0 0 10px 0;'>✨ 显现成功 ✨</h3>", unsafe_allow_html=True)
            render_balls_fancy(res['red'], res['blue'])
            
            st.markdown(f"""
            <div style="display:flex; justify-content:space-around; text-align:center; margin-top:15px; font-size:0.9em; color:#bbb;">
                <div>💰 ¥{res['price']}</div>
                <div>🧾 {res['bets']}注</div>
                <div>📝 {'追加' if res['is_append'] else ''}{'复式' if res['bets']>1 else '单式'}</div>
            </div>
            """, unsafe_allow_html=True)
            
            red_str = " ".join([f"{r:02d}" for r in res['red']])
            blue_str = " ".join([f"{b:02d}" for b in res['blue']])
            append_str = "追加\n" if res['is_append'] else ""
            copy_text = f"""{res['game']}\n红球：{red_str}\n蓝球：{blue_str}\n{append_str}总价：{res['price']}元"""
            
            copy_html = f"""
            <div class="copy-btn-container">
                <button class="copy-btn" onclick="navigator.clipboard.writeText(`{copy_text}`).then(() => {{ this.innerHTML = '✅ 已复制到剪贴板'; setTimeout(() => {{ this.innerHTML = '📋 复制打票口令'; }}, 2000); }}).catch(err => {{ alert('复制失败，请手动复制'); }});">
                    📋 复制打票口令
                </button>
            </div>
            """
            st.components.v1.html(copy_html, height=60)
            st.markdown('</div>', unsafe_allow_html=True)
            
            df_new = pd.DataFrame([res])
            df_new['red'] = df_new['red'].apply(str)
            df_new['blue'] = df_new['blue'].apply(str)
            if os.path.exists(HISTORY_FILE): df_new.to_csv(HISTORY_FILE, mode='a', header=False, index=False)
            else: df_new.to_csv(HISTORY_FILE, mode='w', header=True, index=False)

# --- Tab 2: 记录 (保持不变) ---
with tab2:
    if not os.path.exists(HISTORY_FILE):
        st.info("暂无记录，快去首页生成吧！")
    else:
        df = pd.read_csv(HISTORY_FILE).iloc[::-1]
        for idx, row in df.iterrows():
            with st.expander(f"{row['date']} | {row['game']} 第{row['period']}期"):
                my_red = eval(row['red'])
                my_blue = eval(row['blue'])
                render_balls_fancy(my_red, my_blue)
                check_status = st.empty()
                if api_tool:
                    if st.button("🔍 联网核对", key=f"btn_{idx}", use_container_width=True):
                        with check_status.spinner("查询中..."):
                            res_data, msg = api_tool.get_draw_result(row['game'], str(row['period']))
                            if res_data:
                                try:
                                    real_red = [int(x) for x in res_data['number'].split()]
                                    real_blue = [int(x) for x in res_data['refernumber'].split()]
                                    st.caption(f"开奖日: {res_data['opendate']}")
                                    render_balls_fancy(real_red, real_blue)
                                    hit_r = set(my_red) & set(real_red)
                                    hit_b = set(my_blue) & set(real_blue)
                                    total_hit = len(hit_r) + len(hit_b)
                                    bg_color = '#1a3a2a' if total_hit > 2 else '#2c2f36'
                                    st.markdown(f"""<div style="background-color: {bg_color}; padding:10px; border-radius:8px; margin-top:10px;"><div style="font-weight:bold;">🎯 命中统计: {total_hit}球</div><div style="font-size:0.9em; color:#bbb;">红球: {list(hit_r) if hit_r else '-'} | 蓝球: {list(hit_b) if hit_b else '-'}</div></div>""", unsafe_allow_html=True)
                                    if total_hit > 3: st.balloons()
                                except: check_status.error("解析失败")
                            else: check_status.warning(msg)
                else: st.caption("⚠️ 请在首页设置 AppKey 才能核对")

# --- Tab 3: 走势 (保持不变) ---
with tab3:
    if not api_tool: st.info("请先在首页设置 AppKey")
    else:
        c_trend_game, c_trend_btn = st.columns([2,1])
        trend_game = c_trend_game.selectbox("彩种", ["大乐透", "双色球"], key="trend_sel", label_visibility="collapsed")
        if c_trend_btn.button("刷新", use_container_width=True): st.toast("刷新中...")
        with st.spinner("加载数据..."):
            history = api_tool.get_recent_history(trend_game, num=10)
            if history:
                for item in history:
                    st.markdown(f"""<div class="cyber-card" style="padding: 10px; margin-bottom: 8px;"><div style="display:flex; justify-content:space-between; font-size:0.9em; margin-bottom:5px;"><b>第 {item['issueno']} 期</b><span>{item['opendate'][5:]}</span></div>""", unsafe_allow_html=True)
                    r_balls = [int(x) for x in item['number'].split()]
                    b_balls = [int(x) for x in item['refernumber'].split()]
                    render_balls_fancy(r_balls, b_balls)
                    st.markdown('</div>', unsafe_allow_html=True)
            else: st.error("无法连接 API")

st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)