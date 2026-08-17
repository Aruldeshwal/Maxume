!macro customInit
  nsExec::Exec 'taskkill.exe /F /IM maxume.exe /IM maxume_backend.exe /T'
  ExecWait 'cmd.exe /C taskkill /F /IM maxume.exe /IM maxume_backend.exe /T'
!macroend

!macro customInstall
  nsExec::Exec 'taskkill.exe /F /IM maxume.exe /IM maxume_backend.exe /T'
  ExecWait 'cmd.exe /C taskkill /F /IM maxume.exe /IM maxume_backend.exe /T'
!macroend

!macro customUnInit
  nsExec::Exec 'taskkill.exe /F /IM maxume.exe /IM maxume_backend.exe /T'
  ExecWait 'cmd.exe /C taskkill /F /IM maxume.exe /IM maxume_backend.exe /T'
!macroend
