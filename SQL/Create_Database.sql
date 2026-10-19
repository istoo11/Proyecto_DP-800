USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'CalcUpDB')
BEGIN
    CREATE DATABASE CalcUpDB;
END
GO

USE CalcUpDB;
GO

IF OBJECT_ID('dbo.leaderboard', 'U') IS NOT NULL DROP TABLE dbo.leaderboard;
IF OBJECT_ID('dbo.ejercicios', 'U') IS NOT NULL DROP TABLE dbo.ejercicios;
IF OBJECT_ID('dbo.usuarios', 'U') IS NOT NULL DROP TABLE dbo.usuarios;
GO

CREATE TABLE dbo.usuarios (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    nombre NVARCHAR(255) NOT NULL,
    correo NVARCHAR(255) NOT NULL UNIQUE,
    contraseña NVARCHAR(255) NOT NULL,
    direccion NVARCHAR(500) NULL
);
GO

CREATE TABLE dbo.ejercicios (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    descripcion NVARCHAR(255) NOT NULL,
    ejercicio NVARCHAR(MAX) NOT NULL,
    solucion NVARCHAR(255) NOT NULL,
    descripcion_ejercicio NVARCHAR(MAX) NOT NULL,
    embedding NVARCHAR(MAX) NULL CONSTRAINT CK_ejercicios_embedding_json CHECK (embedding IS NULL OR ISJSON(embedding) = 1)
);
GO

CREATE TABLE dbo.leaderboard (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    id_usuario UNIQUEIDENTIFIER NOT NULL,
    id_ejercicio BIGINT NOT NULL,
    fecha_comienzo DATETIME2 NULL,
    fecha_fin DATETIME2 NULL,
    CONSTRAINT FK_leaderboard_usuarios FOREIGN KEY (id_usuario) REFERENCES dbo.usuarios(id) ON DELETE CASCADE,
    CONSTRAINT FK_leaderboard_ejercicios FOREIGN KEY (id_ejercicio) REFERENCES dbo.ejercicios(id) ON DELETE CASCADE
);
GO

-- -----------------------------------------------------------------------------
-- 3. PROCEDIMIENTOS ALMACENADOS
-- -----------------------------------------------------------------------------