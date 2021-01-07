#!/bin/bash
# author:Quan666
# url:myelf.club

# 脚本所在路径
path=${PWD}
install_gocqhttp() {
  echo "开始安装 go-cqhttp"
  read -p "输入机器人 QQ：" qq
  read -p "输入机器人 QQ密码：" pwd
  wget https://github.com/Mrs4s/go-cqhttp/releases/download/v0.9.37-fix1/go-cqhttp-v0.9.37-fix1-linux-amd64.tar.gz
  tar -xvf go-cqhttp-v0.9.37-fix1-linux-amd64.tar.gz
  rm -rf go-cqhttp-v0.9.37-fix1-linux-amd64.tar.gz
  mkdir gocqhttp
  mv go-cqhttp gocqhttp
  echo '{
  "uin": '${qq}',
  "password": "'${pwd}'",
  "encrypt_password": false,
  "password_encrypted": "",
  "enable_db": true,
  "access_token": "",
  "relogin": {
    "enabled": true,
    "relogin_delay": 3,
    "max_relogin_times": 0
  },
  "_rate_limit": {
    "enabled": false,
    "frequency": 0,
    "bucket_size": 0
  },
  "ignore_invalid_cqcode": false,
  "force_fragmented": true,
  "heartbeat_interval": 0,
  "http_config": {
    "enabled": true,
    "host": "0.0.0.0",
    "port": 5700,
    "timeout": 0,
    "post_urls": {}
  },
  "ws_config": {
    "enabled": true,
    "host": "0.0.0.0",
    "port": 6700
  },
  "ws_reverse_servers": [
    {
      "enabled": true,
      "reverse_url": "ws://127.0.0.1:8080/cqhttp/ws",
      "reverse_api_url": "",
      "reverse_event_url": "",
      "reverse_reconnect_interval": 3000
    }
  ],
  "post_message_format": "string",
  "use_sso_address": false,
  "debug": false,
  "log_level": "",
  "web_ui": {
    "enabled": true,
    "host": "0.0.0.0",
    "web_ui_port": 9999,
    "web_input": false
  }
}' >./gocqhttp/config.hjson
  echo "go-cqhttp 安装完毕"
}
install_ELF_RSS() {
  #  curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun
  #  sudo systemctl start docker
  git clone https://github.com/Quan666/ELF_RSS.git
  cd ELF_RSS
  docker build -t elfrss:latest .
  mkdir /app
  cd ../
  cp ./ELF_RSS /app

  rm -rf ./ELF_RSS
  docker run --name elfrss -p 8080:8080 -v /app/:/app/ -d elfrss:latest
  echo "ELF_RSS 安装完成，请修改配置文件 /app/.env.prod"
}
install() {
  #1. 一键安装 ELF_RSS (RSS 订阅插件)
  #2. 启动 ELF_RSS (请先手动启动go-cqhttp)
  #3. 更新 ELF_RSS（备份配置文件 backup.env.prod）
  #4. 安装 ELFChatBot（闲聊机器人）
  #5. 安装 搜图插件 cq-picsearcher-bot
  echo "一键安装脚本
1. 一键安装 ELF_RSS (RSS 订阅插件)
2. 重启 ELF_RSS (请先手动启动go-cqhttp)
3. 停止 ELF_RSS
4. 查看日志
0. 退出
注意：安装完成后程序在 /app 目录下
      请修改配置文件后重启！
"

  read -p "输入选择:" no
  # 1.1. 未安装 go-cqhttp
  #      1. 输入 QQ
  #      2. 输入 密码
  #      3. 创建配置文件
  #      4. 下载 go-cqhttp && 运行
  if [ $no == 1 ]; then
    echo "1. 安装 go-cqhttp"
    echo "2. 不安装 go-cqhttp"
    read -p "输入选择:" go
    if [ $go == 1 ]; then
      install_gocqhttp
      echo "go-cqhttp 安装完成，在当前目录 gocqhttp 目录下
运行 ./gocqhttp/go-cqhttp ,进行初次登录，之后请后台运行"
    fi
    install_ELF_RSS
    return 0
  elif [ $no == 2 ]; then
    docker restart elfrss
  elif [ $no == 3 ]; then
    docker stop elfrss
  elif [ $no == 4 ]; then
    docker logs elfrss
  elif [ $no == 0 ]; then
    return 0
  fi

  # 1.2. 已经安装 go-cqhttp
  #      1. 运行 docker 构建命令

  # 2.1. 备份配置文件为 backup.env.prod
  #      运行 git pull
  #      运行 docker 构建命令

}

while true; do
  install
  r=$?
  if [ $r == 0 ]; then
    break
  fi
done
