---
name: ip
description: 查看本机所有网络接口的 IP 地址，包括公网 IP、VPN、局域网等。当用户输入 /ip 时使用。
allowed-tools: Bash(curl:*), Bash(ifconfig:*), Bash(python3:*)
---

# 查看本机 IP

执行以下步骤，将结果汇总为一个表格返回给用户：

## 1. 获取公网 IP 及归属地

```bash
curl -s ipinfo.io
```

## 2. 获取所有本地网络接口 IP

```bash
ifconfig | python3 -c "
import sys, re
text = sys.stdin.read()
for block in re.split(r'(?=^\S)', text, flags=re.MULTILINE):
    if not block.strip():
        continue
    name = block.split(':')[0]
    ips = re.findall(r'inet (\d+\.\d+\.\d+\.\d+)', block)
    ip6s = re.findall(r'inet6 ([0-9a-f:]+)%', block)
    if ips or ip6s:
        flags = re.search(r'flags=\d+<([^>]+)>', block)
        flag_str = flags.group(1) if flags else ''
        for ip in ips:
            print(f'{name}\tIPv4\t{ip}\t{flag_str}')
        for ip6 in ip6s:
            if not ip6.startswith('fe80'):
                print(f'{name}\tIPv6\t{ip6}\t{flag_str}')
"
```

## 3. 输出格式

将结果整理为表格：

| 接口 | 类型 | IP | 说明 |
|------|------|-----|------|
| (公网) | IPv4 | x.x.x.x | 归属地信息 |
| en0 | IPv4 | 192.168.x.x | Wi-Fi 局域网 |
| utun9 | IPv4 | 10.x.x.x | VPN 隧道 |
| ... | ... | ... | ... |

说明列根据接口名称自动判断：
- `en0` / `en1` → Wi-Fi 或有线网络
- `lo0` → 本地回环（可省略 127.0.0.1）
- `utun*` 有 IPv4 地址 → VPN 隧道
- `bridge*` → 虚拟网桥
- `docker*` / `veth*` → Docker 网络
