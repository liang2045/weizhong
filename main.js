const { app, BrowserWindow, dialog, ipcMain, shell } = require("electron");
const fs = require("node:fs/promises");
const path = require("node:path");
const { fileURLToPath, pathToFileURL } = require("node:url");

function resolveSharedPath(location) {
  if (!location) return "";
  if (/^file:\/\//i.test(location)) return fileURLToPath(location);
  return location;
}

function resolveLocalFolderPath(location) {
  if (!location) return "";
  if (/^file:\/\//i.test(location)) return fileURLToPath(location);
  return location;
}

function isUrl(location) {
  return /^[a-z][a-z0-9+.-]*:\/\//i.test(location);
}

async function openLocalFolder(location) {
  const folderPath = resolveLocalFolderPath(location);
  const errorMessage = await shell.openPath(folderPath);
  if (!errorMessage) return { ok: true };

  if (!isUrl(location)) {
    await shell.openExternal(pathToFileURL(folderPath).toString());
    return { ok: true };
  }

  return { ok: false, message: `无法打开本地文件夹：${errorMessage}` };
}

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1320,
    height: 880,
    minWidth: 980,
    minHeight: 680,
    resizable: true,
    title: "花再产品库",
    backgroundColor: "#222222",
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.loadFile("index.html");
}

app.whenReady().then(() => {
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

ipcMain.handle("open-resource", async (_event, { url, isCloudLink }) => {
  if (!url) return { ok: false, message: "地址为空" };

  if (isCloudLink) {
    await shell.openExternal(url);
    return { ok: true };
  }

  return openLocalFolder(url);
});

ipcMain.handle("read-sync-file", async (_event, location) => {
  const filePath = resolveSharedPath(location);
  const content = await fs.readFile(filePath, "utf8");
  return content;
});

ipcMain.handle("write-sync-file", async (_event, { location, content }) => {
  const filePath = resolveSharedPath(location);
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, content, "utf8");
  return { ok: true, path: filePath };
});

ipcMain.handle("choose-sync-file", async () => {
  const result = await dialog.showSaveDialog({
    title: "选择团队共享 products.json",
    defaultPath: "products.json",
    filters: [{ name: "JSON 配置", extensions: ["json"] }]
  });

  if (result.canceled || !result.filePath) return "";
  return result.filePath;
});
