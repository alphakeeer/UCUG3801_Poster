# 待导入证据

此目录用于保留GPT Work提供的Verified Facts CSV原始副本。使用 `../run.py import-csv`导入，文件按内容SHA-256命名。

本轮45条补证已在远端原目录保留，并由显式适配器读取；本目录仍用于后续通用模板CSV。两种格式的差别和冲突处理见[导入说明](../IMPORT_VERIFIED_FACTS.md)。模板放在 `config/`，不会被当作研究事实自动导入。
