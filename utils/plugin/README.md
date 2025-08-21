# utils/plugin 插件系统说明

本目录实现了 CABM 项目的插件注册与动态加载机制，支持前端操作注册、插件自动发现、前后端内容扩展等功能。

## 主要功能

- **前端操作注册与调用**：
  - 通过 `register_frontend_operation(name, func)` 注册操作。
  - 通过 `call_frontend_operation(name, *args, **kwargs)` 调用操作。

- **插件基类与注册**：
  - 插件需继承 `BasePlugin`，实现 `register_frontend` 和 `register_backend` 方法。
  - 插件需在模块中定义 `plugin = YourPlugin()` 实例。

- **插件自动加载**：
  - 使用 `load_plugins(plugin_folder)` 自动加载插件目录下的模块或包。
  - 跳过以 `_` 开头或 `.nl` 结尾的目录。

- **前端/后端内容注册**：
  - `apply_frontend_hooks(register_func)` 让所有插件注册前端内容，并自动复制静态文件到 `/static/plugin/插件名/`。
  - `apply_backend_hooks(app)` 让所有插件注册后端路由。

## 插件开发流程

1. 新建插件模块或包，继承 `BasePlugin` 并实现注册方法。
2. 在模块中定义 `plugin = YourPlugin()`。
3. 确保插件目录被 `load_plugins` 加载。
4. 前端静态文件通过 `register_func` 注册，后端路由通过 `register_backend` 注册。

## 参考

详细机制与接口说明请参考 `__init__.py` 及示范插件。
