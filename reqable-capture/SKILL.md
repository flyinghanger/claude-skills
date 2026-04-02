---
name: reqable-capture
description: 通过 Reqable 抓包获取登录态（Cookie/Token/Header），解决需要认证才能访问的页面或 API。当遇到 401/403、需要登录态、需要抓包、需要获取 Cookie 或 Auth Token 时使用。
allowed-tools: Bash(open:*), Bash(curl:*), Bash(cat:*), Bash(python3:*), Bash(networksetup:*), Bash(jq:*), Read, Glob, Grep, Write
---

# Reqable 抓包获取登录态

当需要访问带认证的页面或 API 时，通过 Reqable 代理抓取浏览器的真实请求，提取 Cookie/Token/Header 供后续使用。

## 工作流程

### Step 1: 确认 Reqable 运行中

```bash
pgrep -x Reqable || open -a Reqable
```

如果是首次使用，提醒用户：
- 打开 Reqable 后需要安装并信任 CA 证书（Reqable → Certificate → Install）
- macOS 钥匙串中需要设置证书为「始终信任」

### Step 2: 引导用户抓包

告知用户以下操作步骤：

1. **Reqable 中开启抓包**：点击左上角的 ▶️ 开始录制
2. **在浏览器中访问目标页面/API**：确保浏览器已登录目标网站
3. **在 Reqable 中找到目标请求**：通过 URL 或关键字筛选
4. **导出为 cURL**：右键目标请求 → Copy → Copy as cURL

然后请用户把 cURL 命令粘贴过来。

### Step 3: 解析 cURL 提取认证信息

用户粘贴 cURL 后，用 Python 解析提取关键认证信息：

```bash
python3 -c "
import sys, re, shlex

curl_cmd = sys.argv[1]

# Parse headers
headers = {}
parts = shlex.split(curl_cmd)
i = 0
while i < len(parts):
    if parts[i] in ('-H', '--header') and i + 1 < len(parts):
        key, _, value = parts[i+1].partition(':')
        headers[key.strip().lower()] = value.strip()
    i += 1

# Extract auth info
auth_info = {}
if 'cookie' in headers:
    auth_info['cookie'] = headers['cookie']
if 'authorization' in headers:
    auth_info['authorization'] = headers['authorization']
if 'x-csrf-token' in headers:
    auth_info['x-csrf-token'] = headers['x-csrf-token']

# Extract URL
url = None
for p in parts:
    if p.startswith('http'):
        url = p.strip(\"'\").strip('\"')
        break

print('=== URL ===')
print(url or 'N/A')
print()
print('=== Auth Headers ===')
for k, v in auth_info.items():
    # Truncate long values for display
    display = v[:80] + '...' if len(v) > 80 else v
    print(f'{k}: {display}')
print()
print('=== All Headers ===')
for k, v in headers.items():
    display = v[:80] + '...' if len(v) > 80 else v
    print(f'{k}: {display}')
" "CURL_COMMAND_HERE"
```

### Step 4: 使用认证信息

提取到认证信息后，有两种使用方式：

#### 方式 A：直接 curl 调用
把原始 cURL 命令修改 URL/参数后直接用，保留所有 auth header。

#### 方式 B：提取关键 header 复用
只保留认证相关的 header（Cookie / Authorization / CSRF Token），构造新的请求：

```bash
curl -s 'TARGET_URL' \
  -H 'Cookie: EXTRACTED_COOKIE' \
  -H 'Authorization: EXTRACTED_TOKEN' \
  | jq .
```

### Step 5: 保存认证信息（可选）

如果用户需要多次使用，将 auth header 保存到临时文件供后续调用：

```bash
# Save headers to temp file
cat > /tmp/reqable-auth-headers.txt << 'HEADERS'
Cookie: xxx
Authorization: Bearer xxx
HEADERS
```

后续请求可以读取使用。注意：Cookie/Token 有有效期，过期后需要重新抓包。

## 替代方案：HAR 导出

如果用户导出的是 HAR 文件而非 cURL：

```bash
python3 -c "
import json, sys
with open(sys.argv[1]) as f:
    har = json.load(f)
for entry in har['log']['entries']:
    url = entry['request']['url']
    headers = {h['name'].lower(): h['value'] for h in entry['request']['headers']}
    if 'cookie' in headers or 'authorization' in headers:
        print(f'URL: {url}')
        if 'cookie' in headers:
            print(f'Cookie: {headers[\"cookie\"][:80]}...')
        if 'authorization' in headers:
            print(f'Auth: {headers[\"authorization\"][:80]}...')
        print()
" /path/to/export.har
```

## 常见场景

| 场景 | 做法 |
|------|------|
| 网页需要登录才能看 | 浏览器登录 → Reqable 抓请求 → 提取 Cookie → curl 访问 |
| API 返回 401/403 | 抓浏览器中成功的请求 → 复制完整 header → 重放 |
| 需要 CSRF Token | 抓包找到 token → 提取 cookie + csrf header 一起用 |
| 内部系统抓数据 | 抓包拿到完整认证链 → 脚本批量请求 |

## 注意事项

- Cookie/Token 有有效期，过期需重新抓包
- 不要将认证信息提交到 git（/tmp 目录下的临时文件用完即弃）
- 如果 HTTPS 解密失败，检查 Reqable CA 证书是否正确安装和信任
