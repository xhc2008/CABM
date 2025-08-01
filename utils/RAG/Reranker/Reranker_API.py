import requests
class Reranker_API:
    def __init__(self, base_url, api_key, model):
        self.api_key = api_key
        self.model = model
        self.api_base = base_url.rstrip("/")

    def rerank(self, docs, query, k=5):
        docs_ = []
        for item in docs:
            if isinstance(item, str):
                docs_.append(item)
            else:
                docs_.append(item.page_content)
        docs = list(set(docs_))
        url = f"{self.api_base}/rerank"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "query": query,
            "documents": docs,
            "top_n": k,
            "return_documents": False
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        results = response.json()["results"]
        # 按得分排序并返回文档索引
        idx_score = [(r["index"], r["relevance_score"]) for r in results]
        idx_score = sorted(idx_score, key=lambda x: x[1], reverse=True)
        docs_ = [docs[idx] for idx, _ in idx_score]
        return docs_[:k]

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    reranker = Reranker_API(base_url=os.getenv('sil_url'),
                        api_key=os.getenv('sil_key'),
                        model='netease-youdao/bce-reranker-base_v1')
    docs = ['剑，长五尺，重若千钧，玄黑的锋刃上血色浮泛。剑以天外金石之瑛百炼所成，不遵兵仗规制，一如锻造它的那位短生种匠人般横逆不可当，狷狂已极。从来只与剑为友的她，竟有了许多朋友。她荣任剑首之日，匠人一袭黑衣出席典礼，负手投剑。剑没地数尺，惟余其柄。人人哗然。「我造的剑，唯有罗浮云骑剑首方能诠尽真妙。」他露齿一笑。如月般孤高傲岸的罗浮龙尊，因目睹她的神技，竟生出一较高下的胜负心。枪与剑争锋多年，苦无结果。最终她于显龙大雩殿中一剑分断海潮，终于赢得龙尊钦服。飞遍星海、见识广博的无名客曾为她操舟转舵，带来星海彼岸酿成的仙醪，与她酣饮畅谈，看天空中的群星熠熠。「便是天上的星星，我也会斩下。」她依稀记得酒酣耳热之际的豪言。自童年记忆中扑面而来的那颗燃烧星宿，那时时牵缠不休的恐怖梦魇仿佛也不再可憎可怖。舞剑至今，她第一次明白了何谓生机。而在此之前，她所怀者，不过是死志罢了。还有他，她的徒弟。她想起与他的初识，这个年纪小小鬼主意却极多的孩子，曾问出与当年的自己相同的问题。「师父为何执着于用剑？能杀死敌人的武器有千百种，就算要消灭那颗星星，仙舟的朱明火怕是也能做到。」「这个问题就像问诗人为何要写诗一样？表达自我的方式有许多，但属于我的只有这一种。」如今，他也已成为云骑的翘楚。她已经没有老师了。戎装女子殒于战阵，无法再教她任何东西。她也不再需要老师。对关于剑的一切，她了如指掌。它们就是身体的一部分，是行走坐卧间的一呼一吸。人们称呼她「无罅飞光」，是万载犹不可得的剑士巅顶。但她明白，要「斩下天上的星星」，她的剑，仍然不够——即便她手中握着的，是夸称仙舟第一的宝剑……剑，长五尺，重若千钧，玄黑的锋刃上血色浮泛。', '星魂TAG | \n介绍 | 传奇「云上五骁」之一，人送尊号「无罅飞光」。超 脱了人间的胜负，为了获得斩杀「神」的力量，她选择走上截然不同的道路。至此之后，仙舟的记录中少了一个罗浮「剑首」，多了一个名字被抹去的「叛徒」。\n角色定位 | 镜流是一名通过进入特殊状态增 强自身攻击的输出型角色。在战斗中，镜流通过特殊状态强化自身且使自身行动提前，特殊状态下可施放强力技能。\n## 属性数据\n## 表格内容:\n等级 | 生命值 | 攻击力 | 防御力\n--- | --- | --- | ---', '## 表格内容:\n镜流（Jingliu）\n---\n镜流（Jingliu）\n稀有度 |  | 性别 | 女\n全名/本名 | \n命途 | 毁灭命途 | 战斗属性 | 冰战斗属性\n阵营 | 仙舟「罗浮」 | 常驻/限定 | 限定UP\n实装日期 | 2023年10月11日（1.4版本）\nTAG | 技能强化、攻击力、暴击率、消耗队友生命值、自身行动提前、效果抵抗、自身终结技伤害提升、特殊领域、秘技无受击、演唱会\n星魂TAG |', '## 属性数据\n##  表格内容:\n等级 | 生命值 | 攻击力 | 防御力\n--- | --- | --- | ---\n等级 | 生命值 | 攻击力 | 防御力\n突破前 | 突破后 | 突破前 | 突破后 | 突破前 | 突破后\n1 | 195 | 92 | 66\n20 | 380 | 459 | 180 | 217 | 128 | 155\n30 | 556 | 634 | 263 | 300 | 188 | 214\n40 | 732 | 810 | 346 | 383 | 247 | 273']
    query = '静流的属性数据'
    print(reranker.rerank(docs, query, k=1))