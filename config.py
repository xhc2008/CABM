"""
应用配置文件
包含模型配置、提示词和其他应用设置
⚠警告：除非你知道自己在做什么，否则请不要修改这里的配置
"""
from utils.env_utils import get_env_var
from dotenv import load_dotenv
load_dotenv()
import os

# 对话模型配置
CHAT_CONFIG = {
    "model": get_env_var("CHAT_MODEL","deepseek-ai/DeepSeek-V3"),  # 默认模型
    "max_tokens": 512,   # 最大生成token数
    "top_k": 5,           # Top-K采样
    "temperature": 0.9,   # 温度参数，控制创造性
    "stream": True,       # 是否使用流式响应
}



# 流式输出配置
STREAM_CONFIG = {
    "enable_streaming": True,     # 启用流式输出
}

# 选项生成配置
OPTION_CONFIG = {
    "enable_option_generation": True,  # 启用选项生成
    "model": get_env_var("OPTION_MODEL", "deepseek-ai/DeepSeek-V3"),  # 选项生成模型
    "max_tokens": 100,            # 最大生成token数
    "temperature": 0.7,           # 温度参数
    "stream": False,              # 选项生成不使用流式
    'enable_thinking': False,     # 是否启用思考
}

# 记忆模块配置
MEMORY_CONFIG = {
    "top_k": 5,                   # 记忆检索返回的最相似结果数量
    "timeout": 10,                # 记忆检索超时时间（秒）
    "min_similarity": 0.3,        # 最小相似度阈值
}

RAG_CONFIG = {
    ## 多路召回选择
    # 如果你都选择了API，出现“无法使用BM25”的报错可以忽略，不影响使用
    "Multi_Recall":{
        'BM25': {
            'lan': 'zh'  # ['zh', 'en']  语言选择
        },
        "Cosine_Similarity":{
            ## 嵌入选择('Model', 'API')选择其中一个!
            
            # 'embed_func': 'Model',
            # 'embed_kwds': {
            #     'emb_model_name_or_path': 'BAAI/bge-large-zh',  # 模型名称或路径
            #     'max_len': 512,  # 每段文本最大长度
            #     'bath_size': 64,  # 批量推理大小
            #     'device': 'cuda',  # ['cuda', 'cpu']  # 使用cuda或cpu进行推理
            # },
            
            'embed_func': 'API',
            'embed_kwds': {
                'base_url': 'https://api.siliconflow.cn/v1',  # 嵌入模型的url地址
                'api_key': os.getenv("MEMORY_API_KEY"),
                'model': 'BAAI/bge-m3'
            },
            
            'vector_dim': 1024,  # 嵌入维度(必须和嵌入模型的输出维度一样! 默认bge是1024, 不用调!)
        }
    },
    'Reranker': {
        # 'reranker_func': 'Model',  # Choice ['Model', 'API']
        # 'reranker_kwds': {
        #     'rerank_model_name_or_path': 'BAAI/bge-reranker-large',
        #     'device': 'cuda'
        # }
        
        'reranker_func': 'API',
        'reranker_kwds': {
            'base_url': 'https://api.siliconflow.cn/v1',
            'api_key': os.getenv("MEMORY_API_KEY"),
            'model': 'netease-youdao/bce-reranker-base_v1'
        }
    }
    
}

# 图像生成模型配置
IMAGE_CONFIG = {
    "model": get_env_var("IMAGE_MODEL","Kwai-Kolors/Kolors"),  # 默认模型
    "image_size": "1024x1024",      # 默认图像尺寸
    "batch_size": 1,                # 默认生成数量
    "num_inference_steps": 20,      # 推理步数
    "guidance_scale": 7.5,          # 引导比例
}

# 通用提示词配置
SYSTEM_PROMPTS = {
    "default": """你必须以严格的JSON格式，按顺序输出以下字段：
    "mood": <int> 当前的表情，且必须是其中之一，**只写序号**：<[MOODS]>
    "content": <string> 用1到6句话回复用户，禁止换行，禁止使用markdown，禁止使用括号（）。
    你的身份：""",
}
def get_story_prompts(character_name,character_prompt,seed):
    return f"""
你是一个专业的RPG故事生成器，你需要生成玩家和{character_name}的故事，要求内容新颖、逻辑闭环。根据以下提供的设定，严格输出一个JSON对象。该JSON对象必须且仅包含以下两个属性：

1.  `summary`: <string>
    *   值：一个**简短**的故事开头梗概（约1-3句话）。**仅描述故事的起始情境、主要冲突的引入或主角的初始目标，不要包含故事中后期的情节或结局。**
2.  `outline`: <array of string>
    *   值：一个由字符串组成的数组，表示分解后的故事内容大纲。
    *   **条目数量：** 40 到 100 条。
    *   **格式：** 每条是一个简洁的短语或短句，描述一个关键情节节点、场景转换、重要决策点或角色互动。条目应按故事发生的**时间顺序**排列。
    *   **范围：** 大纲应覆盖从故事开头（紧接在`summary`之后）直到最终结局。

**输入设定：**

*   **角色设定：**
    ```markdown
    {character_prompt}
    ```
*   **故事导向/核心主题/初始目标等补充信息：**
    ```markdown
    {seed}
    ```
"""
# 图像提示词配置
IMAGE_PROMPTS = [
    "繁星点缀的夜空下，一片宁静的湖泊倒映着群山和森林，远处有篝火和小屋",
    "阳光透过云层，照耀在广阔的草原上，野花盛开，远处有山脉和小溪",
    "雪花飘落的冬日森林，松树覆盖着白雪，小路蜿蜒，远处有小木屋和炊烟",
    "雨后的城市街道，霓虹灯反射在湿润的路面上，行人撑着伞，远处是城市天际线",
    "一间温馨的二次元风格卧室，阳光透过薄纱窗帘洒在木地板上,床上散落着卡通抱枕，墙边有摆满书籍和手办的原木色书架.书桌上亮着一盏小台灯，电脑屏幕泛着微光，窗外隐约可见樱花树。画面线条柔和，色彩清新，带有动画般的细腻阴影和高光。",
    "清晨的山谷，薄雾弥漫，溪流潺潺，野鹿在林间漫步",
    "古风庭院，青石小路，竹影婆娑，红色灯笼高挂",
    "未来都市，悬浮汽车穿梭，巨型全息广告牌闪烁，赛博朋克风格",
    "童话森林，蘑菇房子，精灵在花丛中嬉戏，彩色蝴蝶飞舞",
    "海边日落，金色余晖洒在沙滩上，贝壳和海星点缀其间",
    "宇宙星云，绚丽色彩交织，行星和彗星穿梭其中",
    "古堡夜景，月光洒在尖塔上，乌鸦盘旋，神秘氛围",
    "樱花盛开的校园，学生们在树下嬉戏，粉色花瓣随风飘落",
    "蒸汽朋克工厂，齿轮和管道纵横，机械臂在忙碌工作",
    "治愈系咖啡馆，木质桌椅，绿植环绕，窗外细雨绵绵",
    "魔法图书馆，漂浮的书本，发光的魔法阵，猫咪在角落打盹",
    "夏日泳池派对，五彩泳圈漂浮，朋友们欢笑嬉戏",
    "冬季滑雪场，雪人堆砌，孩子们打雪仗，远处有缆车",
    "古风水墨画，山水相依，云雾缭绕，渔舟唱晚",
    "二次元少女在繁花盛开的花园中微笑，蝴蝶环绕",
    "夜晚的露天集市，灯火通明，人群熙攘，各色摊位琳琅满目",
    "未来实验室，透明显示屏，机器人助手，蓝色冷光",
    "童话城堡，彩虹桥连接，独角兽在草地上奔跑",
    "秋天的枫树林，红叶飘落，木质长椅上有一本打开的书",
    "赛博猫在霓虹灯下漫步，身上有机械部件",
    "古风书房，宣纸铺展，毛笔蘸墨，窗外竹影摇曳",
    "星空下的露营帐篷，篝火旁有吉他和热巧克力",
    "二次元风格的甜品店，蛋糕和马卡龙色彩缤纷，店员微笑服务",
    "春天的田野，油菜花盛开，蜜蜂在花间飞舞",
    "夜晚的天台，城市灯火，少年仰望星空，耳机里播放着音乐",
    "未来太空港，宇航员准备登舰，星舰停泊在平台",
    "童话风格的糖果屋，屋顶是巧克力，门口有棒棒糖和棉花糖",
    "古风茶馆，紫砂壶沏茶，窗外细雨，客人低声交谈",
    "二次元风格的图书馆，书架高耸，少女在寻找喜欢的书籍",
    "夏日海滩，冲浪板立在沙滩上，海鸥盘旋，椰树摇曳",
    "冬夜的温泉，蒸汽缭绕，雪花飘落，木屋灯光温暖",
    "未来虚拟现实游戏大厅，玩家戴着头盔，虚拟世界绚丽多彩",
    "童话森林里的蘑菇屋，精灵在门口迎接客人",
    "秋日的南瓜田，南瓜灯点亮，孩子们在田间奔跑",
    "赛博朋克风格的酒吧，霓虹灯闪烁，调酒师是机器人",
    "古风花园，牡丹盛开，蝴蝶飞舞，石桥横跨小溪",
    "星际飞船驾驶舱，仪表盘发光，宇宙星空在窗外",
    "二次元风格的宠物店，猫狗兔子在玻璃柜里卖萌",
    "春天的樱花大道，粉色花瓣铺满道路，情侣牵手漫步",
    "夜晚的摩天轮，灯光闪烁，情侣在车厢里依偎",
    "未来城市的空中花园，悬浮平台上种满鲜花",
    "童话风格的冰雪城堡，雪花飘落，冰雕闪耀",
    "古风琴室，古筝和琵琶并列，少女弹奏，窗外梅花盛开",
    "二次元风格的美术教室，画板和颜料，学生们专注创作",
    "夏日的森林小溪，清澈见底，鱼儿游弋，树荫下有吊床",
    "冬季的圣诞集市，彩灯装饰，热红酒和姜饼香气四溢",
    "未来科技农场，自动化机器人收割，绿色蔬菜整齐排列",
    "童话风格的花仙子，翅膀闪烁，花瓣裙飘扬",
    "秋天的书店，落叶堆积在门口，店内温暖灯光",
    "赛博朋克风格的街头小吃摊，机械臂制作美食",
    "古风画舫，河面平静，船上有诗人吟诵",
    "星空下的天文台，望远镜对准银河，科学家记录数据",
    "二次元风格的运动场，少女们在跑步，阳光明媚",
    "春天的花园，郁金香盛开，蝴蝶和蜜蜂忙碌",
    "夜晚的书房，台灯下的书本和咖啡，窗外下着小雨",
    "未来智能家居，语音助手控制灯光，机器人清扫地板",
    "童话风格的森林小屋，烟囱冒烟，门口有小动物",
    "秋日的葡萄园，紫色葡萄挂满藤蔓，农夫采摘",
    "赛博朋克风格的摩托车，骑手穿着发光夹克",
    "古风竹林，清风徐来，竹叶沙沙作响",
    "星际空间站，宇航员在舱外维修，地球在远方",
    "二次元风格的音乐教室，钢琴和吉他，学生们练习",
    "夏日的游乐园，摩天轮和旋转木马，孩子们欢笑",
    "冬季的滑冰场，冰面光滑，情侣牵手滑行",
    "未来虚拟宠物， hologram 形态，互动玩耍",
    "童话风格的魔法学校，学生们学习魔法，猫头鹰送信",
    "秋天的枫叶大道，红叶如火，行人漫步",
    "赛博朋克风格的夜市，灯光绚烂，人群熙攘",
    "古风书院，学子朗读，老师讲解，窗外柳树依依",
    "星空下的露天电影院，荧幕上映经典电影，观众席上有毯子和爆米花",
    "二次元风格的甜品工坊，蛋糕和饼干造型可爱",
    "春天的湖畔，柳树垂荫，鸭子游弋",
    "夜晚的花园，萤火虫点亮，少女在花丛中漫步",
    "未来智能交通，自动驾驶汽车在城市中穿梭",
    "童话风格的糖果森林，树上长满棒棒糖和巧克力",
    "秋日的南瓜灯展，灯光点亮夜晚，孩子们欢笑",
    "赛博朋克风格的高楼大厦，玻璃幕墙反射霓虹",
    "古风茶道，茶具精致，茶香袅袅",
    "星际探险队在外星球登陆，奇异植物环绕",
    "二次元风格的服装店，模特展示新款，顾客挑选衣服",
    "夏日的果园，苹果和桃子挂满枝头",
    "冬季的雪山，滑雪者疾驰而下，雪花飞舞",
    "未来虚拟会议室，虚拟人物交流，数据流动",
    "童话风格的水晶宫殿，闪耀着七彩光芒",
    "秋天的森林小径，落叶铺满道路，松鼠在树上跳跃",
    "赛博朋克风格的地铁站，乘客穿着未来服饰",
    "古风诗会，文人雅集，琴棋书画",
    "星空下的帐篷营地，篝火旁有故事和歌声",
    "二次元风格的花店，鲜花琳琅满目，店主微笑服务",
    "春天的山坡，野花盛开，羊群吃草",
    "夜晚的灯塔，海浪拍打礁石，灯光指引船只",
    "未来智能健身房，虚拟教练指导锻炼",
    "童话风格的精灵村庄，蘑菇房子和小桥流水",
    "秋日的果园，橙色柿子挂满枝头",
    "赛博朋克风格的无人机快递，包裹飞速送达",
    "古风画廊，名画展出，观众品鉴",
    "星际货运飞船，货物装载，机械臂操作",
    "二次元风格的游泳馆，少女们在水中嬉戏",
    "夏日的露天音乐会，乐队演奏，观众欢呼",
    "冬季的雪地温泉，蒸汽缭绕，雪花飘落",
    "未来虚拟商店， hologram 商品展示",
    "童话风格的魔法森林，发光蘑菇和精灵",
    "秋天的稻田，金黄稻穗随风摇曳",
    "赛博朋克风格的夜景，城市灯火通明",
    "古风庭院，石榴树下，少女读书",
    "星空下的沙漠，骆驼队行进，星星闪烁",
    "二次元风格的美发店，发型师为顾客设计发型",
    "春天的花海，五彩缤纷，蜜蜂采蜜",
    "夜晚的码头，渔船停泊，灯光点点",
    "未来智能厨房，机器人烹饪美食",
    "童话风格的彩虹桥，连接两个梦幻世界",
    "秋日的森林湖泊，倒影清晰，野鸭游弋",
    "赛博朋克风格的虚拟现实游戏，玩家沉浸其中",
    "古风山水画，云雾缭绕，渔舟唱晚",
    "星际科研基地，科学家研究外星生物",
    "二次元风格的蛋糕店，甜品造型可爱",
    "夏日的沙滩排球比赛，运动员奋力扣球",
    "冬季的雪地摩托，疾驰而过，雪花飞扬",
    "未来虚拟宠物乐园， hologram 动物互动",
    "童话风格的魔法药水店，瓶瓶罐罐闪烁光芒",
    "秋天的枫叶林，红黄交错，阳光透过树叶",
    "赛博朋克风格的空中列车，穿梭城市上空",
    "古风书法室，宣纸铺展，墨香四溢",
    "星空下的海滩，潮水拍打，贝壳点缀",
    "二次元风格的漫画店，漫画书堆满书架",
    "春天的果园，樱桃和李子挂满枝头",
    "夜晚的森林，萤火虫点亮黑暗",
    "未来智能医疗中心，机器人医生诊断",
    "童话风格的魔法花园，花朵会说话",
    "秋日的葡萄酒庄园，葡萄采摘，酒桶堆积",
    "赛博朋克风格的虚拟偶像演唱会， hologram 舞台",
    "古风灯会，彩灯高挂，游人如织",
    "星际太空站，宇航员在舱外漫步",
    "二次元风格的运动会，学生们奋力拼搏",
    "夏日的森林露营，帐篷和篝火，朋友们围坐",
    "冬季的雪地足球赛，球员们奋力奔跑",
    "未来虚拟图书馆， hologram 书籍漂浮",
    "童话风格的魔法城堡，塔楼闪耀光芒",
    "秋天的南瓜灯节，灯光点亮夜晚",
    "赛博朋克风格的虚拟现实购物中心， hologram 商品",
    "古风画舫，河面平静，船上有诗人吟诵",
    "星空下的露天音乐会，乐队演奏，观众欢呼",
    "二次元风格的美术馆，画作色彩斑斓",
    "春天的花园，郁金香盛开，蝴蝶和蜜蜂忙碌",
    "夜晚的天台，城市灯火，少年仰望星空",
    "未来智能家居，语音助手控制灯光，机器人清扫地板",
    "童话风格的森林小屋，烟囱冒烟，门口有小动物",
    "秋日的葡萄园，紫色葡萄挂满藤蔓，农夫采摘",
    "赛博朋克风格的摩托车，骑手穿着发光夹克",
    "古风竹林，清风徐来，竹叶沙沙作响",
    "星际空间站，宇航员在舱外维修，地球在远方",
    "二次元风格的音乐教室，钢琴和吉他，学生们练习",
    "夏日的游乐园，摩天轮和旋转木马，孩子们欢笑",
    "冬季的滑冰场，冰面光滑，情侣牵手滑行",
    "未来虚拟宠物， hologram 形态，互动玩耍",
    "童话风格的魔法学校，学生们学习魔法，猫头鹰送信",
    "秋天的枫叶大道，红叶如火，行人漫步",
    "赛博朋克风格的夜市，灯光绚烂，人群熙攘",
    "古风书院，学子朗读，老师讲解，窗外柳树依依",
    "星空下的露天电影院，荧幕上映经典电影，观众席上有毯子和爆米花",
    "二次元风格的甜品工坊，蛋糕和饼干造型可爱",
    "春天的湖畔，柳树垂荫，鸭子游弋",
    "夜晚的花园，萤火虫点亮，少女在花丛中漫步",
    "未来智能交通，自动驾驶汽车在城市中穿梭",
    "童话风格的糖果森林，树上长满棒棒糖和巧克力",
    "秋日的南瓜灯展，灯光点亮夜晚，孩子们欢笑",
    "赛博朋克风格的高楼大厦，玻璃幕墙反射霓虹",
    "古风茶道，茶具精致，茶香袅袅",
    "星际探险队在外星球登陆，奇异植物环绕",
    "二次元风格的服装店，模特展示新款，顾客挑选衣服",
    "夏日的果园，苹果和桃子挂满枝头",
    "冬季的雪山，滑雪者疾驰而下，雪花飞舞",
    "未来虚拟会议室，虚拟人物交流，数据流动",
    "童话风格的水晶宫殿，闪耀着七彩光芒",
    "秋天的森林小径，落叶铺满道路，松鼠在树上跳跃",
    "赛博朋克风格的地铁站，乘客穿着未来服饰",
    "古风诗会，文人雅集，琴棋书画",
    "星空下的帐篷营地，篝火旁有故事和歌声",
    "二次元风格的花店，鲜花琳琅满目，店主微笑服务",
    "春天的山坡，野花盛开，羊群吃草",
    "夜晚的灯塔，海浪拍打礁石，灯光指引船只",
    "未来智能健身房，虚拟教练指导锻炼",
    "童话风格的精灵村庄，蘑菇房子和小桥流水",
    "秋日的果园，橙色柿子挂满枝头",
    "赛博朋克风格的无人机快递，包裹飞速送达",
    "古风画廊，名画展出，观众品鉴",
    "星际货运飞船，货物装载，机械臂操作",
    "二次元风格的游泳馆，少女们在水中嬉戏",
    "夏日的露天音乐会，乐队演奏，观众欢呼",
    "冬季的雪地温泉，蒸汽缭绕，雪花飘落",
    "未来虚拟商店， hologram 商品展示",
    "童话风格的魔法森林，发光蘑菇和精灵",
    "秋天的稻田，金黄稻穗随风摇曳",
    "赛博朋克风格的夜景，城市灯火通明",
    "古风庭院，石榴树下，少女读书",
    "星空下的沙漠，骆驼队行进，星星闪烁",
    "二次元风格的美发店，发型师为顾客设计发型",
    "春天的花海，五彩缤纷，蜜蜂采蜜",
    "夜晚的码头，渔船停泊，灯光点点",
    "未来智能厨房，机器人烹饪美食",
    "童话风格的彩虹桥，连接两个梦幻世界",
    "秋日的森林湖泊，倒影清晰，野鸭游弋",
    "赛博朋克风格的虚拟现实游戏，玩家沉浸其中",
    "古风山水画，云雾缭绕，渔舟唱晚",
    "星际科研基地，科学家研究外星生物",
    "二次元风格的蛋糕店，甜品造型可爱",
    "夏日的沙滩排球比赛，运动员奋力扣球",
    "冬季的雪地摩托，疾驰而过，雪花飞扬",
    "未来虚拟宠物乐园， hologram 动物互动",
    "童话风格的魔法药水店，瓶瓶罐罐闪烁光芒",
    "秋天的枫叶林，红黄交错，阳光透过树叶",
    "赛博朋克风格的空中列车，穿梭城市上空",
    "古风书法室，宣纸铺展，墨香四溢",
    "星空下的海滩，潮水拍打，贝壳点缀",
    "二次元风格的漫画店，漫画书堆满书架",
    "春天的果园，樱桃和李子挂满枝头",
    "夜晚的森林，萤火虫点亮黑暗",
    "未来智能医疗中心，机器人医生诊断",
    "童话风格的魔法花园，花朵会说话",
    "秋日的葡萄酒庄园，葡萄采摘，酒桶堆积",
    "赛博朋克风格的虚拟偶像演唱会， hologram 舞台",
    "古风灯会，彩灯高挂，游人如织",
    "星际太空站，宇航员在舱外漫步",
    "二次元风格的运动会，学生们奋力拼搏",
    "夏日的森林露营，帐篷和篝火，朋友们围坐",
    "冬季的雪地足球赛，球员们奋力奔跑",
    "未来虚拟图书馆， hologram 书籍漂浮",
    "童话风格的魔法城堡，塔楼闪耀光芒",
    "秋天的南瓜灯节，灯光点亮夜晚",
    "赛博朋克风格的虚拟现实购物中心， hologram 商品",
    "古风画舫，河面平静，船上有诗人吟诵",
    "星空下的露天音乐会，乐队演奏，观众欢呼",
    "二次元风格的美术馆，画作色彩斑斓",
]

# 负面提示词
NEGATIVE_PROMPTS = "模糊, 扭曲, 变形, 低质量, 像素化, 低分辨率, 不完整"

OPTION_SYSTEM_PROMPTS="""
你是一个选项生成器，你需要根据对话内容，为**用户**提供3个选项。
每个选项不能多于15个字。选项之间用换行隔开。不要回复多余的提示词、解释或符号，只回复选项内容。
回复格式示例：
我觉得可以
我觉得不行
这要看你行不行
"""
# 应用配置
APP_CONFIG = {
    "debug": get_env_var("DEBUG", "False").lower() == "true",
    "port": int(get_env_var("PORT", "5000")),
    "host": get_env_var("HOST", "0.0.0.0"),  # 服务器监听地址，0.0.0.0表示监听所有接口
    "static_folder": "static",
    "template_folder": "templates",
    "image_cache_dir": "static/images/cache",
    "max_history_length": 8,  # 最大对话历史长度（发送给AI的上下文长度）
    "history_dir": "data/history",  # 历史记录存储目录
    "show_scene_name": True,  # 是否在前端显示场景名称
    "show_logo_splash": get_env_var("SHOW_LOGO_SPLASH", "True").lower() == "true",  # 是否显示启动logo动画
    "auto_open_browser": get_env_var("AUTO_OPEN_BROWSER", "True").lower() == "true",  # 是否自动打开浏览器（会自动使用本地IP地址）
    "clean_assistant_history": get_env_var("CLEAN_ASSISTANT_HISTORY", "True").lower() == "true",  # 已弃用：JSON格式下不再需要清理【】标记
}

def get_chat_config():
    """获取对话模型配置"""
    return CHAT_CONFIG.copy()

def get_image_config():
    """获取图像生成模型配置"""
    return IMAGE_CONFIG.copy()

def get_system_prompt(prompt_type="default"):
    """获取通用提示词"""
    return SYSTEM_PROMPTS.get(prompt_type, SYSTEM_PROMPTS["default"])

def get_random_image_prompt():
    """获取随机图像提示词"""
    import random
    return random.choice(IMAGE_PROMPTS)

def get_app_config():
    """获取应用配置"""
    return APP_CONFIG.copy()

def get_stream_config():
    """获取流式输出配置"""
    return STREAM_CONFIG.copy()

def get_memory_config():
    """获取记忆模块配置"""
    return MEMORY_CONFIG.copy()

def get_RAG_config():
    """获取RAG模块配置"""
    return RAG_CONFIG.copy()

def get_option_config():
    """获取选项生成配置"""
    return OPTION_CONFIG.copy()

def get_option_system_prompt():
    """获取选项生成系统提示词"""
    return OPTION_SYSTEM_PROMPTS

def validate_config():
    """验证配置完整性"""
    # 验证对话模型配置
    required_chat_keys = ["model", "max_tokens", "temperature"]
    missing_chat_keys = [key for key in required_chat_keys if key not in CHAT_CONFIG]
    
    # 验证图像模型配置
    required_image_keys = ["model", "image_size", "guidance_scale"]
    missing_image_keys = [key for key in required_image_keys if key not in IMAGE_CONFIG]
    
    # 验证系统提示词配置
    if "default" not in SYSTEM_PROMPTS:
        missing_chat_keys.append("default_system_prompt")
    
    # 验证流式输出配置
    required_stream_keys = ["enable_streaming"]
    missing_stream_keys = [key for key in required_stream_keys if key not in STREAM_CONFIG]
    
    # 验证记忆模块配置
    required_memory_keys = ["top_k", "timeout", "min_similarity"]
    missing_memory_keys = [key for key in required_memory_keys if key not in MEMORY_CONFIG]
    
    # 验证选项生成配置
    required_option_keys = ["enable_option_generation", "model", "max_tokens", "temperature"]
    missing_option_keys = [key for key in required_option_keys if key not in OPTION_CONFIG]
    
    # 验证应用配置
    required_app_keys = ["debug", "port", "host", "image_cache_dir", "history_dir", "max_history_length", "show_scene_name", "clean_assistant_history"]
    missing_app_keys = [key for key in required_app_keys if key not in APP_CONFIG]
    
    # 合并所有缺失的配置项
    all_missing = missing_chat_keys + missing_image_keys + missing_stream_keys + missing_memory_keys + missing_option_keys + missing_app_keys
    
    if all_missing:
        raise ValueError(f"配置不完整，缺少以下配置项: {', '.join(all_missing)}")
    
    return True

if __name__ == "__main__":
    # 测试配置验证
    try:
        if validate_config():
            print("配置验证成功")
            print(f"对话模型: {get_chat_config()['model']}")
            print(f"图像模型: {get_image_config()['model']}")
            print(f"默认系统提示词: {get_system_prompt()}")
            print(f"随机图像提示词: {get_random_image_prompt()}")
            print(f"流式输出启用: {get_stream_config()['enable_streaming']}")
            print(f"记忆检索top_k: {get_memory_config()['top_k']}")
            print(f"选项生成启用: {get_option_config()['enable_option_generation']}")
            print(f"选项生成模型: {get_option_config()['model']}")
    except ValueError as e:
        print(f"配置验证失败: {e}")