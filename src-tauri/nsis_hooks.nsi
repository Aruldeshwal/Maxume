!macro customInit
  ExecWait 'taskkill /F /IM maxume.exe /IM maxume_backend.exe /T'
!macroend

!macro customUnInit
  ExecWait 'taskkill /F /IM maxume.exe /IM maxume_backend.exe /T'
!macroend
