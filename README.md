# 花再产品库

一个可缩放的桌面窗口应用，用 XAI 风格的克制层级和固定品牌配色展示公司产品资源。每张卡片包含产品图、产品名、定价文字，以及「详情页、主图、SKU、白底图、网盘链接、产品资料」六个快捷按钮。

## 运行方式

1. 安装 Node.js 后在项目目录执行 `npm install`。
2. 执行 `npm start` 打开“花再产品库”桌面窗口。
3. 窗口可自由缩放；页面右上角可切换深色 / 浅色模式。
4. 点击「新建卡片」添加产品。
5. 点击卡片右下角设置按钮，上传产品图、修改品名和定价；除“网盘链接”外，其余按钮都配置本地 NAS / 共享盘文件夹地址。
6. 拖动卡片，或使用卡片右下角的上移/下移按钮调整位置。


## 打包 EXE

1. 在 Windows 电脑上执行 `npm install` 安装依赖。
2. 执行 `npm run exe`（等同于 `npm run dist:win`）生成 Windows 可执行文件。
3. 打包完成后，`dist/` 目录会生成安装版 `花再产品库-Setup-1.0.0-x64.exe` 和便携版 `花再产品库-Portable-1.0.0-x64.exe`；把 EXE 发给同事安装或直接运行即可。
4. 如需改版本号，请先修改 `package.json` 里的 `version`，再重新执行 `npm run exe`。
5. 也可以在 GitHub Actions 手动运行 `Build Windows EXE` 工作流，完成后从 Artifacts 下载 EXE。

## 团队同步方式

1. 在「设置」里选择或填写团队共享的 `products.json` 文件路径，例如 `Z:\Huazai\products.json` 或 `\\NAS\Huazai\products.json`。
2. 任意一个客户端新增、编辑、删除、拖动排序或导入配置后，桌面端会自动把当前卡片信息写回共享配置文件。
3. 其他安装者点击「更新」即可从同一个共享配置文件同步最新卡片信息。
4. 如果使用 HTTP JSON 地址，客户端可以点击「更新」读取，但静态 HTTP 地址通常不能由客户端直接写回；要实现任意客户端发布，推荐使用 NAS / 共享盘 JSON 文件路径。

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

> 注意：除“网盘链接”外，按钮都会按本地文件夹处理并通过系统文件管理器弹出；请填写文件夹路径，例如 `\\NAS\Products\A1`、`Z:\Products\A1` 或 `/Volumes/NAS/Products/A1`。
