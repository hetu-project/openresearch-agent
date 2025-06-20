#!/bin/bash
echo "Resetting PostgreSQL..."

# 停止所有 PostgreSQL 服务
sudo systemctl stop postgresql
sudo pkill -f postgres

# 删除现有集群
sudo pg_dropcluster --stop 16 main 2>/dev/null || true

# 删除数据目录
sudo rm -rf /var/lib/postgresql/16/main

# 重新创建集群
sudo pg_createcluster 16 main

# 启动集群
sudo pg_ctlcluster 16 main start

# 启用自动启动
sudo systemctl enable postgresql

echo "Checking status..."
sudo pg_lsclusters
sudo ss -tlnp | grep 5432

# 设置密码
sudo -u postgres psql -c "ALTER USER postgres PASSWORD '1234qwer';"

# 创建数据库
sudo -u postgres createdb openrearch

echo "Testing connection..."
PGPASSWORD=1234qwer psql -h localhost -p 5432 -U postgres -d openrearch -c "SELECT version();"
