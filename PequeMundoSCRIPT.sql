-- ============================================================
--  PequeMundo – Base de Datos MySQL
--  Versión corregida: VARCHAR en lugar de VARCHAR2,
--  AUTO_INCREMENT, columna categoria agregada a PRODUCTO,
--  columna password y rol agregada a USUARIO.
-- ============================================================

CREATE DATABASE IF NOT EXISTS pequemundo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE pequemundo;

-- ── PRODUCTO ──────────────────────────────────────────────
CREATE TABLE PRODUCTO (
    id_producto   INT AUTO_INCREMENT PRIMARY KEY,
    nombre        VARCHAR(100)  NOT NULL,
    descripcion   VARCHAR(500),
    categoria     VARCHAR(50)   NOT NULL DEFAULT 'General',
    precio        INT           NOT NULL,
    stock         INT           NOT NULL DEFAULT 0,
    imagen        VARCHAR(200)  DEFAULT 'peque-mueble.webp',
    estado        VARCHAR(20)   NOT NULL DEFAULT 'Activo'
    -- estado: 'Activo' | 'Agotado' | 'Oculto'
);

-- ── USUARIO ───────────────────────────────────────────────
CREATE TABLE USUARIO (
    id_usuario      INT AUTO_INCREMENT PRIMARY KEY,
    nombre_usuario  VARCHAR(100) NOT NULL,
    email           VARCHAR(100) NOT NULL UNIQUE,
    telefono        VARCHAR(20),
    password_hash   VARCHAR(255) NOT NULL,
    rol             VARCHAR(20)  NOT NULL DEFAULT 'Cliente'
    -- rol: 'Admin' | 'Vendedor' | 'Cliente'
);

-- ── ORDEN ─────────────────────────────────────────────────
CREATE TABLE ORDEN (
    id_orden        INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario      INT          NOT NULL,
    estado          VARCHAR(30)  NOT NULL DEFAULT 'Pendiente',
    -- estado: 'Pendiente' | 'Preparando' | 'Enviado' | 'Entregado' | 'Cancelado'
    tipo_entrega    VARCHAR(30)  NOT NULL DEFAULT 'domicilio_rm',
    -- tipo_entrega: 'domicilio_rm' | 'domicilio_region' | 'retiro'
    subtotal        INT          NOT NULL,
    precio_envio    INT          NOT NULL DEFAULT 0,
    total           INT          NOT NULL,
    fecha_orden     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_orden_usuario FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario)
);

-- ── DETALLE_ORDEN ─────────────────────────────────────────
CREATE TABLE DETALLE_ORDEN (
    id_detalle      INT AUTO_INCREMENT PRIMARY KEY,
    id_orden        INT NOT NULL,
    id_producto     INT NOT NULL,
    cantidad        INT NOT NULL,
    precio_unitario INT NOT NULL,
    subtotal        INT NOT NULL,
    CONSTRAINT fk_detalle_orden    FOREIGN KEY (id_orden)    REFERENCES ORDEN(id_orden),
    CONSTRAINT fk_detalle_producto FOREIGN KEY (id_producto) REFERENCES PRODUCTO(id_producto)
);

-- ── DIRECCION_ENTREGA ─────────────────────────────────────
CREATE TABLE DIRECCION_ENTREGA (
    id_direccion  INT AUTO_INCREMENT PRIMARY KEY,
    id_orden      INT          NOT NULL,
    destinatario  VARCHAR(120),
    calle         VARCHAR(200),
    numero        VARCHAR(20),
    depto         VARCHAR(50),
    comuna        VARCHAR(60),
    region        VARCHAR(60),
    CONSTRAINT fk_direccion_orden FOREIGN KEY (id_orden) REFERENCES ORDEN(id_orden)
);

-- ── PAGO ──────────────────────────────────────────────────
CREATE TABLE PAGO (
    id_pago             INT AUTO_INCREMENT PRIMARY KEY,
    id_orden            INT          NOT NULL,
    proveedor           VARCHAR(50)  NOT NULL DEFAULT 'MercadoPago',
    codigo_transaccion  VARCHAR(100),
    estado_pago         VARCHAR(30)  NOT NULL DEFAULT 'Pendiente',
    -- estado_pago: 'Pendiente' | 'Aprobado' | 'Rechazado' | 'En proceso'
    monto               INT          NOT NULL,
    fecha_pago          DATETIME,
    CONSTRAINT fk_pago_orden FOREIGN KEY (id_orden) REFERENCES ORDEN(id_orden)
);

-- ── DESPACHO ──────────────────────────────────────────────
CREATE TABLE DESPACHO (
    id_despacho         INT AUTO_INCREMENT PRIMARY KEY,
    id_orden            INT         NOT NULL,
    empresa             VARCHAR(60),
    numero_seguimiento  VARCHAR(60),
    fecha_despacho      DATE,
    fecha_entrega       DATE,
    CONSTRAINT fk_despacho_orden FOREIGN KEY (id_orden) REFERENCES ORDEN(id_orden)
);

-- ── VENDEDOR ──────────────────────────────────────────────
-- (Referencia a usuarios con rol Vendedor; puede usarse para asignaciones)
CREATE TABLE VENDEDOR (
    id_vendedor     INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario      INT         NOT NULL,
    nombre_vendedor VARCHAR(100),
    CONSTRAINT fk_vendedor_usuario FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario)
);

-- ============================================================
--  DATOS DE PRUEBA
-- ============================================================

-- Usuarios (password_hash = werkzeug pbkdf2 de 'admin123' / 'cliente123')
-- Para pruebas rápidas los guardamos en texto plano; en producción usar generate_password_hash
INSERT INTO USUARIO (nombre_usuario, email, telefono, password_hash, rol) VALUES
('Admin',          'admin@pequemundo.cl', '+56912345678', 'admin123',    'Admin'),
('María González', 'cliente@test.cl',     '+56987654321', 'cliente123',  'Cliente');

-- Productos
INSERT INTO PRODUCTO (nombre, descripcion, categoria, precio, stock, imagen, estado) VALUES
('Cuna Clásica',          'Cuna de madera sólida con barandas ajustables.',              'Cunas',      129990, 8,  'peque-mueble.webp', 'Activo'),
('Cuna Convertible 3en1', 'Se transforma de cuna a cama de niño y luego a sofá.',        'Cunas',      189990, 4,  'peque-mueble.webp', 'Activo'),
('Cuna Viajera Plegable', 'Ligera y plegable, ideal para viajes. Incluye bolso.',        'Cunas',       79990, 12, 'peque-mueble.webp', 'Activo'),
('Cama Individual',       'Cama con barandas de seguridad, para niños de 2 a 8 años.',  'Camas',      149990, 6,  'peque-mueble.webp', 'Activo'),
('Cama Litera Doble',     'Litera con escalera integrada y barandas de seguridad.',      'Camas',      249990, 3,  'peque-mueble.webp', 'Activo'),
('Cama con Cajones',      'Cama individual con dos cajones de almacenamiento.',          'Camas',      179990, 5,  'peque-mueble.webp', 'Activo'),
('Cómoda 3 Cajones',      'Cómoda compacta con tres amplios cajones.',                  'Cómodas',     99990, 10, 'peque-mueble.webp', 'Activo'),
('Escritorio Infantil',   'Escritorio regulable en altura para niños.',                 'Escritorios', 89990, 7,  'peque-mueble.webp', 'Activo'),
('Silla Ergonómica Kids', 'Silla ajustable con soporte lumbar para niños.',             'Sillas',      69990, 9,  'peque-mueble.webp', 'Activo'),
('Clóset 2 Puertas',      'Clóset espacioso con barra y estantes internos.',            'Clósets',    199990, 4,  'peque-mueble.webp', 'Activo');
