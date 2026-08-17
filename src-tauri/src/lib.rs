use tauri_plugin_shell::ShellExt;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // Automatically launch the Python backend sidecar if available
            let spawn_res = app.shell().sidecar("binaries/maxume_backend")
                .or_else(|_| app.shell().sidecar("maxume_backend"));

            if let Ok(cmd) = spawn_res {
                match cmd.spawn() {
                    Ok((_rx, _child)) => {
                        println!("[Maxume] Embedded Python backend sidecar spawned successfully.");
                    }
                    Err(err) => {
                        eprintln!("[Maxume] Note: Embedded sidecar spawn status: {}", err);
                    }
                }
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
