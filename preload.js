const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("huazaiDesktop", {
  openResource: (payload) => ipcRenderer.invoke("open-resource", payload),
  readSyncFile: (location) => ipcRenderer.invoke("read-sync-file", location),
  writeSyncFile: (location, content) => ipcRenderer.invoke("write-sync-file", { location, content }),
  chooseSyncFile: () => ipcRenderer.invoke("choose-sync-file")
});
