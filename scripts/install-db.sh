#!/bin/bash
echo "Installing PostgreSQL..."

# 更新包列表
sudo apt update

# 安装 PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# 启动并启用服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 等待服务启动
sleep 5

# 检查服务状态
sudo systemctl status postgresql

# 检查端口监听
sudo ss -tlnp | grep 5432

# 设置密码
sudo -u postgres psql -c "ALTER USER postgres PASSWORD '1234qwer';"

# 创建数据库
sudo -u postgres createdb openrearch

# 测试连接
echo "Testing connection..."
PGPASSWORD=1234qwer psql -h localhost -p 5432 -U postgres -d openrearch -c "SELECT version();"

echo "PostgreSQL installation completed!"
