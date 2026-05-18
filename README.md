# 花再产品库

一个轻量级静态 Web 程序，用谷歌 Material 风格的卡片列表集中展示公司产品资源。每张卡片包含产品图、产品名、定价文字，以及「详情页、主图、SKU、白底图、网盘链接、产品资料」六个快捷按钮。

## 使用方式

1. 用浏览器打开 `index.html`，或在目录中启动任意静态文件服务器。
2. 点击「新建卡片」添加产品。
3. 点击卡片右下角设置按钮，上传产品图、修改品名和定价，并配置六个按钮的 NAS 地址或网盘 URL。
4. 拖动卡片，或使用卡片右下角的上移/下移按钮调整位置。
5. 点击页面右上角「设置」，在弹出的设置页面中配置团队同步地址、查看拖动说明，并导入或导出配置。
6. 点击「导出配置」生成 `products.json`，把它放到团队共享的 HTTP 地址、NAS Web 服务或同目录中。
7. 其他同事填写「团队同步地址」并保存，点击「更新」即可同步产品卡片。

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
        "详情页": "file:///Volumes/NAS/Products/A1/detail",
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

> 注意：除“网盘链接”外，程序会按本地 NAS / 共享盘资源处理地址，并把 Windows 共享路径（如 `\\NAS\Products\A1`）或盘符路径（如 `Z:\Products\A1`）转换为 `file://` 地址后打开。浏览器安全策略仍可能限制直接打开某些本地路径，建议在公司终端中配置可信站点、协议处理器或使用 NAS 提供的 WebDAV/文件管理入口。
