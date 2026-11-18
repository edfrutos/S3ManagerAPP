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

## Versión 1.2.4 (primera versión en la Mac App Store)
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

INTERFAZ
• Tema claro, oscuro o el del sistema, desde Ver > Apariencia.

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
| Versión | 1.2.4 |
| Copyright | 2026 Eugenio de Frutos Sánchez |

**Capturas de pantalla (macOS)**: 16:10, una de estas resoluciones: 1280×800, 1440×900,
2560×1600 o 2880×1800. Mínimo 1, máximo 10. Sin claves reales visibles: usar el perfil del
bucket de revisión `s3manager-review-edf`.

Sugeridas (en este orden):
1. Pestaña Buckets con la lista y la información del bucket.
2. Pestaña Archivos con contenido y algunos seleccionados.
3. Resultado de Verificar permisos.
4. Diálogo de perfiles AWS (con el campo de la clave secreta vacío o en puntos).
5. La misma vista de la captura 1 en tema oscuro (Ver > Apariencia > Oscura).

Procedimiento en una pantalla Retina (sale a 2880×1800):
1. Reducir la ventana de S3Manager a menos de 1440×900 puntos.
2. Capturar solo la ventana, sin sombra; después hacer clic en la ventana:
   `screencapture -o -w ~/Desktop/s3m-1.png`
3. Centrarla en un lienzo 16:10 del color de fondo de la app:
   `sips -p 1800 2880 --padColor F5F5F5 ~/Desktop/s3m-1.png --out ~/Desktop/s3m-1-16x10.png`
   (tema oscuro: `--padColor 1E1E1E`).
4. Comprobar el tamaño: `sips -g pixelWidth -g pixelHeight ~/Desktop/s3m-1-16x10.png`.

## Información para la revisión de la app
- Requiere inicio de sesión: **Sí** (claves de AWS, no usuario/contraseña).
- Notas para el revisor (texto sugerido):
  > S3Manager necesita credenciales de AWS para funcionar. Para la revisión hemos creado
  > un usuario IAM de prueba con acceso limitado a un único bucket de demostración:
  > Access Key ID: <AKIA…>  Secret Access Key: <…>  Región: eu-south-2  Bucket: s3manager-review-edf
  > Pasos: al abrir la app por primera vez, aceptar la configuración de credenciales (o
  > menú Archivo → Gestionar Perfiles AWS…) → dejar el perfil «default», pegar las dos
  > claves y elegir la región eu-south-2 → «Guardar Perfil» → «Cerrar» → en la pestaña
  > Buckets pulsar «Actualizar» → seleccionar el bucket → «Verificar Permisos» / «Ver
  > Archivos» (descargar y borrar archivos están permitidos; crear o borrar buckets no, y
  > la app mostrará un error de permisos: es lo esperado). Al descargar, macOS pide elegir
  > la carpeta de destino, porque la app funciona con App Sandbox. El tema se cambia en
  > Ver → Apariencia.
- Usuario IAM: `s3manager`, política inline `S3ManagerReviewOnlyBucket` (ListAllMyBuckets +
  lectura/escritura/borrado solo en `s3manager-review-edf`). Las claves reales se pegan solo
  en App Store Connect, nunca en este archivo.
- Tras la aprobación: desactivar/borrar la access key del usuario `s3manager`.
- Contacto: nombre, teléfono y correo del desarrollador.

## Cumplimiento de exportación (cifrado)
- La app usa HTTPS (boto3) y cifrado local estándar (Fernet/AES, PBKDF2) solo para proteger
  las credenciales del propio usuario. Normalmente encaja en la exención (cifrado estándar
  del sistema/autenticación y protección de datos del usuario). Confirmar en el cuestionario
  de App Store Connect. ✅ `ITSAppUsesNonExemptEncryption = false` ya está en el Info.plist,
  así que App Store Connect no pregunta por cada build.

## Bloqueos antes de poder subir una build a la Mac App Store (resueltos)
Resueltos en la versión 1.2.4 (ver `docs/PLAN_MAC_APP_STORE.md`):
- App Sandbox: en sandbox no se escribe en `~/.aws`, y `~/.s3manager` queda dentro del
  contenedor.
- Certificados: Apple Distribution (con el perfil «S3Manager») y 3rd Party Mac Developer
  Installer.
- Empaquetado: `make mas` genera el `.pkg`, que se sube con Transporter.

## Política de privacidad (efjdev.com/privacidad): texto propuesto para S3Manager
Sustituye al segundo párrafo de la sección «S3Manager»:

> Tus claves secretas se guardan en el Llavero de tu Mac; si activas la contraseña maestra,
> se guardan además cifradas con ella. Los datos sin secretos (nombres de perfil, región,
> perfil activo, tema elegido) se guardan en tu equipo, y los archivos que descargas van a la
> carpeta que eliges. Todo ello permanece en tu Mac.
>
> **Versión de la Mac App Store.** Funciona dentro del entorno aislado de macOS (App
> Sandbox): solo accede a las carpetas y archivos que eliges en el panel de macOS y no
> escribe en ~/.aws, así que sus perfiles no se comparten con aws-cli. Para usar los mismos
> perfiles en otro equipo o versión, expórtalos e impórtalos desde la app en un archivo
> cifrado con contraseña.
>
> **Versión de descarga directa.** Para que puedas usar los mismos perfiles con aws-cli,
> la app escribe tus perfiles en ~/.aws/credentials y ~/.aws/config: sin contraseña
> maestra, la clave secreta queda en ese archivo en texto plano, como hace el propio
> aws-cli; con contraseña maestra se escribe un marcador en su lugar. Los datos sin
> secretos se guardan en ~/.s3manager/config.json.

Actualizar también la fecha de «Última actualización».
