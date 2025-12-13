# 使用 Manim 社区版官方镜像 (基于 Ubuntu)
FROM manimcommunity/manim:v0.19.0

# 切换为 root 用户以安装依赖
USER root

# 设置工作目录
WORKDIR /manim

# (可选) 如果需要支持中文，这里安装字体
RUN apt-get update && apt-get install -y fonts-noto-cjk

# 创建输入输出挂载点 (最佳实践)
RUN mkdir -p /manim/input /manim/output

# 修正权限 (使用 base image 默认用户 manimuser)
RUN chown -R manimuser:manimuser /manim

# 切换回 manimuser 用户
USER manimuser