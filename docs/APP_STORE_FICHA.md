# Ficha App Store Connect — S3Manager (macOS)

## Registro (Nueva app)
| Campo | Valor |
|---|---|
| Plataforma | macOS |
| Nombre (máx. 30) | S3Manager |
| Idioma principal | Español (España) |
| ID de paquete | com.edefrutos.s3manager |
| SKU | S3MANAGER-MACOS-001 |
| Acceso de usuario | Acceso total |

## Información de la app
| Campo | Valor |
|---|---|
| Subtítulo (máx. 30) | Buckets de Amazon S3 en tu Mac |
| Categoría principal | Herramientas para desarrolladores |
| Categoría secundaria | Utilidades |
| Derechos de contenido | No contiene, muestra ni accede a contenido de terceros (responder "No") |
| Clasificación por edades | Todas las respuestas "Ninguno" / "No" → 4+ |
| URL política de privacidad | https://efjdev.com/privacidad/ |

## Precio y disponibilidad
- Precio: Gratis
- Disponibilidad: todos los países

## Privacidad de la app (App Privacy)
- ¿Recopilas datos de esta app? → **No, no recopilamos datos**.
  Motivo: no hay servidor del desarrollador ni analítica. Las credenciales y los archivos
  solo viajan entre el Mac del usuario y su propia cuenta de AWS; Apple no considera
  "recopilación" los datos que no salen hacia el desarrollador ni terceros que él controle.

## Versión 1.2.2
**Texto promocional (máx. 170)**
Lista, descarga y borra archivos de tus buckets de Amazon S3 sin consola ni línea de comandos. Varios perfiles de AWS y claves protegidas en el Llavero.

**Descripción (máx. 4000)**
S3Manager es una aplicación de escritorio para trabajar con tus buckets de Amazon S3 desde una ventana, sin abrir la consola web ni usar la línea de comandos.

BUCKETS
• Lista todos los buckets de tu cuenta.
• Crea buckets nuevos en la región que elijas.
• Elimina un bucket con todo su contenido, siempre con confirmación previa.

ARCHIVOS
• Explora el contenido de cada bucket.
• Descarga varios archivos a la vez a la carpeta que elijas, con barra de progreso.
• Borra objetos en lote, con confirmación.

PERMISOS
• Comprueba qué puedes hacer en cada bucket: lectura, escritura y borrado.
• Consulta su región y su configuración de cifrado.

PERFILES Y SEGURIDAD
• Gestiona varios perfiles de AWS y cambia entre ellos desde la barra superior.
• Las claves secretas se guardan en el Llavero de macOS.
• Contraseña maestra opcional: tus claves quedan cifradas y la app las pide al abrirse.
• Exporta e importa perfiles en un archivo cifrado con contraseña.
• Compatible con aws-cli: los perfiles se sincronizan con ~/.aws.

PRIVACIDAD
S3Manager no tiene servidor propio, no requiere cuenta con el desarrollador y no incluye publicidad ni analítica. Solo se conecta a Amazon Web Services, con tus credenciales y para las operaciones que tú lanzas. Al arrancar no se conecta a nada.

Requiere una cuenta de AWS con claves de acceso (Access Key ID y Secret Access Key) con permisos sobre S3.

Amazon S3 y AWS son marcas de Amazon.com, Inc. o sus filiales. S3Manager es una aplicación independiente, no afiliada ni respaldada por Amazon.

**Palabras clave (máx. 100, separadas por comas, sin espacios)**
aws,s3,bucket,amazon,cloud,almacenamiento,descargar,archivos,perfiles,credenciales,nube,iam

| Campo | Valor |
|---|---|
| URL de soporte | https://efjdev.com/soporte/ |
| URL de marketing | https://efjdev.com/s3manager/ |
| Versión | 1.2.2 |
| Copyright | 2026 Eugenio de Frutos Sánchez |

**Capturas de pantalla (macOS)**: 16:10, una de estas resoluciones: 1280×800, 1440×900,
2560×1600 o 2880×1800. Mínimo 1, máximo 10. Sugeridas: pestaña Buckets con lista,
pestaña Archivos con contenido, resultado de Verificar permisos, diálogo de perfiles AWS,
diálogo de contraseña maestra. Sin claves reales visibles.

## Información para la revisión de la app
- Requiere inicio de sesión: **Sí** (claves de AWS, no usuario/contraseña).
- Notas para el revisor (texto sugerido):
  > S3Manager necesita credenciales de AWS para funcionar. Para la revisión hemos creado
  > un usuario IAM de prueba con acceso limitado a un único bucket de demostración:
  > Access Key ID: <AKIA…>  Secret Access Key: <…>  Región: eu-south-2  Bucket: s3manager-review-edf
  > Pasos: abrir la app → Configurar credenciales → pegar las claves y escribir la región
  > eu-south-2 → pulsar «Actualizar» en la pestaña Buckets → seleccionar el bucket →
  > «Verificar permisos» / pestaña Archivos (descargar y borrar están permitidos; crear o
  > borrar buckets no, y la app mostrará un error de permisos: es lo esperado).
- Usuario IAM: `s3manager`, política inline `S3ManagerReviewOnlyBucket` (ListAllMyBuckets +
  lectura/escritura/borrado solo en `s3manager-review-edf`). Las claves reales se pegan solo
  en App Store Connect, nunca en este archivo.
- Tras la aprobación: desactivar/borrar la access key del usuario `s3manager`.
- Contacto: nombre, teléfono y correo del desarrollador.

## Cumplimiento de exportación (cifrado)
- La app usa HTTPS (boto3) y cifrado local estándar (Fernet/AES, PBKDF2) solo para proteger
  las credenciales del propio usuario. Normalmente encaja en la exención (cifrado estándar
  del sistema/autenticación y protección de datos del usuario). Confirmar en el cuestionario
  de App Store Connect; si aplica, añadir `ITSAppUsesNonExemptEncryption = false` al Info.plist.

## Bloqueos antes de poder subir una build a la Mac App Store
- App Sandbox obligatorio: hoy la app escribe en ~/.aws y ~/.s3manager (fuera del contenedor).
- Certificados "Apple Distribution"/"3rd Party Mac Developer Application" (ya existen) y
  "3rd Party Mac Developer Installer" (falta) + perfil de aprovisionamiento Mac App Store.
- Empaquetado .pkg con productbuild y subida con Transporter o `xcrun altool`/`notarytool`.
