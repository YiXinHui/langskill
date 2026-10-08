# HTML 导出与素材嵌入

## 前置条件

- Google Chrome、Chromium 或兼容的 headless 浏览器；
- Python 3；
- Pillow：`python3 -m pip install pillow`。

## HTML 骨架

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <style>
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; }
    .poster { width: 1080px; height: 1440px; position: relative; overflow: hidden; }
  </style>
</head>
<body><main class="poster"></main></body>
</html>
```

## 导出

使用绝对路径：

```bash
bash <skill绝对路径>/scripts/export_poster.sh \
  <输入HTML绝对路径> <输出JPG绝对路径> <宽px> <高px> <缩放倍数>
```

例如 1080×1440、2 倍输出：

```bash
bash /path/to/lang-poster/scripts/export_poster.sh \
  /path/to/poster.html /path/to/poster.jpg 1080 1440 2
```

## 素材

- 二维码保持原始点阵和静区，不做去白底。
- 普通 Logo 可以在授权前提下转为透明背景。
- 长期交付优先使用 base64 或稳定相对路径。
- 本地绝对素材路径只适合本机预览。

## 常见故障

| 现象 | 常见原因 | 处理 |
|---|---|---|
| 只截到局部 | 定位参照不是固定画布 | 所有元素相对 `.poster` 定位 |
| 底部消失 | 实际内容超出画布 | 检查容器高度和 overflow |
| 字体缺失 | file 协议或字体不存在 | 使用脚本的本地 HTTP 服务和字体回退 |
| JPG 没更新 | 输入／输出路径指错 | 使用绝对路径并检查修改时间 |
| 二维码失效 | 被去白底或缩放模糊 | 保留原图和足够像素 |

导出后必须实际查看图片；只检查文件存在和尺寸不足以证明视觉正确。
