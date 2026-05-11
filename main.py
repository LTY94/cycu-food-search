import pandas as pd
import jieba
from collections import defaultdict

# 1. 讀取資料庫
print("⏳ 讀取資料中...")
# 把 NaN (空值) 替換成空字串，避免程式出錯
df = pd.read_csv('cycu_food.csv', encoding='utf-8').fillna('')

# 2. 建立倒排索引 (Inverted Index) 的核心 Hash Table
inverted_index = defaultdict(list)

print("🧠 開始建立倒排索引...")

# 3. 逐筆處理每一家餐廳的資料
for index, row in df.iterrows():
    shop_id = row['ID']
    
    # 巧妙結合：把「關鍵詞」和「介紹」合併在一起當作搜尋文本
    full_text = str(row['關鍵詞']) + " " + str(row['介紹'])
    
    # 用 jieba 把文字切成一個個的關鍵字
    words = jieba.lcut(full_text)
    
    # 將店家的 ID 存入對應的關鍵字 Hash Table 中
    for word in words:
        # 簡單過濾掉標點符號或太短的廢字 (例如空格或單一字)
        if len(word) > 1: 
            # 避免同一家店在同一個關鍵字重複紀錄
            if shop_id not in inverted_index[word]:
                inverted_index[word].append(shop_id)

print("✅ 倒排索引建立完成！")
print("=" * 40)

# -----------------------------------------
# 4. 測試搜尋威力！
# 💡 你可以隨意修改下面這個字，測試你的搜尋引擎！
search_term = "宵夜"  
# -----------------------------------------

print(f"🔍 搜尋關鍵字：【{search_term}】")
if search_term in inverted_index:
    # 從倒排索引瞬間抓出所有符合的店家 ID
    matched_ids = inverted_index[search_term]
    
    # 從資料庫中把這些 ID 的完整資料拉出來
    result_df = df[df['ID'].isin(matched_ids)]
    
    print(f"🎉 找到了！共有 {len(matched_ids)} 家符合的餐廳：\n")
    # 只印出幾個重要的欄位給你看
    print(result_df[['店名', '料理標籤', '星級評分', '特約優惠']])
else:
    print("😭 找不到任何相關的餐廳。")