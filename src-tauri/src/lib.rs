use std::sync::Mutex;
use std::process::{Command, Child};
use std::path::PathBuf;
use std::env::current_exe;
use std::fs::OpenOptions;
use std::io::Write;
use tauri::Manager;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

#[allow(dead_code)]
enum BackendProcess {
    TauriChild(CommandChild),
    StdChild(Child),
}

impl Drop for BackendProcess {
    fn drop(&mut self) {
        if let BackendProcess::StdChild(ref mut child) = *self {
            let _ = child.kill();
        }
    }
}

#[allow(dead_code)]
struct SidecarState(Mutex<Option<BackendProcess>>);

fn log_launcher(msg: &str) {
    if let Ok(app_data) = std::env::var("APPDATA") {
        let log_dir = PathBuf::from(app_data).join("Maxume");
        let _ = std::fs::create_dir_all(&log_dir);
        let log_file = log_dir.join("launcher.log");
        if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(log_file) {
            let _ = writeln!(f, "[Maxume Launcher] {}", msg);
        }
    }
}

#[cfg(target_os = "windows")]
fn kill_stale_backend_processes() {
    use std::os::windows::process::CommandExt;
    const CREATE_NO_WINDOW: u32 = 0x08000000;
    let _ = Command::new("taskkill")
        .args(["/F", "/IM", "maxume_backend.exe", "/T"])
        .creation_flags(CREATE_NO_WINDOW)
        .status();
}

#[cfg(not(target_os = "windows"))]
fn kill_stale_backend_processes() {}

fn find_backend_binary() -> Option<PathBuf> {
    // 1. Production Installed Layout: Check directly adjacent to maxume.exe
    if let Ok(exe_path) = current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            let direct = exe_dir.join("maxume_backend.exe");
            if direct.exists() {
                return Some(direct);
            }
            let in_binaries = exe_dir.join("binaries").join("maxume_backend.exe");
            if in_binaries.exists() {
                return Some(in_binaries);
            }
        }
    }

    // 2. Workspace / Development Layout
    let dev_candidates = [
        "src-tauri/binaries/maxume_backend-x86_64-pc-windows-msvc.exe",
        "binaries/maxume_backend-x86_64-pc-windows-msvc.exe",
        "sidecar/dist/maxume_backend.exe",
        "maxume_backend.exe",
    ];
    for c in &dev_candidates {
        let p = PathBuf::from(c);
        if p.exists() {
            return Some(p);
        }
    }

    None
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // Clean up any stale orphaned backend processes
            kill_stale_backend_processes();

            let mut active_backend: Option<BackendProcess> = None;

            // Strategy 1: Direct Executable Discovery (100% reliable for Windows installers)
            if let Some(backend_path) = find_backend_binary() {
                log_launcher(&format!("Found backend binary at: {:?}", backend_path));

                let mut cmd = Command::new(&backend_path);

                // On Windows, run in background without creating a console window
                #[cfg(target_os = "windows")]
                {
                    use std::os::windows::process::CommandExt;
                    const CREATE_NO_WINDOW: u32 = 0x08000000;
                    cmd.creation_flags(CREATE_NO_WINDOW);
                }

                match cmd.spawn() {
                    Ok(child) => {
                        log_launcher(&format!("Successfully spawned backend PID: {}", child.id()));
                        active_backend = Some(BackendProcess::StdChild(child));
                    }
                    Err(err) => {
                        log_launcher(&format!("Direct spawn error: {:?}", err));
                    }
                }
            } else {
                log_launcher("Direct binary not found, attempting Tauri sidecar fallback...");
                // Strategy 2: Tauri sidecar fallback
                let spawn_res = app.shell().sidecar("binaries/maxume_backend")
                    .or_else(|_| app.shell().sidecar("maxume_backend"));

                if let Ok(cmd) = spawn_res {
                    if let Ok((_rx, child)) = cmd.spawn() {
                        log_launcher("Tauri sidecar spawned successfully.");
                        active_backend = Some(BackendProcess::TauriChild(child));
                    }
                }
            }

            // Persist process in app state so it stays alive throughout application lifetime
            app.manage(SidecarState(Mutex::new(active_backend)));
            Ok(())
        })
        .on_window_event(|window, event| {
            match event {
                tauri::WindowEvent::CloseRequested { .. } | tauri::WindowEvent::Destroyed => {
                    kill_stale_backend_processes();
                    if let Some(state) = window.try_state::<SidecarState>() {
                        if let Ok(mut guard) = state.0.lock() {
                            let _ = guard.take();
                        }
                    }
                }
                _ => {}
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
