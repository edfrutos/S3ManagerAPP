# Changelog S3Manager v1.2.2

## 🌍 Versión 1.2.2 - Todas las regiones de AWS (2026-11-16)

### ✨ Mejoras
- **Lista completa de regiones S3**: los desplegables de región (crear bucket y perfiles AWS) se rellenan con las regiones que conoce botocore, en lugar de una lista fija de 20. Se añaden, entre otras, `eu-south-2` (España), `eu-central-2`, `ap-south-2`, `ap-southeast-3` a `-7`, `ap-east-2`, `ap-northeast-3`, `il-central-1`, `me-central-1`, `ca-west-1` y `mx-central-1`. `us-east-1` sigue siendo la región por defecto.
- Si no se pudieran leer los datos de botocore, se usa una lista fija de respaldo con las mismas regiones.
