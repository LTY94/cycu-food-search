import streamlit as st
import pandas as pd
import jieba
from collections import defaultdict

# --- 網頁外觀設定 ---
st.set_page_config(page_title="中原美食雷達", page_icon="🍔", layout="wide")
st.title("🍔 中原美食專屬搜尋引擎")

SYNONYM_DICT = {
    "貓貓": "貓咪",
    "汪星人": "狗狗",
    "便宜": "平價",
    "省錢": "平價",
    "粗飽": "吃到飽",
    "好喝": "飲料"
}

# --- 核心大腦設定 ---
@st.cache_data
def load_data_and_build_index():
    df = pd.read_csv('cycu_food.csv', encoding='utf-8').fillna('')
    inverted_index = defaultdict(list)
    tag_set = set() 
    
    for index, row in df.iterrows():
        shop_id = row['ID']
        kw_text = str(row['關鍵詞'])
        desc_text = str(row['介紹'])
        tag_text = str(row['料理標籤'])
        
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

st.divider()

# --- 搜尋介面區 ---
col1, col2 = st.columns(2)

with col1:
    selected_word = st.selectbox("🎯 下拉關鍵字 (料理分類)：", tag_options)

with col2:
    manual_input = st.text_input("✍️ 或直接輸入搜尋 (例如輸入：麵、飯、鍋)：")

if manual_input:
    search_term = manual_input
    original_term = search_term
    
    if search_term in SYNONYM_DICT:
        search_term = SYNONYM_DICT[search_term]
        st.info(f"💡 系統已自動將「{original_term}」轉換為「{search_term}」進行搜尋。")
        
    matched_ids_set = set()
    for index_key, ids in inverted_index.items():
        if search_term in index_key:
            matched_ids_set.update(ids)
            
    matched_ids = list(matched_ids_set)
    result_df = df[df['ID'].isin(matched_ids)]
    search_type_msg = "關鍵字彈性搜尋"

elif selected_word != "(自己輸入關鍵字)":
    search_term = selected_word
    result_df = df[df['料理標籤'].astype(str).str.contains(search_term, na=False)]
    search_type_msg = "料理標籤分類"

else:
    search_term = None


# --- 顯示結果區 ---
if search_term:
    if len(result_df) > 0:
        st.success(f"🎉 幫你找到了 {len(result_df)} 家符合的餐廳！（模式：{search_type_msg}）")
        
        cards_per_row = 3
        for i, (idx, row) in enumerate(result_df.iterrows()):
            if i % cards_per_row == 0:
                cols = st.columns(cards_per_row)
                
            with cols[i % cards_per_row]:
                with st.container(border=True, height=580):
                    # 💡 已將圖片寬度寫法更新為最新版本 width="stretch"
                    #img_url = row['圖片網址'] if '圖片網址' in row and row['圖片網址'] != '' else "https://fakeimg.pl/400x250/ff9900/ffffff?text=No+Image"
                    #st.image(img_url, width="stretch")
                    
                    st.subheader(f"✨ {row['店名']}")
                    st.markdown(f"⭐ **{row['星級評分']}** | 🏷️ {row['料理標籤']}")
                    
                    intro_text = str(row['介紹']).strip()
                    if not intro_text or intro_text == 'nan': 
                        intro_text = "店家暫無提供詳細介紹。"
                    
                    with st.expander("📝 查看店家介紹"):
                        st.write(intro_text)
                    
                    st.markdown("---")
                    
                    st.markdown(f"🕒 **時間**：{row['營業時間']}")
                    st.markdown(f"📞 **電話**：{row['店家電話']}")
                    st.markdown(f"📍 **地址**：{row['地址']}")
                    
                    if row['特約優惠'] and str(row['特約優惠']) != 'nan' and str(row['特約優惠']) != '無':
                        st.info(f"🎁 {row['特約優惠']}")
                    else:
                        st.write(" ") 
                    
                    # 💡 已將按鈕寬度寫法更新為最新版本 width="stretch"
                    st.link_button("🗺️ 開啟導航", row['Google Map 網址'], width="stretch")
                    
    else:
        st.error(f"😭 目前沒有與「{search_term}」相關的餐廳。")