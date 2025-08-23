# 插件前端操作注册与调用机制
FRONTEND_OPERATIONS = {}

def register_frontend_operation(name, func):
	"""
	注册插件前端操作
	:param name: 操作名称（字符串，唯一）
	:param func: 实现该操作的函数
	"""
	FRONTEND_OPERATIONS[name] = func

def call_frontend_operation(name, *args, **kwargs):
	"""
	调用已注册的前端操作
	:param name: 操作名称
	:param args: 位置参数
	:param kwargs: 关键字参数
	:return: 操作结果
	"""
	if name in FRONTEND_OPERATIONS:
		return FRONTEND_OPERATIONS[name](*args, **kwargs)
	raise ValueError(f"未找到前端操作: {name}")

# 插件系统：支持前端内容和后端路由的动态注册

import importlib
import os
import sys
import shutil
from typing import Callable, List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PLUGIN_REGISTRY: Dict[str, 'BasePlugin'] = {}
FRONTEND_HOOKS: List[Callable[[Any], None]] = []
BACKEND_ROUTE_HOOKS: List[Callable[[Any], None]] = []

class BasePlugin:
	"""
	插件基类。插件需继承此类，并实现 register_frontend, register_backend 方法。
	"""
	name: str = "BasePlugin"

	def register_frontend(self, register_func: Callable[[str, str], None]):
		"""
		注册前端内容。register_func(路由, 文件路径)
		"""
		pass

	def register_backend(self, app):
		"""
		注册后端路由。app为后端框架实例（如Flask/FastAPI等）
		"""
		pass

def register_plugin(plugin: BasePlugin):
	"""注册插件到全局注册表，并调用其注册方法。"""
	PLUGIN_REGISTRY[plugin.name] = plugin
	FRONTEND_HOOKS.append(plugin.register_frontend)
	BACKEND_ROUTE_HOOKS.append(plugin.register_backend)

def load_plugins(plugin_folder: str):
	"""
	自动加载指定目录下的插件（需为模块/包）。
	"""

	# 读取插件管理器的禁用插件列表
	disabled_plugins = set()
	try:
		plugin_manager_config = os.path.join(plugin_folder, 'plugin_manager', 'disabled_plugins.json')
		if os.path.exists(plugin_manager_config):
			import json
			with open(plugin_manager_config, 'r', encoding='utf-8') as f:
				disabled_plugins = set(json.load(f))
	except Exception as e:
		logger.error(f"读取禁用插件列表失败: {e}")

	sys.path.insert(0, plugin_folder)
	for fname in os.listdir(plugin_folder):
		# 跳过以_开头的文件/目录
		full_path = os.path.join(plugin_folder, fname)
		if fname.startswith("_") or not (fname.endswith(".py") or os.path.isdir(full_path)):
			continue
		# 检查是否在禁用列表中（处理.nl后缀）
		clean_fname = fname.rstrip('.nl') if fname.endswith('.nl') else fname
		if clean_fname in disabled_plugins:
			logger.info(f"跳过被禁用的插件: {fname}")
			continue
		mod_name = fname[:-3] if fname.endswith(".py") else fname
		try:
			mod = importlib.import_module(mod_name)
			if hasattr(mod, 'plugin'):
				register_plugin(mod.plugin)
				logger.info(f"加载插件 {mod_name} 成功")
		except Exception as e:
			logger.error(f"加载插件 {mod_name} 失败: {e}")

def apply_frontend_hooks(register_func: Callable[[str, str], None]):
	"""
	让所有插件注册前端内容。
	"""
	# 物理复制inject.js等前端文件到/static/plugin/插件名/，保持原有目录结构
	static_plugin_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'plugin'))
	os.makedirs(static_plugin_root, exist_ok=True)
	def copy_and_register(route, path):
		# 只处理/static/plugin/xxx/yyy.js 路由
		if route.startswith('/static/plugin/') and os.path.exists(path):
			rel_path = route[len('/static/plugin/'):].lstrip('/')
			dst = os.path.join(static_plugin_root, rel_path)
			os.makedirs(os.path.dirname(dst), exist_ok=True)
			shutil.copy2(path, dst)
			register_func(route, dst)
	for hook in FRONTEND_HOOKS:
		hook(copy_and_register)

def apply_backend_hooks(app):
	"""
	让所有插件注册后端路由。
	"""
	for hook in BACKEND_ROUTE_HOOKS:
		hook(app)
