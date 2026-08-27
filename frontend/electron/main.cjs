const {
  app,
  BrowserWindow,
} = require("electron");

const {
  spawn,
} = require("child_process");

const path = require("path");

let backendProcess = null;
const backendExecutable =
  process.platform === "win32"
    ? "music-rights-backend.exe"
    : "music-rights-backend";

function startBackend() {
  let backendPath;

  if (app.isPackaged) {
    backendPath = path.join(
      process.resourcesPath,
      "backend",
      "music-rights-backend",
      backendExecutable
    );
  } else {
    backendPath = path.join(
      __dirname,
      "..",
      "..",
      "dist",
      "music-rights-backend",
      backendExecutable
    );
  }

  console.log(
    "BACKEND PATH:",
    backendPath
  );

  backendProcess = spawn(
    backendPath,
    [],
    {
      stdio: "inherit",
    }
  );

  backendProcess.on(
    "error",
    (error) => {
      console.error(
        "BACKEND START ERROR:",
        error
      );
    }
  );

  backendProcess.on(
    "exit",
    (code, signal) => {
      console.log(
        "BACKEND EXIT:",
        code,
        signal
      );
    }
  );
}

async function waitForBackend() {
  const maxAttempts = 40;

  for (
    let i = 0;
    i < maxAttempts;
    i++
  ) {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/projects"
      );

      if (response.ok) {
        console.log(
          "Backend prêt"
        );

        return true;
      }
    } catch {
      // backend pas encore prêt
    }

    await new Promise(
      (resolve) =>
        setTimeout(
          resolve,
          250
        )
    );
  }

  console.error(
    "Le backend n'a pas démarré."
  );

  return false;
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1600,
    height: 1000,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  win.loadFile(
    path.join(
      __dirname,
      "../dist/index.html"
    )
  );

  // Pour debug seulement.
  // À enlever plus tard.
  win.webContents.openDevTools();
}

app.whenReady().then(
  async () => {
    startBackend();

    const backendReady =
      await waitForBackend();

    if (!backendReady) {
      console.error(
        "Impossible de démarrer FastAPI."
      );

      return;
    }

    createWindow();
  }
);

app.on(
  "before-quit",
  () => {
    if (backendProcess) {
      backendProcess.kill();
      backendProcess = null;
    }
  }
);

app.on(
  "window-all-closed",
  () => {
    if (
      process.platform !== "darwin"
    ) {
      app.quit();
    }
  }
);