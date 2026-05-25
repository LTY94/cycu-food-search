import streamlit as st
import pandas as pd
import jieba
from collections import defaultdict
import datetime
import math
import os

# --- 網頁外觀設定 ---
st.set_page_config(page_title="中原美食雷達", page_icon="🍔", layout="wide")

# ==========================================
# 0. 系統後台記錄器
# ==========================================
def log_search_behavior(action, keyword, result_count):
    file_name = 'search_logs.csv'
    file_exists = os.path.isfile(file_name)
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(file_name, mode='a', encoding='utf-8-sig', newline='') as f:
        if not file_exists:
            f.write("時間,動作,關鍵字,找到家數\n")
        f.write(f"{current_time},{action},{keyword},{result_count}\n")

# ==========================================
# 1. 座標與距離計算核心設定 (全校大樓與宿舍真實座標)
# ==========================================
LANDMARKS = {
    "中原大學正門": (24.9575, 121.2408),
    "張靜愚紀念圖書館": (24.9568, 121.2415),
    "真知教學大樓": (24.9572, 121.2395),
    "全人教育村": (24.9560, 121.2418),
    "商學大樓": (24.9565, 121.2398),
    "工學館": (24.9585, 121.2422),
    "電學大樓": (24.9576, 121.2428),
    "理學大樓": (24.9582, 121.2412),
    "懷恩樓": (24.9569, 121.2405),
    "體育館": (24.9550, 121.2402),
    "恩慈宿舍 (女生宿舍)": (24.9555, 121.2425),
    "良善宿舍 (女生宿舍)": (24.9562, 121.2432),
    "力行宿舍 (男生宿舍)": (24.9542, 121.2418),
    "信實宿舍 (男生宿舍)": (24.9535, 121.2430),
    "中原夜市實踐路口": (24.9590, 121.2415),
    "中原夜市日新路口": (24.9595, 121.2398)
}

def calculate_real_distance(coord1, coord2):
    lat1, lng1 = coord1
    lat2, lng2 = coord2
    d_lat = (lat1 - lat2) * 111000
    d_lng = (lng1 - lng2) * 101000
    return int(math.sqrt(d_lat**2 + d_lng**2))

# ==========================================
# 2. 側邊欄 Menu 導覽列
# ==========================================
with st.sidebar:
    st.image("https://fakeimg.pl/300x150/ff9900/ffffff?text=CYCU+Food", width="stretch")
    st.title("🍔 中原美食雷達")
    st.markdown("---")
    page = st.radio("📍 功能切換", ["🔍 美食搜尋", "📅 吃貨日記與推薦", "📊 使用者行為分析"])
    
    st.markdown("---")
    st.subheader("📍 當前位置設定")
    user_location = st.selectbox(
        "選擇你目前在哪棟大樓/宿舍：",
        ["(不指定)"] + list(LANDMARKS.keys())
    )
    current_loc_name = "中原大學正門" if user_location == "(不指定)" else user_location
    current_coords = LANDMARKS[current_loc_name]
    st.success(f"📍 定位基準點：{current_loc_name}")

# ==========================================
# 3. 核心大腦 (讀取 467 筆大資料庫)
# ==========================================
SYNONYM_DICT = {
    "貓貓": "貓咪", "汪星人": "狗狗", "便宜": "平價", 
    "省錢": "平價", "粗飽": "吃到飽", "好喝": "飲料"
}

@st.cache_data
def load_data_and_build_index():
    df = pd.read_csv('中原大學美食搜尋系統(工作表1).csv', encoding='utf-8').fillna('')
    df['ID'] = pd.to_numeric(df['ID'], errors='coerce').fillna(0).astype(int)
    
    inverted_index = defaultdict(list)
    tag_set = set() 
    
    for index, row in df.iterrows():
        shop_id = row['ID']
        kw_text = str(row.get('關鍵詞', ''))
        desc_text = str(row.get('介紹', ''))
        tag_text = str(row.get('料理標籤', ''))
        
        clean_tag = tag_text.replace('、', ' ').replace(',', ' ').replace('，', ' ')
        for tag in clean_tag.split():
            if tag.strip():
                tag_set.add(tag.strip())

        full_text = kw_text + " " + desc_text + " " + tag_text
        words = jieba.lcut(full_text)
        
        for word in words:
            clean_word = word.strip()
            if len(clean_word) > 0: 
                if shop_id not in inverted_index[clean_word]:
                    inverted_index[clean_word].append(shop_id)
                    
    dropdown_options = ["(自己輸入關鍵字)"] + sorted(list(tag_set))
    return df, inverted_index, dropdown_options

df, inverted_index, tag_options = load_data_and_build_index()

# ⚡ 真實距離計算邏輯 (智慧相容欄位名稱)
coord_col_name = None
if '座標位置' in df.columns:
    coord_col_name = '座標位置'
elif '座標' in df.columns:
    coord_col_name = '座標'

shop_distances = []
for idx, row in df.iterrows():
    if coord_col_name and str(row[coord_col_name]) != 'nan' and str(row[coord_col_name]).strip() != '':
        try:
            coords_split = str(row[coord_col_name]).split(',')
            shop_coords = (float(coords_split[0].strip()), float(coords_split[1].strip()))
            dist = calculate_real_distance(current_coords, shop_coords)
            shop_distances.append(dist)
        except:
            shop_distances.append(999999) 
    else:
        shop_distances.append(999999) 

df['真實距離'] = shop_distances

weekday_map = {0: '一', 1: '二', 2: '三', 3: '四', 4: '五', 5: '六', 6: '日'}
today_str = weekday_map[datetime.datetime.today().weekday()]


# ==========================================
# 共用卡片排版函式
# ==========================================
def render_cards(dataframe):
    cards_per_row = 3
    for i, (idx, row) in enumerate(dataframe.iterrows()):
        if i % cards_per_row == 0:
            cols = st.columns(cards_per_row)
            
        with cols[i % cards_per_row]:
            with st.container(border=True, height=550): 
                img_url = row['圖片網址'] if '圖片網址' in df.columns and str(row['圖片網址']) != 'nan' and str(row['圖片網址']).strip() != '' else "https://fakeimg.pl/400x250/ff9900/ffffff?text=No+Image"
                st.image(img_url, width="stretch")
                
                st.subheader(f"✨ {row['店名']}")
                
                if row['真實距離'] == 999999:
                    dist_text = "📍 距離：尚未建立座標"
                else:
                    dist_text = f"📍 距離：{row['真實距離']} 公尺"
                    
                st.markdown(f"⭐ **{row['星級評分']}** | 🏷️ {row['料理標籤']} | {dist_text}")
                
                business_hours = str(row['營業時間'])
                if f"週{today_str}" in business_hours or f"星期{today_str}" in business_hours:
                    st.error(f"🔴 今日公休 (星期{today_str})")
                else:
                    st.success("🟢 今日有營業")
                
                st.markdown("---")
                
                intro_text = str(row.get('介紹', '')).strip()
                if not intro_text or intro_text == 'nan': 
                    intro_text = "店家暫無提供詳細介紹。"
                with st.expander("📝 查看店家介紹"):
                    st.write(intro_text)
                    
                st.markdown(f"🕒 **時間**：{business_hours}")
                st.markdown(f"📞 **電話**：{row['店家電話']}")
                st.markdown(f"📍 **地址**：{row['地址']}")
                
                if '特約優惠' in df.columns and row['特約優惠'] and str(row['特約優惠']) != 'nan' and str(row['特約優惠']) != '無':
                    st.info(f"🎁 {row['特約優惠']}")
                else:
                    st.write(" ") 
                    
                st.link_button("🗺️ 開啟導航", row['Google Map 網址'], width="stretch")


# ==========================================
# 4. 頁面內容切換邏輯
# ==========================================
if page == "🔍 美食搜尋":
    st.title(f"🔍 尋找今天的中原美食 (基準點：{current_loc_name})")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_word = st.selectbox("🎯 下拉關鍵字 (料理分類)：", tag_options)
    with col2:
        manual_input = st.text_input("✍️ 或直接輸入搜尋 (例如輸入：麵、貓咪)：")

    is_search_active = False
    action_type = ""
    
    if manual_input:
        is_search_active = True
        action_type = "手動輸入"
        search_term = manual_input
        if search_term in SYNONYM_DICT:
            search_term = SYNONYM_DICT[search_term]
            st.info(f"💡 自動將搜尋詞轉換為「{search_term}」。")
            
        matched_ids_set = set()
        for index_key, ids in inverted_index.items():
            if search_term in index_key:
                matched_ids_set.update(ids)
        result_df = df[df['ID'].isin(list(matched_ids_set))]
        
    elif selected_word != "(自己輸入關鍵字)":
        is_search_active = True
        action_type = "下拉選單"
        search_term = selected_word
        result_df = df[df['料理標籤'].astype(str).str.contains(search_term, na=False)]
    else:
        search_term = None

    if is_search_active and search_term:
        if len(result_df) > 0:
            result_df = result_df.sort_values(by='真實距離', ascending=True)
            st.success(f"🎉 幫你找到了 {len(result_df)} 家符合的餐廳！")
            render_cards(result_df)
            
            log_search_behavior(action_type, search_term, len(result_df))
        else:
            st.error(f"😭 目前沒有與「{search_term}」相關的餐廳。")
            log_search_behavior(action_type, search_term, 0)
            
    else:
        # 🌟 【核心修改】主動推播功能：嚴格限制 500 公尺內才顯示
        st.markdown(f"### 🎯 離「{current_loc_name}」500公尺內的鄰近美食精選推薦")
        
        # 篩選條件：距離必須小於等於 500 公尺
        nearby_df = df[df['真實距離'] <= 500]
        
        if len(nearby_df) > 0:
            closest_df = nearby_df.sort_values(by='真實距離', ascending=True)
            render_cards(closest_df)
        else:
            st.info(f"💡 目前方圓 500 公尺內沒有找到符合或已建立座標的餐廳喔！變更左側「當前位置設定」可探索更多區域。")

# ----------------------------------
# 頁面 B：吃貨日記與推薦 (智慧分析推薦)
# ----------------------------------
elif page == "📅 吃貨日記與推薦":
    st.title("📅 我的吃貨日記與專屬推薦")
    
    if os.path.exists('search_logs.csv'):
        log_df = pd.read_csv('search_logs.csv', encoding='utf-8-sig')
        
        if len(log_df) > 0:
            top_keyword = log_df['關鍵字'].value_counts().index[0]
            
            st.markdown(f"### 💡 根據你的搜尋日記，你近期最渴望的食物是：「**{top_keyword}**」")
            st.write("👉 我們特地為你挑選了**方圓 500 公尺內**的鄰近相關美食：")
            
            matched_ids_set = set()
            for index_key, ids in inverted_index.items():
                if top_keyword in index_key:
                    matched_ids_set.update(ids)
            rec_df = df[df['ID'].isin(list(matched_ids_set))]
            
            # 🌟 【同步優化】智慧推薦頁面也同步限制在 500 公尺之內
            rec_df = rec_df[rec_df['真實距離'] <= 500].sort_values(by='真實距離', ascending=True)
            
            if len(rec_df) > 0:
                render_cards(rec_df)
            else:
                st.info(f"目前方圓 500 公尺內，暫時沒有與你的最愛「{top_keyword}」相符且已建立座標的餐廳。")
                
            st.markdown("---")
            st.subheader("📖 近期的搜尋軌跡")
            diary_display = log_df[['時間', '動作', '關鍵字']].sort_values(by='時間', ascending=False).head(10)
            st.dataframe(diary_display)
            
        else:
             st.warning("👻 日記本還是空的！趕快去「美食搜尋」找點吃的。")
    else:
        st.warning("👻 日記本還是空的！趕快去「美食搜尋」找點吃的。")

# ----------------------------------
# 頁面 C：使用者行為分析
# ----------------------------------
elif page == "📊 使用者行為分析":
    st.title("📊 系統後台：使用者行為紀錄")
    
    if os.path.exists('search_logs.csv'):
        log_df = pd.read_csv('search_logs.csv', encoding='utf-8-sig')
        if len(log_df) > 0:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.subheader("🔥 熱門搜尋關鍵字 Top 10")
                top_keywords = log_df['關鍵字'].value_counts().head(10)
                st.bar_chart(top_keywords)
                
            with col2:
                st.subheader("🔍 搜尋方式統計")
                action_counts = log_df['動作'].value_counts()
                st.bar_chart(action_counts)
                
            st.markdown("---")
            st.subheader("📝 完整搜尋歷史紀錄 (資料庫原始檔)")
            st.dataframe(log_df)
        else:
             st.warning("👻 目前檔案是空的，還沒有搜尋紀錄。")
    else:
        st.warning("👻 目前還沒有任何人進行搜尋喔！")