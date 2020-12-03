{{- define "pilot.registry.env_variables"}}
env:
  - name: DEBUG
    value: "{{ .Values.global.registry.app.env.debugEnabled }}"
  - name: STORAGE
    value: "{{ .Values.global.registry.app.env.storageName }}"
  - name: STORAGE_LOCAL_ROOTDIR
    value: "{{ .Values.global.registry.app.env.storageRootDir }}"
{{- end }}