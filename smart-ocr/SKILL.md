---
name: smart-ocr
version: 1.0
description: |
  从图片中提取文字。基于 macOS Vision 框架，利用 Apple Neural Engine 硬件加速。
  支持中英混排、深色主题截图、高分辨率图片，单张 ~1 秒。
  触发词：OCR、提取文字、图片识别、截图文字、识别图中文字。
---

# Smart OCR — macOS Vision 文字提取

## 使用方式

```bash
~/.claude/skills/smart-ocr/scripts/ocr <image_path> [image_path2 ...]
```

支持 PNG、JPG 等常见图片格式，可一次传入多张。

## 输出格式

按图片分组，每张图片以 `=== <path> ===` 开头，逐行输出识别到的文字（按从上到下、从左到右排列）。

## 重新编译

二进制基于当前系统的 Swift 工具链编译，系统更新后可能需要重新编译：

```bash
cd ~/.claude/skills/smart-ocr/scripts
swiftc -o ocr ocr.swift -framework Vision -framework AppKit
```

前提：`/Library/Developer/CommandLineTools/usr/include/swift/module.modulemap` 已重命名为 `.bak`（避免 SwiftBridging 模块冲突）。
