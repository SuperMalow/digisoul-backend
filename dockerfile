# 使用官方轻量级 Python 镜像
FROM python:3.12-slim

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 设置工作目录
WORKDIR /app

# 1. 仅复制依赖文件（利用 Docker 缓存层）
COPY pyproject.toml uv.lock ./

# 2. 安装依赖 (不安装项目本身，仅安装第三方库)
# --frozen 确保严格遵循 lock 文件
RUN uv sync --frozen --no-cache --no-install-project

# 3. 复制项目代码
COPY . .

# 4. 安装项目
RUN uv sync --frozen --no-cache

# 环境变量：确保使用 uv 创建的虚拟环境
ENV PATH="/app/.venv/bin:$PATH"

# 启动脚本（可以根据需要修改）
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]