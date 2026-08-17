use std::sync::Mutex;
use tauri::Manager;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

#[allow(dead_code)]
struct SidecarState(Mutex<Option<CommandChild>>);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let mut child_process: Option<CommandChild> = None;

            let spawn_res = app.shell().sidecar("binaries/maxume_backend")
                .or_else(|_| app.shell().sidecar("maxume_backend"));

            if let Ok(cmd) = spawn_res {
                match cmd.spawn() {
                    Ok((mut rx, child)) => {
                        println!("[Maxume] Embedded Python backend sidecar spawned successfully.");
                        child_process = Some(child);

                        // Read stdout/stderr asynchronously so process pipes never buffer-lock
                        tauri::async_runtime::spawn(async move {
                            while let Some(event) = rx.recv().await {
                                match event {
                                    tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                                        println!("[Backend stdout] {}", String::from_utf8_lossy(&line));
                                    }
                                    tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                                        eprintln!("[Backend stderr] {}", String::from_utf8_lossy(&line));
                                    }
                                    tauri_plugin_shell::process::CommandEvent::Error(err) => {
                                        eprintln!("[Backend err] {}", err);
                                    }
                                    tauri_plugin_shell::process::CommandEvent::Terminated(status) => {
                                        println!("[Backend terminated] {:?}", status);
                                    }
                                    _ => {}
                                }
                            }
                        });
                    }
                    Err(err) => {
                        eprintln!("[Maxume] Note: Embedded sidecar spawn status: {}", err);
                    }
                }
            }

            // Persist child state so it stays alive throughout application lifetime
            app.manage(SidecarState(Mutex::new(child_process)));
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
