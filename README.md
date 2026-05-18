# 产品资源卡片中心

一个轻量级静态 Web 程序，用谷歌 Material 风格的卡片列表集中展示公司产品资源。每张卡片包含产品图、产品名、定价文字，以及「详情页、主图、SKU、白底图、网盘链接、产品资料」六个快捷按钮。

## 使用方式

1. 用浏览器打开 `index.html`，或在目录中启动任意静态文件服务器。
2. 点击「新建卡片」添加产品。
3. 点击卡片右下角设置按钮，上传产品图、修改品名和定价，并配置六个按钮的 NAS 地址或网盘 URL。
4. 拖动卡片，或使用卡片右下角的上移/下移按钮调整位置。
5. 点击「导出配置」生成 `products.json`，把它放到团队共享的 HTTP 地址、NAS Web 服务或同目录中。
6. 其他同事填写「团队同步地址」并保存，点击「更新」即可同步产品卡片。

## 同步文件格式

程序支持直接读取数组，或读取包含 `products` 数组的 JSON 对象：

```json
{
  "updatedAt": "2026-05-18T00:00:00.000Z",
  "products": [
    {
      "id": "demo-smart-handle-a1",
      "name": "新品智能手柄 A1",
      "price": "定价：¥299 / 批发价详询",
      "image": "",
      "links": {
        "详情页": "https://example.com/product/a1",
        "主图": "file:///Volumes/NAS/Products/A1/main-image",
        "SKU": "file:///Volumes/NAS/Products/A1/sku",
        "白底图": "file:///Volumes/NAS/Products/A1/white-bg",
        "网盘链接": "https://example.com/share/a1",
        "产品资料": "file:///Volumes/NAS/Products/A1/documents"
      }
    }
  ]
}
```

> 注意：浏览器安全策略可能限制直接打开某些 `file://` 或 NAS 协议地址。建议将 NAS 资源配置为浏览器可访问的 SMB/WebDAV/HTTP 链接，或在公司终端中配置对应协议处理器。
